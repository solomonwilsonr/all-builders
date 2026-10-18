// check.js (plan v2.2): the card's colour follows the code's outcome (red only for a local recall), the lines say what
// was checked, and a listing gets the live investigation while a mock answer is never used as data.
import assert from "node:assert";
const answers = {
  "/v1/listings/trust-check": { checks: {}, summary: "No warning signs", matched_by: null },
  "/v1/listings/safety-check": { verdict: "red", official_status: { recalled: true, checked: ["CPSC"], recall_ids: ["cpsc:1"], recalls: [] }, ai_findings: [], reviews_checked: 0 },
  "/v1/investigations": { outcome: "potential_concern", basis: "recalled_abroad_same_model", headline: "Recalled abroad, same model number; not confirmed for India",
    lead_record: { authority: "CPSC", record_id: "cpsc:26792", published: "2026-09-24" }, coverage: { summary: "India: no matching notice · the United States: notice found (live)",
    countries: [{ country: "IN", name: "India", is_market: true, state: "no_matching_notice_found", sources: [] }] },
    what_would_change: [{ fact: "the serial, lot or date code on the unit", how: "photo of the label" }], matches: [{ authority: "CPSC", record_id: "cpsc:26792", url: "https://www.cpsc.gov/x", tier: "exact", local: false }], source_mode: "live" },
};
// signed in, so every call carries a token (check.js signs each request)
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, role: "shopper" } };
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
globalThis.fetch = async (url) => {
  const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0];
  return { ok: true, status: 200, headers: { get: () => "real" }, json: async () => answers[path] };
};
const { outcomeLevel, outcomeLines, runCheck } = await import(new URL("../check.js", import.meta.url));

assert.strictEqual(outcomeLevel("confirmed_recall", "unknown"), "red");
assert.strictEqual(outcomeLevel("potential_concern", "green"), "amber");
assert.strictEqual(outcomeLevel("no_matching_notice_found", "unknown"), "unknown", "no notice found is not green without enough reviews");
assert.strictEqual(outcomeLevel("no_matching_notice_found", "green"), "green");
assert.strictEqual(outcomeLevel("insufficient_evidence", "green"), "unknown");

const lines = outcomeLines(answers["/v1/investigations"]);
assert.ok(lines[0].includes("not confirmed for India") && lines[0].includes("cpsc:26792"));
assert.ok(lines[1].startsWith("Checked: India"));
assert.ok(lines[2].startsWith("What would change this"));

const r = await runCheck({ url: "https://www.amazon.in/dp/X", title: "NEWDERY Power Bank ZHX-PB22", currency: "INR" });
assert.strictEqual(r.safe.level, "amber", "a US recall on an Amazon.in listing is amber, not red");
assert.strictEqual(r.outcome.coverage[0].country, "IN");
assert.strictEqual(r.outcome.sources[0].record_id, "cpsc:26792");

// recall_jp, as the live API answered it on 18 Oct: trust-check matches the listing by url to a look-alike whose stored
// answer has no notice, while the live investigation confirms the CAA recall. The recall must win.
const saved = { ...answers };
answers["/v1/listings/trust-check"] = { checks: { spec: { result: "flag", conflicts: ["capacity_mah differs (10000 vs 5000)"] } },
  summary: "Be careful: specs differ from the genuine model", matched_by: "url", matched_product_id: "SS-P-AMZ-B0BNL95XMR" };
answers["/v1/products/SS-P-AMZ-B0BNL95XMR/safety"] = { verdict: "not_enough_evidence", outcome: "no_matching_notice_found",
  headline: "No matching notice found in the sources checked", official_status: { recalled: false, checked: ["CAA"], recall_ids: [], recalls: [] }, ai_findings: [] };
answers["/v1/investigations"] = { outcome: "confirmed_recall", investigation_id: "INV-8C851D1A", headline: "Recalled in Japan: this exact model is on an official recall list",
  lead_record: { authority: "CAA", record_id: "jp_caa:00000035913" }, coverage: { countries: [] }, matches: [] };
const jp = await runCheck({ url: "https://www.amazon.co.jp/dp/SAFESHELF-W5PRO", title: "HAIARA モバイルバッテリー W5PRO 10000mAh", currency: "JPY" });
assert.strictEqual(jp.safe.level, "red", "a confirmed recall from the live investigation beats a look-alike's stored answer");
assert.strictEqual(jp.outcome.outcome, "confirmed_recall");
assert.strictEqual(jp.outcome.investigation_id, "INV-8C851D1A");
assert.ok(jp.safe.lines[0].includes("jp_caa:00000035913"));
answers["/v1/investigations"] = { outcome: "no_matching_notice_found", headline: "No matching notice" }; // no recall: the stored answer stays
const kept = await runCheck({ url: "https://www.amazon.co.jp/dp/OTHER", title: "Other", currency: "JPY" });
assert.strictEqual(kept.outcome.headline, "No matching notice found in the sources checked");
Object.assign(answers, saved);

answers["/v1/investigations"] = null; // old server: falls back to the older lines
globalThis.fetch = async (url) => ({ ok: true, status: 200, headers: { get: () => (url.includes("investigations") ? "mock" : "real") },
  json: async () => answers[url.replace(/^https?:\/\/[^/]+/, "").split("?")[0]] || { outcome: "confirmed_recall" } });
const old = await runCheck({ url: "https://www.amazon.in/dp/Y", title: "Other", currency: "INR" });
assert.strictEqual(old.outcome, null, "a mock investigation is never used as data");
console.log("ok  outcome");
