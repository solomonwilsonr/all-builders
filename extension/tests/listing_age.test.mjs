// check.js: the sellerAge widget shows how long the PRODUCT has been listed (Date First Available), not the seller's age.
import assert from "node:assert";
import { readFileSync } from "node:fs";

const mock = JSON.parse(readFileSync(new URL("../../contracts/mock/listing_age.json", import.meta.url)));
let source = "mock", sent = null, answer = mock;
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, role: "shopper" } };
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
globalThis.fetch = async (url, init) => {
  sent = { url, body: JSON.parse(init.body) };
  return { ok: true, status: 200, headers: { get: () => source }, json: async () => answer };
};
const { listingAgeWidget, listingAge } = await import(new URL("../check.js", import.meta.url));

const vm = listingAgeWidget(mock);
assert.deepStrictEqual([vm.tone, vm.word, vm.band, vm.listed], ["warn", "New listing", "12 days old", "First listed 5 October 2026"]);
assert.strictEqual(vm.text, mock.text);
assert.strictEqual(vm.note, "This is the listing's age, not the seller's.");
assert.deepStrictEqual(vm.reasons, [...mock.reasons, mock.label]);

const at = (verdict, tone, age_days, listed_on, headline = "h") => listingAgeWidget({ verdict, tone, age_days, listed_on, headline, text: "t", reasons: [] });
assert.deepStrictEqual([at("recent", "warn", 46, "2026-09-01").band, at("recent", "warn", 46, "2026-09-01").listed], ["46 days old", "First listed 1 September 2026"]);
assert.strictEqual(at("under_a_year", "none", 214, "2026-03-17").band, "about 7 months old");
const old = at("established", "ok", 1352, "2023-02-03", "Long-listed product");
assert.deepStrictEqual([old.tone, old.band, old.listed, old.word], ["ok", "about 3 years old", "First listed 3 February 2023", "Long-listed product"]);
assert.strictEqual(at("new", "warn", 0, "2026-10-17").band, "listed today");
assert.strictEqual(at("new", "warn", 1, "2026-10-16").band, "1 day old");
// The first review, a floor from some reviews, and "no reviews"
const fr = listingAgeWidget({ verdict: "new", tone: "warn", headline: "New listing", basis: "first_review", age_days: 15, listed_on: "2026-10-02", text: "t" });
assert.deepStrictEqual([fr.band, fr.listed], ["15 days old", "First review 2 October 2026"]);
const floor = listingAgeWidget({ verdict: "listed_at_least", tone: "none", headline: "Listed for at least 15 days", basis: "review_floor", age_days: 15, listed_on: "2026-10-02", text: "t" });
assert.deepStrictEqual([floor.tone, floor.band, floor.listed], ["none", "at least 15 days old", "Oldest review read 2 October 2026"]);
const none = listingAgeWidget({ verdict: "no_reviews", tone: "warn", headline: "No reviews yet", basis: "no_reviews", age_days: null, listed_on: null, text: "No reviews yet: a very new or untested listing." });
assert.deepStrictEqual([none.tone, none.word, none.band, none.listed], ["warn", "No reviews yet", null, null]);
assert.strictEqual(listingAgeWidget({ verdict: "unknown", headline: "x" }), null, "no date and no brand card: nothing is shown");
// Amazon's brand card: the brand's time on Amazon, beside the age and never in place of it
const card = { name: "Portronics", years_on_amazon: "10+", positive_ratings: { percent: 84, customers: "10K+" }, recent_orders: "100K+" };
assert.strictEqual(listingAgeWidget({ ...mock, brand: card }).brand, "Brand: Portronics · 10+ years on Amazon · 84% positive from 10K+ customers · 100K+ recent orders");
assert.strictEqual(listingAgeWidget({ ...mock, brand: { name: "MAK", years_on_amazon: "1+", positive_ratings: null, recent_orders: null } }).brand, "Brand: MAK · 1+ year on Amazon");
assert.strictEqual(listingAgeWidget({ ...mock, brand: null }).brand, null);
const onlyBrand = listingAgeWidget({ verdict: "unknown", headline: "x", brand: card, reasons: [] });
assert.deepStrictEqual([onlyBrand.word, onlyBrand.tone, onlyBrand.band, onlyBrand.listed], ["Listing age not available", "none", null, null]);
assert.ok(onlyBrand.brand.startsWith("Brand: Portronics"));
assert.strictEqual(onlyBrand.note, "The brand's time on Amazon is not the listing's age.");
assert.strictEqual(listingAgeWidget(null), null);
assert.notStrictEqual(vm.tone, "red", "never red");
assert.ok(!JSON.stringify(vm).includes("seller joined") || vm.reasons.some((r) => r.includes("not the seller's")), "it never claims to be the seller's age");

// The call: the date as read from the page goes to the API; sample answers only for a local API
const { API_BASE } = await import(new URL("../config.js", import.meta.url));
const local = /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE);
const listing = { url: "https://www.amazon.in/dp/B0X", first_available: "5 October 2026", page_text: "Date First Available : 5 October 2026" };
if (local) {
  const out = await listingAge(listing);
  assert.strictEqual(out.demo, true);
  assert.strictEqual(out.word, "New listing");
} else {
  await assert.rejects(listingAge(listing), /Demo data was rejected/);
}
source = "real";
const real = await listingAge(listing);
assert.strictEqual(real.demo, false);
assert.ok(sent.url.endsWith("/v1/listings/listing-age"));
assert.deepStrictEqual(sent.body, { url: "https://www.amazon.in/dp/B0X", first_available: "5 October 2026", page_text: "Date First Available : 5 October 2026" });
// With no page date, what the reviews showed goes along too
await listingAge({ url: "https://www.amazon.in/dp/B0Z", oldest_review: "2026-10-02", reviews_read: 7, reviews_complete: true, ratings_total: 9 });
assert.deepStrictEqual(sent.body, { url: "https://www.amazon.in/dp/B0Z", oldest_review: "2026-10-02", reviews_read: 7, reviews_complete: true, ratings_total: 9 });
await listingAge({ url: "https://www.amazon.in/dp/B0Q", brand_text: "Top Brand Portronics 84% positive ratings from 10K+ customers 10+ years on Amazon" });
assert.strictEqual(sent.body.brand_text, "Top Brand Portronics 84% positive ratings from 10K+ customers 10+ years on Amazon");
answer = { ...mock, verdict: "unknown", headline: "Listing age not available", listed_on: null, age_days: null, brand: null };
assert.strictEqual(await listingAge({ url: "https://www.amazon.in/dp/B0Y" }), null, "an unknown answer shows nothing");
console.log("listing_age ok");
