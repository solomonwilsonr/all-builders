// Calls the API and turns the answers into one display model. Runs in the background worker,
// so pages (including https shops) never call the API themselves and no sign-in token reaches a page.
import { API_BASE } from "./config.js";
import { idToken, SignInNeeded } from "./session.js";

const VERDICT = {
  green: { icon: "✅", word: "Looks fine so far" },
  amber: { icon: "⚠️", word: "Be careful: under review" },
  red: { icon: "⛔", word: "Danger or not real" },
  unknown: { icon: "❔", word: "Not enough evidence yet" },
};

// Every call carries the signed-in person's ID token. A 401 or 403 is asked once more with a fresh token (the old
// one may have just run out, or an admin may have just changed the role); a second 401 means sign in again.
async function signedFetch(url, options, fresh = false) {
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${await idToken(fresh)}` };
  const res = await fetch(url, { ...options, headers });
  if (!fresh && (res.status === 401 || res.status === 403)) return signedFetch(url, options, true);
  if (res.status === 401) throw new SignInNeeded("Your SafeShelf sign-in wasn't accepted. Click the SafeShelf icon in the toolbar to sign in again");
  return res;
}

// allowMock: only for a local API (make api), so a new endpoint's sample answer can be shown, labelled as a demo.
export async function api(path, options = {}, base = API_BASE, allowMock = false) {
  // The real engine can take a minute on a cold start, so wait up to 150 s instead of hanging forever.
  const res = await signedFetch(base + path, { signal: AbortSignal.timeout(150000), ...options });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail; // the API's own explanation, e.g. "The AI is busy right now"
    throw new Error(typeof detail === "string" ? detail : `${path} answered ${res.status}`);
  }
  const source = res.headers.get("X-SafeShelf-Source");
  if (source === "mock" && !allowMock) throw new Error("Demo data was rejected. Restart the local API with make api to use real results.");
  return { body: await res.json(), source };
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
  const res = await signedFetch(API_BASE + "/v1/agent/sessions/stream", { method: "POST", body: JSON.stringify(body), signal: AbortSignal.timeout(timeoutMs) });
  if (res.status === 404 || res.status === 405) return agentSession(body, timeoutMs);
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail;
    throw new Error(typeof detail === "string" ? detail : `the agent answered ${res.status}`);
  }
  if (res.headers.get("X-SafeShelf-Source") === "mock") throw new Error("Demo data was rejected. Restart the local API with make api to use real results.");
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

// "Is it any good?" as a small widget under the verdict (POST /v1/listings/review-verdict). About quality only: it is
// never red and never changes the safety colour. null when there is nothing to show.
const REVIEW_TONE = { good: "good", mixed: "mixed", poor: "poor", not_enough_reviews: "none" };
const upper = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);
export function reviewWidget(v) {
  if (!v || !REVIEW_TONE[v.verdict]) return null;
  const r = v.rating || {};
  const stars = [r.average && `★ ${r.average}`, r.count && `${r.count.toLocaleString("en-IN")} rating${r.count === 1 ? "" : "s"}`].filter(Boolean).join(" · ");
  const flag = (v.trust?.flags || [])[0];
  return {
    tone: REVIEW_TONE[v.verdict],
    word: v.headline,
    stars: [stars, v.reviews_read && `${v.reviews_read} review${v.reviews_read === 1 ? "" : "s"} read`].filter(Boolean).join(" · "),
    liked: (v.liked || []).slice(0, 2).map((t) => upper(t.phrase)),
    // Up to ten, most common first: the share of buyers when the reviews read allow one, else how many reviews say it
    complaints: (v.complaints || []).slice(0, 10).map((c) => ({
      text: upper(c.phrase),
      sub: c.share_estimate ? `about ${Math.max(1, Math.round(100 * c.share_estimate))}% of buyers` : `${c.mentions} review${c.mentions === 1 ? "" : "s"}`,
      // The reviews counted for it, from the API's own answer: opening a complaint shows them, no second call
      reviews: (c.reviews || []).map((r) => ({ stars: r.rating ? "★".repeat(Math.round(r.rating)) : "", date: r.date || "", title: r.title || "", text: r.text || "" })),
    })),
    warning: v.trust?.may_be_inflated && flag ? `Some reviews may not be genuine: ${flag.detail}` : null,
    note: v.verdict === "not_enough_reviews" ? "Too few ratings to judge" : v.confidence === "low" ? "Low confidence" : null,
    reasons: v.reasons || [],
  };
}

// "Is it possible?": is the price believable, and can the listing's technical claims be true? Two APIs, so the price
// chart can show while the slower claims check is still running. About price and physics only: never red, and it never
// changes the safety verdict.
const money = (n, cur = "INR") => (n == null ? "" : `${cur === "INR" ? "₹" : `${cur} `}${Math.round(n).toLocaleString("en-IN")}`);
const PRICE_TONE = { too_low: ["warn", "Price looks too low"], below_usual: ["warn", "Cheaper than usual"], normal: ["ok", "Price looks normal"],
  high: ["none", "Pricier than usual"], not_enough_data: ["none", "Not enough price data"] };
const CLAIM_TONE = { possible: ["ok", "Claims look possible"], doubtful: ["warn", "Some claims look doubtful"], not_possible: ["warn", "A claim looks impossible"], cant_tell: ["none", "Can't tell if the claims hold"] };
const CLAIM_MARK = { possible: "check", doubtful: "warn", not_possible: "stop", cant_tell: "help" };
const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : null);

// The range chart: positions are percent of the track, which runs from 0 to 10% past the dearest price shown.
// The question answered in one line, from the price answer and the claims answer: the worse of the two. Code only.
const ANSWER_WORD = { not_possible: "Not possible at this price", unlikely: "Unlikely at this price", possible: "Possible at this price", cant_tell: "Can't tell if this price is possible" };
const RANK = { not_possible: 3, unlikely: 2, cant_tell: 1, possible: 0 };
export function possibleAnswer(price, claims) {
  const fromPrice = price?.answer || null;
  const bad = (claims?.claims || []).find((c) => c.result === "not_possible") || (claims?.claims || []).find((c) => c.result === "doubtful");
  const fromClaims = bad ? { verdict: bad.result === "not_possible" ? "not_possible" : "unlikely", text: `${bad.claim}: ${bad.why}`,
    word: bad.result === "not_possible" ? "A claim is not possible" : "A claim looks doubtful" } : null;
  const picks = [fromPrice, fromClaims].filter(Boolean);
  if (!picks.length) return null;
  const top = picks.reduce((a, b) => (RANK[b.verdict] > RANK[a.verdict] ? b : a));
  const subject = price?.answer?.subject;
  return { tone: top.verdict === "possible" ? "ok" : top.verdict === "cant_tell" ? "none" : "warn", verdict: top.verdict,
    word: top.word || ANSWER_WORD[top.verdict],
    question: top === fromPrice && subject && price.listing != null ? `${money(price.listing, price.currency)} for a ${subject}` : top === fromClaims ? `"${bad.claim}"` : null,
    text: top.text };
}

export function priceWidget(v) {
  const tone = v && PRICE_TONE[v.verdict];
  if (!tone) return null;
  const cur = v.currency || "INR";
  const top = Math.max(v.genuine_range?.high || 0, v.listing_price || 0, ...(v.comparables || []).map((c) => c.price)) * 1.1;
  const at = (n) => (top > 0 && n != null ? Math.min(100, Math.max(0, (100 * n) / top)) : null);
  const range = v.genuine_range;
  return {
    tone: tone[0], word: v.headline || tone[1], answer: v.answer || null, listing: v.listing_price ?? null, currency: cur,
    line: v.listing_price != null
      ? `${money(v.listing_price, cur)}${range ? ` · genuine ${v.category || "products"}: ${money(range.low, cur)} – ${money(range.high, cur)}` : ""}`
      : "No price found on this page",
    chart: range ? { band: [at(range.low), at(range.high)], median: at(range.median), dot: at(v.listing_price),
      label: `This listing ${money(v.listing_price, cur)}; genuine range ${money(range.low, cur)} to ${money(range.high, cur)}` } : null,
    // Price against the technology: a design cannot be sold below what it costs to build
    value: v.value ? { tone: { too_cheap_for_tech: "warn", cheap_for_tech: "warn", fair: "ok", pricey_for_tech: "none" }[v.value.verdict] || "none",
      text: v.value.text, word: { too_cheap_for_tech: "Too cheap for the technology it claims", cheap_for_tech: "Cheap for the technology", fair: "Fair for the technology", pricey_for_tech: "Pricey for the technology" }[v.value.verdict] || "" } : null,
    comparables: (v.comparables || []).slice(0, 6).map((c) => ({ text: `${c.name} · ${money(c.price, cur)}`, url: safeUrl(c.source_url), source: c.source || "" })),
    reasons: v.reasons || [],
  };
}

export function claimsWidget(v) {
  const tone = v && CLAIM_TONE[v.verdict];
  if (!tone) return null;
  return {
    verdict: v.verdict, tone: tone[0], word: v.headline || tone[1],
    claims: (v.claims || []).map((c) => ({ result: c.result, claim: c.claim, mark: CLAIM_MARK[c.result] || "help", text: c.claim, why: c.why, basis: c.basis,
      sources: (c.sources || []).filter((x) => safeUrl(x.url)).map((x) => ({ title: x.title || x.url, url: x.url })) })),
    // The same pages back every cited claim, so they are listed once under the claims, not under each one
    sources: [...new Map((v.claims || []).flatMap((c) => c.sources || []).filter((x) => safeUrl(x.url)).map((x) => [x.url, { title: x.title || x.url, url: x.url }])).values()].slice(0, 4),
    reasons: v.reasons || [],
  };
}

// The technology first: can what the listing claims exist at all? Only if it can is the price looked up (so an impossible
// technology costs nothing more and shows no price). Two calls, one after the other, so the technology shows first.
// demo: a local API's sample answers, labelled as such; any other API's sample answers are rejected.
const localApi = () => /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE);
const askPossible = (path, listing) => api(path, { method: "POST", body: JSON.stringify(listing) }, API_BASE, localApi());

export async function techCheck(listing) {
  const { body, source } = await askPossible("/v1/listings/claims-check", listing);
  const claims = claimsWidget(body);
  return { claims, answer: possibleAnswer(null, claims), demo: source === "mock" };
}

// claims: the technology result from techCheck, so the answer can weigh both (a doubtful claim lowers a fine price)
export async function priceCheck(listing, claims = null) {
  const { body, source } = await askPossible("/v1/listings/price-benchmark", listing);
  const price = priceWidget(body);
  return { price, answer: possibleAnswer(price, claims), demo: source === "mock" };
}

// sellerAge widget: how long has this product been listed? From the page's "Date First Available", read in the shopper's
// browser (no other page is opened). It is the LISTING's age, not the seller's: marketplaces do not publish a join date.
const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const ageWords = (d) => (d <= 0 ? "listed today" : d < 60 ? `${d} day${d === 1 ? "" : "s"} old` : d < 730 ? `about ${Math.round(d / 30)} months old` : `about ${Math.floor(d / 365)} years old`);
const FROM = { date_first_available: "First listed", first_review: "First review", review_floor: "Oldest review read" };
// Amazon's brand card: how long the BRAND has sold on Amazon and how buyers rate it. Not the listing's or the seller's age.
const brandLine = (b) => {
  if (!b) return null;
  const years = b.years_on_amazon ? `${b.years_on_amazon} year${/^1\+?$/.test(b.years_on_amazon) ? "" : "s"} on Amazon` : null;
  const rating = b.positive_ratings ? `${b.positive_ratings.percent}% positive from ${b.positive_ratings.customers} customers` : null;
  const parts = [b.name && `Brand: ${b.name}`, years, rating, b.recent_orders && `${b.recent_orders} recent orders`].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
};
export function listingAgeWidget(v) {
  if (!v) return null;
  const brand = brandLine(v.brand);
  const known = ["new", "recent", "under_a_year", "established", "listed_at_least", "no_reviews"].includes(v.verdict);
  if (!known && !brand) return null; // nothing to show
  if (!known) return { tone: "none", word: "Listing age not available", text: "This page shows no date for the listing.", band: null, listed: null, brand,
    note: "The brand's time on Amazon is not the listing's age.", reasons: [...(v.reasons || []), v.label].filter(Boolean) };
  const [y, m, d] = String(v.listed_on || "").split("-").map(Number);
  return { tone: ["ok", "warn", "none"].includes(v.tone) ? v.tone : "none", word: v.headline, text: v.text,
    band: v.age_days != null ? (v.verdict === "listed_at_least" ? `at least ${ageWords(v.age_days)}` : ageWords(v.age_days)) : null,
    listed: y && m && d ? `${FROM[v.basis] || "First listed"} ${d} ${MONTH_NAMES[m - 1]} ${y}` : null, brand,
    note: "This is the listing's age, not the seller's.", reasons: [...(v.reasons || []), v.label].filter(Boolean) };
}

// listing: {url, first_available, page_text}. null when the page shows no date (nothing is shown then).
export async function listingAge(listing) {
  const { url, first_available, page_text, oldest_review, reviews_read, reviews_complete, ratings_total, brand_text } = listing;
  const { body, source } = await askPossible("/v1/listings/listing-age", { url, first_available, page_text, oldest_review, reviews_read, reviews_complete, ratings_total, brand_text });
  const vm = listingAgeWidget(body);
  return vm ? { ...vm, demo: source === "mock" } : null;
}

// officialSeller: is the seller the brand, one of its authorised sellers, or a third party? From the lists brands themselves
// published (each answer cites its source). Information, never a score, never a warning colour. Nothing is shown for a brand
// that published nothing usable (no_list, unknown_brand): there it shows one quiet line saying so.
const OFFICIAL_SHOWN = ["official_brand", "official_seller", "amazon_retail", "third_party", "channel_not_listed", "channel_listed", "official_website", "third_party_website"];
const safeHttp = (u) => (/^https?:\/\//i.test(u || "") ? u : null);
export function officialSellerWidget(v) {
  if (!v) return null;
  // The brand published nothing usable: one quiet line saying so (and which brand and seller were seen), never a blank
  if (!OFFICIAL_SHOWN.includes(v.verdict)) {
    const seen = v.seller ? `seller: ${v.seller}` : "";
    return { quiet: true, tone: "none", word: null, text: `Seller check: ${v.text}${seen ? ` (${seen})` : ""}`, seller: v.seller || null, marketplace: v.marketplace || null, source: null, reasons: [] };
  }
  const src = v.source || {};
  const when = src.as_of || src.retrieved;
  const [y, m, d] = String(when || "").split("-").map(Number);
  // official: true = an official partner (green pill); false = not one (dark pill); null = not settled (plain). Never red.
  return { tone: v.tone === "ok" ? "ok" : "none", official: v.official === true ? true : v.official === false ? false : null,
    word: v.headline, text: v.text, seller: v.seller || null, marketplace: v.marketplace || null,
    source: src.text ? { text: src.text, url: safeHttp(src.url), when: y && m && d ? `${src.as_of ? "published" : "read"} ${d} ${MONTH_NAMES[m - 1]} ${y}` : null } : null,
    reasons: [...(v.reasons || []), v.label].filter(Boolean) };
}

// listing: {url, title, seller}.
export async function officialSeller(listing) {
  const { url, title, seller, brand_store } = listing; // only these: the brand is read from the title; brand_store is the "Visit the X Store" link's name
  const { body, source } = await askPossible("/v1/listings/official-seller", { url, title, seller, ...(brand_store ? { brand_store } : {}) });
  const vm = officialSellerWidget(body);
  return vm ? { ...vm, demo: source === "mock" } : null;
}

// Remembered per page for 10 minutes, like the check. A mock answer is rejected by api(), so no example is ever shown.
const verdicts = new Map();
export function reviewSummary(listing) {
  const hit = verdicts.get(listing.url);
  if (hit && Date.now() - hit.at < 10 * 60 * 1000) return hit.promise;
  const promise = api("/v1/listings/review-verdict", { method: "POST", body: JSON.stringify(listing) }).then(({ body }) => reviewWidget(body));
  verdicts.set(listing.url, { at: Date.now(), promise });
  promise.catch(() => verdicts.delete(listing.url)); // never remember a failure
  return promise;
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
      investigation_id: inv?.investigation_id || null, // "I already bought it" picks up this investigation
      plain: outcome.plain || null, // the answer in everyday words (engine/plain.py): shown first
      coverage: outcome.coverage?.countries || [], what_would_change: outcome.what_would_change || [],
      sources: (inv?.matches || []).filter((m) => m.tier !== "lookalike").slice(0, 4).map((m) => ({ authority: m.authority, record_id: m.record_id, url: m.url, title: m.title, local: m.local, tier: m.tier })),
      lead: outcome.lead_record || null, limitations: outcome.limitations || [], policy_version: outcome.policy_version } : null,
  };
}
