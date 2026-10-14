// Calls the API and turns the answers into one display model. Runs in the background worker,
// so pages (including https shops) never call the API themselves and no key reaches a page.
import { API_BASE, API_KEY } from "./config.js";

const VERDICT = {
  green: { icon: "✅", word: "Looks fine so far" },
  amber: { icon: "⚠️", word: "Be careful: under review" },
  red: { icon: "⛔", word: "Danger or not real" },
  unknown: { icon: "❔", word: "Not enough evidence yet" },
};

export async function api(path, options = {}, base = API_BASE) {
  const headers = { "Content-Type": "application/json", ...(API_KEY && { "X-API-Key": API_KEY }) };
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
const CHECK_NAMES = { copied_photos: "photos", price: "price", website_age: "website age", spec: "specs" };

// How the engine matched the listing. A look-alike is only a similar product, so it is never treated as this product.
const STRONG_MATCHES = new Set(["url", "model_number"]);

const card = (level, lines) => ({ level, icon: VERDICT[level].icon, word: VERDICT[level].word, lines });

// POST /v1/shelf/items. `listing_url` and `title` are extra fields so a listing that has no product id yet can still be saved.
export async function saveToShelf({ product_id, listing_url, title }) {
  const { body, source } = await api("/v1/shelf/items", { method: "POST", body: JSON.stringify({ product_id, listing_url, title }) });
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
  return { text: answer?.text || "I don't know. There is not enough evidence to answer that.", evidence_ids: answer?.evidence_ids || [], source };
}

// One check per page at a time, remembered for 10 minutes: Check, Save and Ask all need it, and the real engine is slow.
const recent = new Map();
export function runCheck(page) {
  const hit = recent.get(page.url);
  if (hit && Date.now() - hit.at < 10 * 60 * 1000) return hit.promise;
  const promise = runCheckNow(page);
  recent.set(page.url, { at: Date.now(), promise });
  promise.catch(() => recent.delete(page.url)); // never remember a failure
  return promise;
}

async function runCheckNow(page) {
  const { product_id, listing_id, ...listing } = page;
  const { body: trust, source } = await api("/v1/listings/trust-check", { method: "POST", body: JSON.stringify(listing) });
  const exact = !trust.matched_by || STRONG_MATCHES.has(trust.matched_by); // the mock has no matched_by
  const pid = exact ? trust.matched_product_id || product_id : product_id;
  const safety = pid ? (await api(`/v1/products/${pid}/safety`)).body : null;

  const safeLevel = !safety ? "unknown" : safety.verdict === "not_enough_evidence" ? "unknown" : safety.verdict;
  const safeLines = safety
    ? [
        safety.official_status.recalled ? "Officially recalled" : `Not recalled (checked ${safety.official_status.checked.join(", ")})`,
        ...safety.ai_findings.map((f) => `${f.independent_reports} reports of ${f.mechanism} (${f.status.replace("_", " ")})`),
        ...(safety.reviews_checked != null && safeLevel === "unknown" ? [`Only ${safety.reviews_checked} reviews checked, too few for a safety verdict`] : []),
      ]
    : ["We could not match this exact product to one we have checked, so we make no safety claim for it"];

  const realLines = Object.entries(trust.checks).flatMap(([k, c]) =>
    c.result === "flag" ? [CHECK_WORDS[k]?.(c)] : c.result === "unknown" ? [`Could not verify ${CHECK_NAMES[k] || k}: ${c.reason || "no data"}`] : [],
  ).filter(Boolean);
  if (trust.hidden_instructions_found) realLines.push("Page has hidden text trying to instruct AI. Ignored.");
  const real = card(realLevel(trust.checks), realLines.length ? realLines : ["No warning signs found"]);

  // No warning is not good news when checks could not run, so the API's reassuring sentence is not used then.
  const worst = [safeLevel, real.level].includes("red") ? "red" : [safeLevel, real.level].includes("amber") ? "amber" : null;
  const summary = worst ? trust.summary : [safeLevel, real.level].includes("unknown")
    ? "Not enough evidence yet. SafeShelf could not verify everything, so no warning here does not mean the product is safe."
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
    evidence_ids: trust.evidence_ids || [],
    // The engine's own answer, kept so follow-up questions can use it ("how was the price checked?")
    matched_by: trust.matched_by || null,
    trust_checks: trust.checks,
    genuine_model_safety: trust.safety_of_genuine_model || null,
    label: [safety?.label, trust.label].filter(Boolean).join(" · "),
  };
}
