// check.js: the officialSeller widget. Information only: green or neutral, never a warning colour; nothing for a brand with no list.
import assert from "node:assert";
import { readFileSync } from "node:fs";

const mock = JSON.parse(readFileSync(new URL("../../contracts/mock/official_seller.json", import.meta.url)));
let source = "mock", sent = null, answer = mock;
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, role: "shopper" } };
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
globalThis.fetch = async (url, init) => {
  sent = { url, body: JSON.parse(init.body) };
  return { ok: true, status: 200, headers: { get: () => source }, json: async () => answer };
};
const { officialSellerWidget, officialSeller } = await import(new URL("../check.js", import.meta.url));

const vm = officialSellerWidget(mock);
assert.deepStrictEqual([vm.tone, vm.word, vm.official, vm.seller, vm.marketplace], ["none", "Not an official partner", false, "Random Traders", "amazon.in"]);
assert.strictEqual(vm.text, mock.text);
assert.deepStrictEqual(vm.source, { text: mock.source.text, url: "https://www.boat-lifestyle.com/pages/warranty", when: "read 17 October 2026" });
assert.deepStrictEqual(vm.reasons, [...mock.reasons, mock.label]);

// A date the brand published is shown as published; an official seller is green; other tones are neutral
const nothing = officialSellerWidget({ ...mock, verdict: "channel_not_listed", headline: "Not an official channel, per CMF", source: { text: "Nothing's support article", url: "https://support.nothing.tech/x", as_of: "2025-08-28", retrieved: "2026-10-17" } });
assert.strictEqual(nothing.source.when, "published 28 August 2025");
const yes = officialSellerWidget({ ...mock, verdict: "official_seller", tone: "ok", official: true, headline: "Official partner" });
assert.deepStrictEqual([yes.tone, yes.official, yes.word], ["ok", true, "Official partner"]);
assert.strictEqual(officialSellerWidget({ ...mock, official: null }).official, null, "not settled: neither pill");
assert.strictEqual(officialSellerWidget({ ...mock, official: "yes" }).official, null, "only true or false counts");
assert.strictEqual(officialSellerWidget({ ...mock, verdict: "third_party", tone: "warn" }).tone, "none", "never a warning colour, whatever the server says");
assert.strictEqual(officialSellerWidget({ ...mock, tone: "red" }).tone, "none");
for (const verdict of ["official_brand", "official_seller", "amazon_retail", "third_party", "channel_not_listed", "channel_listed", "official_website", "third_party_website"]) {
  assert.ok(officialSellerWidget({ ...mock, verdict }), verdict);
}
// Nothing for a brand with no list, and only http(s) source links
const quiet = officialSellerWidget({ ...mock, verdict: "unknown_brand", brand: null, seller: "Z Traders", text: "No brand with a published seller list is named in the title." });
assert.deepStrictEqual([quiet.quiet, quiet.tone, quiet.text], [true, "none", "Seller check: No brand with a published seller list is named in the title. (seller: Z Traders)"]);
assert.strictEqual(officialSellerWidget({ ...mock, verdict: "no_list", seller: null, text: "x" }).text, "Seller check: x");
assert.strictEqual(officialSellerWidget(null), null);
assert.strictEqual(officialSellerWidget({ ...mock, source: { text: "x", url: "javascript:alert(1)", retrieved: "2026-10-17" } }).source.url, null);
assert.strictEqual(officialSellerWidget({ ...mock, source: null }).source, null);

// The call: sample answers only for a local API
const { API_BASE } = await import(new URL("../config.js", import.meta.url));
const local = /\/\/(localhost|127\.0\.0\.1)/.test(API_BASE);
const listing = { url: "https://www.amazon.in/dp/B0X", title: "boAt Airdopes", seller: "Random Traders" };
if (local) {
  const out = await officialSeller(listing);
  assert.strictEqual(out.demo, true);
  assert.strictEqual(out.word, "Not an official partner");
} else {
  await assert.rejects(officialSeller(listing), /Demo data was rejected/);
}
source = "real";
const real = await officialSeller(listing);
assert.strictEqual(real.demo, false);
assert.ok(sent.url.endsWith("/v1/listings/official-seller"));
assert.deepStrictEqual(sent.body, listing);
sent = null; await officialSeller({ ...listing, page_text: "Brand\tboAt" });
assert.deepStrictEqual(Object.keys(sent.body).sort(), ["seller", "title", "url"], "the page text is never sent");
answer = { ...mock, verdict: "no_list", headline: "No official seller information", brand: null, source: null, text: "vivo publishes no list of authorised Amazon.in sellers." };
const none = await officialSeller(listing);
assert.strictEqual(none.quiet, true, "no published list: one quiet line, not a blank");
assert.ok(none.text.startsWith("Seller check: vivo publishes no list"));
console.log("official_seller ok");
