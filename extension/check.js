// Calls the API and turns the answers into one display model. Runs in the background worker,
// so pages (including https shops) never call the API themselves and no key reaches a page.
import { API_BASE, API_KEY } from "./config.js";

const VERDICT = {
  green: { icon: "✅", word: "No problems found" },
  amber: { icon: "⚠️", word: "Be careful" },
  red: { icon: "⛔", word: "Don't buy" },
  unknown: { icon: "❔", word: "Can't tell yet" },
};

export async function api(path, options = {}, base = API_BASE) {
  const headers = { "Content-Type": "application/json", ...(API_KEY && { "X-API-Key": API_KEY }), ...(options.headers || {}) };
  // The real engine can take a minute on a cold start, so wait up to 150 s instead of hanging forever.
  const res = await fetch(base + path, { signal: AbortSignal.timeout(150000), ...options, headers });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail; // the API's own explanation, e.g. "The AI is busy right now"
    throw new Error(typeof detail === "string" ? detail : `${path} answered ${res.status}`);
  }
  return { body: await res.json(), source: res.headers.get("X-SafeShelf-Source") };
}

// "Is it real?" colour comes from counting flags in code, never from page text.
// Checks the engine could not do ("unknown") never count as good news.
function realLevel(checks) {
  const results = Object.values(checks).map((c) => c.result);
  const flags = results.filter((r) => r === "flag").length;
  if (flags >= 2) return "red";
  if (flags === 1) return "amber";
  return results.includes("unknown") ? "unknown" : "green";
}

const CHECK_WORDS = {
  copied_photos: (c) => c.matches_official_listing && "Photos are copied from the official listing",
  price: (c) => c.price != null && `Price Rs ${c.price} is far below the genuine Rs ${c.lowest_credible_price}`,
  website_age: (c) => `Website registered only ${c.domain_registered_days_ago} days ago`,
  spec: (c) => c.conflicts?.length && `Spec conflicts: ${c.conflicts.join(", ")}`,
};
const CHECK_NAMES = { copied_photos: "photos", price: "price", website_age: "website age", spec: "specs", seller: "seller" };
// A check that couldn't decide, in plain words: the seller's line already reads as a sentence.
const unknownLine = (k, c) => {
  const why = c.reason || "not enough information";
  if (k === "seller" && /^Sold by/.test(why)) return why;
  return `Couldn't check the ${CHECK_NAMES[k] || k}: ${why}`;
};

// How the engine matched the listing. A look-alike is only a similar product, so it is never treated as this product.
const STRONG_MATCHES = new Set(["url", "model_number"]);

const card = (level, lines) => ({ level, icon: VERDICT[level].icon, word: VERDICT[level].word, lines });

// POST /v1/shelf/items. `listing_url` and `title` are extra fields so a listing that has no product id yet can still be saved.
// A random id for this browser, sent as X-Owner-Ref so the API keeps this shopper's saved products apart (it stores
// only a hash of it). No account or personal detail is involved.
async function ownerRef() {
  const { owner_ref } = await chrome.storage.local.get("owner_ref");
  if (owner_ref) return owner_ref;
  const fresh = crypto.randomUUID();
  await chrome.storage.local.set({ owner_ref: fresh });
  return fresh;
}

// Plan v2.2: My Shelf saves are watchlist items: re-checked against live official sources, with an alert only when the
// outcome for this exact model and batch changes.
export async function saveToShelf({ product_id, listing_url, title, brand, model, market }) {
  const headers = { "X-Owner-Ref": await ownerRef() };
  const { body, source } = await api("/v1/watchlists", { method: "POST", headers,
    body: JSON.stringify({ product_id, url: listing_url, title, brand, model, market }) });
  return { ...body, source }; // source tells the caller whether the API really stored it ("real") or only answered with an example ("mock")
}

// What an evidence ID points to: the source, date and exact quote behind a finding.
export async function getEvidence(ids) {
  const { body, source } = await api(`/v1/evidence?ids=${encodeURIComponent(ids.join(","))}`);
  const want = new Set(ids);
  return { items: (Array.isArray(body) ? body : body.items || []).filter((e) => want.has(e.evidence_id)), source };
}

