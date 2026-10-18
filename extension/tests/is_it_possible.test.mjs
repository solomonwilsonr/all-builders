// check.js: the "Is it possible?" widget's view models (price chart, claims) and the two-call wrapper. Never red.
import assert from "node:assert";
import { readFileSync } from "node:fs";

const price = JSON.parse(readFileSync(new URL("../../contracts/mock/price_benchmark.json", import.meta.url)));
const claims = JSON.parse(readFileSync(new URL("../../contracts/mock/claims_check.json", import.meta.url)));
let source = "mock", fail = null;
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, role: "shopper" } };
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
globalThis.fetch = async (url) => {
  if (fail && url.includes(fail)) return { ok: false, status: 500, headers: { get: () => null }, json: async () => ({ detail: "boom" }) };
  return { ok: true, status: 200, headers: { get: () => source }, json: async () => (url.includes("price-benchmark") ? price : claims) };
};
const { priceWidget, claimsWidget, possibleAnswer, techCheck, priceCheck } = await import(new URL("../check.js", import.meta.url));

const p = priceWidget(price);
assert.strictEqual(p.tone, "warn");
assert.strictEqual(p.word, "Price looks too low");
assert.strictEqual(p.line, "₹299 · genuine 60W chargers and adapters: ₹1,199 – ₹2,499");
// the track runs from 0 to 10% past the dearest price (₹2,499 x 1.1): the dot sits far left of the genuine band
assert.ok(p.chart.dot < p.chart.band[0] && p.chart.band[0] < p.chart.median && p.chart.median < p.chart.band[1]);
assert.ok(p.chart.dot > 0 && p.chart.band[1] < 100);
assert.strictEqual(Math.round(p.chart.dot), 11);
assert.strictEqual(p.chart.label, "This listing ₹299; genuine range ₹1,199 to ₹2,499");
assert.strictEqual(p.value.word, "Too cheap for the technology it claims");
assert.strictEqual(p.value.tone, "warn");
assert.strictEqual(p.value.text, "₹5 per watt against ₹19 to ₹38 per watt for genuine GaN chargers and adapters");
assert.strictEqual(priceWidget({ ...price, value: null }).value, null);
assert.strictEqual(p.comparables.length, 4);
assert.deepStrictEqual(p.comparables[0], { text: "Ambrane 60W GaN charger · ₹1,199", url: "https://www.ambraneindia.com/", source: "ambraneindia.com" });

const noData = priceWidget({ verdict: "not_enough_data", listing_price: 499, currency: "INR", genuine_range: null, comparables: [], reasons: ["Only 1 reference price"] });
assert.strictEqual(noData.chart, null);
assert.strictEqual(noData.tone, "none");
assert.strictEqual(priceWidget({ verdict: "normal", listing_price: null, genuine_range: null, comparables: [] }).line, "No price found on this page");
const unsafe = priceWidget({ ...price, comparables: [{ name: "x", price: 1, source_url: "javascript:alert(1)" }] });
assert.strictEqual(unsafe.comparables[0].url, null, "only http(s) links are kept");

