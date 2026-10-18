// check.js: the "Is it any good?" widget's view model. Quality only, never red; a mock answer is never shown.
import assert from "node:assert";
import { readFileSync } from "node:fs";

const mock = JSON.parse(readFileSync(new URL("../../contracts/mock/review_verdict.json", import.meta.url)));
let source = "real";
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, role: "shopper" } };
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
globalThis.fetch = async () => ({ ok: true, status: 200, headers: { get: () => source }, json: async () => mock });
const { reviewWidget, reviewSummary } = await import(new URL("../check.js", import.meta.url));

const vm = reviewWidget(mock);
assert.strictEqual(vm.positiveShare, 0.76, "positive bar uses the supplied rating share");
assert.strictEqual(vm.complaints[0].share, 0.12, "concern bars retain the numeric buyer share");
assert.strictEqual(reviewWidget({ ...mock, rating: {} }).positiveShare, null, "missing positive share does not create a chart");
assert.strictEqual(reviewWidget({ ...mock, complaints: [{ phrase: "issue", mentions: 2 }] }).complaints[0].share, null, "review counts are not converted to buyer percentages");
assert.strictEqual(reviewWidget({ ...mock, complaints: [{ phrase: "issue", share_estimate: 0 }] }).complaints[0].share, 0, "zero share remains zero");
assert.strictEqual(vm.tone, "mixed");
assert.strictEqual(vm.word, "Mixed reviews");
assert.strictEqual(vm.stars, "★ 4.1 · 3,412 ratings · 38 reviews read");
assert.deepStrictEqual(vm.liked, ["Charges fast", "Good value"]);
assert.deepStrictEqual(vm.complaints.map((c) => [c.text, c.sub]), [["Stopped working after 2 months", "about 12% of buyers"], ["Cable too short", "about 3% of buyers"]]);
assert.deepStrictEqual(vm.complaints[0].reviews[0], { stars: "★", date: "2026-09-02", title: "Died after 8 weeks", text: mock.complaints[0].reviews[0].text }, "the reviews counted come from the answer itself");
assert.strictEqual(vm.complaints[0].reviews.length, 2);
assert.deepStrictEqual(vm.reasons, mock.reasons);
assert.strictEqual(vm.warning, null);
assert.strictEqual(vm.note, null);

const inflated = reviewWidget({ ...mock, verdict: "good", headline: "Mostly good", confidence: "low", complaints: [],
  trust: { may_be_inflated: true, flags: [{ kind: "same_day_burst", detail: "7 five-star reviews were posted on 3 Oct 2026" }] } });
assert.strictEqual(inflated.tone, "good");
assert.deepStrictEqual(inflated.complaints, []);
assert.strictEqual(inflated.warning, "Some reviews may not be genuine: 7 five-star reviews were posted on 3 Oct 2026");
assert.strictEqual(inflated.note, "Low confidence");

const few = reviewWidget({ verdict: "not_enough_reviews", headline: "Not enough reviews yet", rating: { count: 1 }, reviews_read: 1,
  complaints: [{ phrase: "broke", mentions: 1, share_estimate: null }] });
assert.strictEqual(few.tone, "none");
assert.strictEqual(few.stars, "1 rating · 1 review read");
assert.strictEqual(few.complaints[0].sub, "1 review");
assert.strictEqual(few.note, "Too few ratings to judge");
assert.ok(!Object.values({ ...vm, few }).includes("red"), "the widget never uses red");

const many = reviewWidget({ ...mock, complaints: Array.from({ length: 14 }, (_, i) => ({ phrase: `issue ${i}`, mentions: 20 - i, share_estimate: null })) });
assert.strictEqual(many.complaints.length, 10, "at most ten complaints");
assert.strictEqual(many.complaints[0].sub, "20 reviews");

assert.strictEqual(reviewWidget(null), null);
assert.strictEqual(reviewWidget({ verdict: "green" }), null, "only the review verdict's own words are accepted");

// The background call: a real answer becomes the view model; a mock answer is rejected, never shown.
assert.strictEqual((await reviewSummary({ url: "https://www.amazon.in/dp/A" })).word, "Mixed reviews");
source = "mock";
await assert.rejects(reviewSummary({ url: "https://www.amazon.in/dp/B" }), /Demo data was rejected/);
console.log("review_widget ok");