// Shelf Chat: a question about this listing, answered by the SafeShelf API (POST /v1/agent/sessions).
// It sends the check result the shopper just saw and the last few messages, so follow-ups work.
export async function askAgent({ product_id, message, language, session_id, context, history }) {
  const { body, source } = await api("/v1/agent/sessions", {
    method: "POST",
    body: JSON.stringify({ mode: "chat", product_id, message, language, session_id, context, history }),
  });
  // Until the API serves a real chat handler it answers with a made-up example. Never show that as an answer.
  if (source === "mock") throw new Error("Shelf Chat is not live on the SafeShelf API yet: it only returns an example answer.");
  const answer = [...(body.messages || [])].reverse().find((m) => m.role === "assistant");
  return { text: answer?.text || "I don't know. There is not enough evidence to answer that.", evidence_ids: answer?.evidence_ids || [], steps: body.steps || [], language: body.language, source };
}

// Any agent session (Investigate pipeline, Shopper Agent steps, Safer Alternative, report draft): POST /v1/agent/sessions.
// timeoutMs: the Research Agent browses official sites and can take two to three minutes.
export async function agentSession(body, timeoutMs = 150000) {
  const { body: answer, source } = await api("/v1/agent/sessions", { method: "POST", body: JSON.stringify(body), signal: AbortSignal.timeout(timeoutMs) });
  if (source === "mock") throw new Error("SafeShelf's agents are not live on this API yet: it only returns an example answer.");
  return answer;
}

// The same agents with each step sent as it happens (POST /v1/agent/sessions/stream, server-sent events).
// onEvent gets start / step / verdict events; the promise gives the final answer. An API without the stream
// (older server) gets the plain call, and so does a dropped connection (a TypeError such as "network error"):
// the server keeps a finished check for 10 minutes, so asking again is quick.
export async function agentStream(body, onEvent, timeoutMs = 150000) {
  try { return await streamOnce(body, onEvent, timeoutMs); }
  catch (err) {
    if (!(err instanceof TypeError)) throw err;
    onEvent?.({ type: "retry" });
    return agentSession(body, timeoutMs);
  }
}