const c = claimsWidget(claims);
assert.strictEqual(c.tone, "warn");
assert.strictEqual(c.verdict, "doubtful");
assert.deepStrictEqual(c.claims.map((x) => x.mark), ["check", "warn"]);
assert.strictEqual(c.claims[1].sources[0].url, "https://www.energy.gov/");
assert.deepStrictEqual(c.sources, [{ title: "How phone chargers use power", url: "https://www.energy.gov/" }], "sources are listed once");
assert.strictEqual(claimsWidget({ verdict: "cant_tell", claims: [], reasons: [] }).tone, "none");
const impossible = claimsWidget({ ...claims, verdict: "not_possible", claims: [{ claim: "20,000mAh at 150 g", result: "not_possible", why: "The cells alone weigh 274 g", basis: "rule", sources: [] }] });
for (const vm of [p, noData, c, impossible, claimsWidget({ ...claims, verdict: "possible" })]) assert.notStrictEqual(vm.tone, "red", "never red");
// The one-line answer: the worse of the price answer and the claims, in plain words
const ans = possibleAnswer(p, c);
assert.strictEqual(ans.verdict, "not_possible");
assert.strictEqual(ans.word, "Not possible at this price");
assert.strictEqual(ans.question, "₹299 for a 60W charger");
assert.ok(ans.text.startsWith("Genuine 60W chargers cost ₹1,199 to ₹2,499. ₹299 is 25%"));
assert.strictEqual(ans.tone, "warn");
const unlikely = possibleAnswer({ ...p, answer: { verdict: "unlikely", subject: "33W charger", text: "x" }, listing: 349 }, null);
assert.deepStrictEqual([unlikely.word, unlikely.question], ["Unlikely at this price", "₹349 for a 33W charger"]);
const okPrice = { ...p, answer: { verdict: "possible", subject: "60W charger", text: "ok" } };
assert.deepStrictEqual([possibleAnswer(okPrice, claimsWidget({ ...claims, verdict: "possible", claims: [claims.claims[0]] })).word], ["Possible at this price"]);
assert.strictEqual(possibleAnswer(okPrice, c).word, "A claim looks doubtful", "a doubtful claim lowers a fine price");
// Technology that cannot exist is the whole answer: no price, and the question is about the claim itself
const stopped = possibleAnswer(null, impossible);
assert.deepStrictEqual([stopped.word, stopped.verdict, stopped.question, stopped.text],
  ["A claim is not possible", "not_possible", '"20,000mAh at 150 g"', "20,000mAh at 150 g: The cells alone weigh 274 g"]);
assert.strictEqual(possibleAnswer(null, claimsWidget({ ...claims, verdict: "possible", claims: [claims.claims[0]] })), null, "a fine technology alone says nothing about the price");
assert.strictEqual(possibleAnswer({ ...p, answer: { verdict: "cant_tell", subject: null, text: "?" } }, null).tone, "none");
assert.strictEqual(possibleAnswer(null, null), null);
assert.strictEqual(priceWidget(null), null);
assert.strictEqual(priceWidget({ verdict: "green" }), null);
assert.strictEqual(claimsWidget({ verdict: "high" }), null);

// Sample answers (source "mock") are shown, labelled as a demo, only for a local API; against any other API they are rejected.
const { API_BASE } = await import(new URL("../config.js", import.meta.url));
const local = /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE);
if (local) {
  const tech = await techCheck({ url: "https://www.amazon.in/dp/A" });
  assert.strictEqual(tech.claims.verdict, "doubtful");
  assert.strictEqual(tech.demo, true);
  assert.strictEqual(tech.answer.word, "A claim looks doubtful");
  const pr = await priceCheck({ url: "https://www.amazon.in/dp/A" }, tech.claims);
  assert.strictEqual(pr.price.word, "Price looks too low");
  assert.strictEqual(pr.answer.word, "Not possible at this price", "the price answer, weighed with the technology");
} else {
  await assert.rejects(techCheck({ url: "https://www.amazon.in/dp/A" }), /Demo data was rejected/);
  await assert.rejects(priceCheck({ url: "https://www.amazon.in/dp/A" }), /Demo data was rejected/);
}
// Real answers: no demo label
source = "real";
const real = await techCheck({ url: "https://www.amazon.in/dp/R" });
assert.ok(real.claims && real.demo === false);
assert.strictEqual((await priceCheck({ url: "https://www.amazon.in/dp/R" }, real.claims)).demo, false);
// A failed call is an error for the caller to handle: one part failing must not hide the other
fail = "claims-check";
await assert.rejects(techCheck({ url: "https://www.amazon.in/dp/B" }), /boom/);
assert.ok((await priceCheck({ url: "https://www.amazon.in/dp/B" })).price, "the price still works when the technology call failed");
fail = "price-benchmark";
await assert.rejects(priceCheck({ url: "https://www.amazon.in/dp/C" }), /boom/);
console.log("is_it_possible ok");