async function streamOnce(body, onEvent, timeoutMs) {
  const headers = { "Content-Type": "application/json", ...(API_KEY && { "X-API-Key": API_KEY }) };
  const res = await fetch(API_BASE + "/v1/agent/sessions/stream", { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(timeoutMs) });
  if (res.status === 404 || res.status === 405) return agentSession(body, timeoutMs);
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail;
    throw new Error(typeof detail === "string" ? detail : `the agent answered ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    onEvent({ type: "ping" }); // every piece, even the server's 15 s keep-alive comment, so the worker stays awake
    buffer += decoder.decode(value, { stream: true });
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const data = buffer.slice(0, cut).split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5)).join("\n");
      buffer = buffer.slice(cut + 2);
      if (!data) continue;
      const event = JSON.parse(data);
      if (event.type === "done") return event.result;
      if (event.type === "error") throw new Error(event.detail || "The agent could not finish");
      onEvent(event);
    }
  }
  throw new Error("The agent stopped without an answer");
}

// "Is it safe?" for a listing SafeShelf has no product for. null when the API cannot answer it (old server, mock).
async function listingSafety(listing) {
  try {
    const { body, source } = await api("/v1/listings/safety-check", { method: "POST", body: JSON.stringify(listing) });
    return source === "mock" ? null : body;
  } catch (_) {
    return null;
  }
}

function pageSafetyLines(s) {
  const st = s.official_status;
  const what = [s.brand, s.model].filter(Boolean).join(" ");
  const lines = [];
  for (const r of st.recalls || []) {
    lines.push(st.recall_ids.includes(r.recall_id) ? `Officially recalled: ${r.title}` : `A recall notice may cover this ${s.brand || ""} product (check the model): ${r.title}`.replace("  ", " "));
  }
  if (!st.recalled && what) lines.push(`No official recall found for ${what} (checked ${st.checked.join(", ")})`);
  lines.push(...s.ai_findings.map((f) => `${f.independent_reports} buyer${f.independent_reports === 1 ? "" : "s"} on this page reported ${f.mechanism} (AI finding, under review)`));
  if (!s.ai_findings.length) {
    lines.push(s.reviews_checked
      ? `Read ${s.reviews_checked} review${s.reviews_checked === 1 ? "" : "s"} on this page: no fire, burn or shock reports, but that is too few to call it safe`
      : "No reviews on this page to read for safety reports");
  }
  return lines;
}

// Plan v2.2: the live official-source investigation (country scope, coverage, sources). null when the API can't
// answer it (old server, mock), so the card falls back to the older recall lines.
async function sourcesCheck(listing, productId) {
  try {
    const body = { url: listing.url, title: listing.title, currency: listing.currency, page_text: listing.page_text,
      brand: listing.brand, model: listing.model, ...(productId && { product_id: productId }) };
    const { body: inv, source } = await api("/v1/investigations", { method: "POST", body: JSON.stringify(body) });
    return source === "mock" || !inv?.outcome ? null : inv;
  } catch (_) {
    return null;
  }
}

// The colour from the code's outcome: red only for a recall in the shopper's own country; green only when the
// reviews were enough and showed nothing (engine/safety.py colour()).
export function outcomeLevel(outcome, radar) {
  if (outcome === "confirmed_recall") return "red";
  if (outcome === "substantiated_hazard_signal" || outcome === "potential_concern") return "amber";
  if (outcome === "no_matching_notice_found") return radar === "green" || radar === "amber" ? radar : radar === "red" ? "amber" : "unknown";
  return radar === "amber" ? "amber" : "unknown";
}

export function outcomeLines(o) {
  const lead = o.lead_record;
  const lines = [lead ? `${o.headline} (${lead.authority} ${lead.record_id}${lead.published ? `, ${lead.published}` : ""})` : o.headline];
  if (o.coverage?.summary) lines.push(`Checked: ${o.coverage.summary}`);
  const next = (o.what_would_change || [])[0];
  if (next && o.outcome !== "confirmed_recall") lines.push(`What would change this: ${next.fact}`);
  return lines;
}

// One check per page at a time, remembered for 10 minutes: Check, Save and Ask all need it, and the real engine is slow.
const recent = new Map();
// fresh: "Check again" asks the API again instead of reusing the remembered answer.
export function runCheck(page, fresh = false) {
  const hit = recent.get(page.url);
  if (!fresh && hit && Date.now() - hit.at < 10 * 60 * 1000) return hit.promise;
  const promise = runCheckNow(page);
  recent.set(page.url, { at: Date.now(), promise });
  promise.catch(() => recent.delete(page.url)); // never remember a failure
  return promise;
}

async function runCheckNow(page) {
  const { product_id, listing_id, ...listing } = page;
  // "Is it real?" and "Is it safe?" start together (one after the other took 13 s + 61 s on a new product).
  // Safety is started for what the page says it is: its product id, else the listing alone; if "Is it real?" then
  // matches a different known product, that product's stored safety answer is used instead.
  const trustCall = api("/v1/listings/trust-check", { method: "POST", body: JSON.stringify(listing) });
  const earlySafety = product_id ? api(`/v1/products/${product_id}/safety`).then((r) => r.body) : listingSafety(listing);
  earlySafety.catch(() => {}); // awaited below only when it is the answer used
  const invCall = product_id ? Promise.resolve(null) : sourcesCheck(listing, null);
  const { body: trust, source } = await trustCall;
  const exact = !trust.matched_by || STRONG_MATCHES.has(trust.matched_by); // the mock has no matched_by
  const pid = exact ? trust.matched_product_id || product_id : product_id;
  // Known product: its stored safety answer. Otherwise the listing alone: recalls by brand and model, and the reviews on the page.
  const safety = pid && pid !== product_id ? (await api(`/v1/products/${pid}/safety`)).body : await earlySafety;

  // A stored product's safety answer carries the outcome itself; a listing gets it from the live investigation.
  const inv = safety?.outcome ? null : await invCall;
  const outcome = safety?.outcome ? safety : inv;
  const radarLevel = !safety ? "unknown" : safety.verdict === "not_enough_evidence" ? "unknown" : safety.verdict;
  const safeLevel = outcome ? outcomeLevel(outcome.outcome, safety?.outcome ? radarLevel : (safety?.verdict === "not_enough_evidence" ? "unknown" : safety?.verdict)) : radarLevel;
  const findingLines = (safety?.ai_findings || []).map((f) => `${f.independent_reports} buyer report${f.independent_reports === 1 ? "" : "s"} of ${f.mechanism} (AI finding, under review)`);
  const safeLines = outcome ? [...outcomeLines(outcome), ...findingLines] : !safety
    ? ["We could not match this exact product to one we have checked, so we make no safety claim for it"]
    : pid ? [
        safety.official_status.recalled ? "Officially recalled" : `Not recalled (checked ${safety.official_status.checked.join(", ")})`,
        ...safety.ai_findings.map((f) => `${f.independent_reports} reports of ${f.mechanism} (${f.status.replace("_", " ")})`),
        ...(safety.reviews_checked != null && safeLevel === "unknown" ? [`Only ${safety.reviews_checked} reviews checked, too few for a safety verdict`] : []),
      ]
    : pageSafetyLines(safety);
  const safetyEvidence = (pid ? [] : safety?.ai_findings || []).flatMap((f) => f.evidence_ids || []);

  const realLines = Object.entries(trust.checks).flatMap(([k, c]) =>
    c.result === "flag" ? [CHECK_WORDS[k]?.(c)] : c.result === "unknown" ? [unknownLine(k, c)] : [],
  ).filter(Boolean);
  if (trust.hidden_instructions_found) realLines.push("This page hides text meant to trick AI tools, which is a warning sign. We ignored it.");
  // For a product SafeShelf has no genuine version of, the engine also says what looked right (seller, M.R.P., site).
  realLines.push(...(trust.good_signs || []));
  const real = card(realLevel(trust.checks), realLines.length ? realLines : ["Nothing suspicious about the seller or price"]);

  // No warning is not good news when checks could not run, so the API's reassuring sentence is not used then.
  const worst = [safeLevel, real.level].includes("red") ? "red" : [safeLevel, real.level].includes("amber") ? "amber" : null;
  // The API's sentence is about the "Is it real?" checks only, so a safety warning gets its own sentence
  // (otherwise "Be careful" sat above "No warning signs found in these checks").
  const safetyWorry = { red: "This product has been recalled or has serious safety reports.", amber: "Buyers have reported safety problems that are under review." }[safeLevel];
  const realWorry = ["red", "amber"].includes(real.level) ? trust.summary : null;
  const summary = worst ? [safetyWorry, realWorry].filter(Boolean).join(" ") : [safeLevel, real.level].includes("unknown")
    ? "SafeShelf could not verify everything, so no warning here does not mean the product is safe."
    : trust.summary;

  return {
    host: new URL(listing.url).host,
    product_id: pid || null,
    // For a look-alike match the engine still names the nearest similar product. The tabs may show data for it, clearly labelled.
    similar_product_id: exact ? null : trust.matched_product_id || null,
    source, // "mock" until the real engine answers; screens must say so
    safe: card(safeLevel, safeLines),
    real,
    summary,
    evidence_ids: [...(trust.evidence_ids || []), ...safetyEvidence],
    // The engine's own answer, kept so follow-up questions can use it ("how was the price checked?")
    matched_by: trust.matched_by || null,
    trust_checks: trust.checks,
    genuine_model_safety: trust.safety_of_genuine_model || null,
    label: [safety?.label, trust.label].filter(Boolean).join(" · "),
    // Plan v2.2: what was checked, country by country, and the official records behind the answer.
    outcome: outcome ? { outcome: outcome.outcome, headline: outcome.headline, source_mode: outcome.source_mode,
      plain: outcome.plain || null, // the answer in everyday words (engine/plain.py): shown first
      coverage: outcome.coverage?.countries || [], what_would_change: outcome.what_would_change || [],
      sources: (inv?.matches || []).filter((m) => m.tier !== "lookalike").slice(0, 4).map((m) => ({ authority: m.authority, record_id: m.record_id, url: m.url, title: m.title, local: m.local, tier: m.tier })),
      lead: outcome.lead_record || null, limitations: outcome.limitations || [], policy_version: outcome.policy_version } : null,
  };
}
