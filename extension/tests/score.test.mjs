// check.js: the SafeShelf score (weights, unknown checks left out, caps) and the order the cards show in.
import assert from "node:assert";
const store = {};
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } } };
const { safetyScore, scoreOrder, scorePoints, SCORE_WEIGHTS } = await import(new URL("../check.js", import.meta.url));

assert.strictEqual(Object.values(SCORE_WEIGHTS).reduce((a, b) => a + b, 0), 100);
assert.ok(SCORE_WEIGHTS.tech > SCORE_WEIGHTS.reviews, "technology weighs more than reviews");
assert.ok(SCORE_WEIGHTS.price > SCORE_WEIGHTS.seller, "price weighs more than the seller check");

const all = { recall: "no_matching_notice_found", tech: { verdict: "possible", claims: [{ result: "possible" }] }, reviews: { tone: "mixed", positiveShare: 0.6, flagCount: 0 },
  seller: { verdict: "third_party" }, price: { verdict: "normal" }, age: { verdict: "established" } };
let s = safetyScore(all);
assert.strictEqual(s.score, 86, "8575 / 100 = 85.75: (95*30 + 100*25 + 55*15 + 100*15 + 40*10 + 100*5) / 100");
assert.strictEqual(s.band.key, "good");
assert.strictEqual(s.used, 6);

// A check with no result is left out and the rest are rescaled: not counted as 0 or 100
s = safetyScore({ ...all, price: null, age: undefined });
assert.strictEqual(s.used, 4);
assert.strictEqual(s.score, Math.round((95 * 30 + 100 * 25 + 55 * 15 + 40 * 10) / 80));
// Technology "possible" with nothing assessed is not a pass
assert.strictEqual(scorePoints("tech", { verdict: "possible", claims: [] }), null);
assert.strictEqual(scorePoints("tech", { verdict: "possible", claims: [{ result: "cant_tell" }] }), null);
// Fake-review flags cost 10 each, at most 30
assert.strictEqual(scorePoints("reviews", { tone: "good", positiveShare: 0.9, flagCount: 5 }), 70);
assert.strictEqual(scorePoints("reviews", { tone: "none" }), null);
// Price: the worse of the market price and the price for the technology
assert.strictEqual(scorePoints("price", { verdict: "normal", valueVerdict: "too_cheap_for_tech" }), 10);

// Caps: the number can never look better than these facts allow
assert.strictEqual(safetyScore({ ...all, recall: "confirmed_recall" }).score, 15);
assert.strictEqual(safetyScore({ ...all, tech: { verdict: "not_possible", claims: [{ result: "not_possible" }] } }).score, 25);
assert.strictEqual(safetyScore({ ...all, price: { verdict: "too_low" }, seller: { verdict: "third_party" } }).score, 40);
assert.match(safetyScore({ ...all, recall: "confirmed_recall" }).cap, /recall/);

// Under half of the weight known: no number
s = safetyScore({ age: { verdict: "new" }, price: { verdict: "normal" } });
assert.strictEqual(s.enough, false);
assert.strictEqual(safetyScore({}).score, null);

// Order: the worst check first, checks with no result last
let order = scoreOrder(safetyScore({ ...all, tech: { verdict: "doubtful", claims: [{ result: "doubtful" }] } }));
assert.strictEqual(order.tech, 0, "doubtful technology comes first");
assert.strictEqual(order.reviews, 1, "then the poor reviews");
order = scoreOrder(safetyScore({ ...all, price: null }));
assert.ok(order.price >= 100, "a check with no result goes to the bottom");
order = scoreOrder(safetyScore({ ...all, reviews: { tone: "poor", positiveShare: 0.2, flagCount: 0 }, tech: { verdict: "possible", claims: [{ result: "possible" }] } }));
assert.strictEqual(order.reviews, 0, "bad reviews come first when technology is fine");
// A cheaper-than-usual price now comes ahead of a third-party seller, and costs more points
assert.strictEqual(scorePoints("price", { verdict: "below_usual" }), 45);
assert.strictEqual(scorePoints("price", { verdict: "normal", valueVerdict: "cheap_for_tech" }), 40);
order = scoreOrder(safetyScore({ ...all, price: { verdict: "below_usual" } }));
assert.ok(order.price < order.seller, "cheap price (15 x 55 lost) outranks a third-party seller (10 x 60 lost)");
// A product like the amber "Buyers report safety problems" one: no official recall, but buyers report a safety risk, the price is
// not possible for the technology, and the seller is not an official partner. It must not read as "Looks good".
const risky = { recall: "no_matching_notice_found", level: "amber", answer: { verdict: "not_possible" }, tech: { verdict: "possible", claims: [{ result: "possible" }] },
  reviews: { tone: "good", positiveShare: 0.8, flagCount: 0 }, seller: { verdict: "channel_not_listed", official: false }, price: { verdict: "below_usual", valueVerdict: "too_cheap_for_tech" },
  age: { verdict: "listed_at_least" } };
s = safetyScore(risky);
assert.ok(s.score <= 40, `risky listing scored ${s.score}`);
assert.ok(["careful", "avoid"].includes(s.band.key));
assert.strictEqual(safetyScore({ ...all, level: "amber" }).score, 59, "an amber verdict can never score above 59");
assert.strictEqual(safetyScore({ ...all, level: "red" }).score, 25);
assert.strictEqual(safetyScore({ ...all, level: "green" }).score, 86, "a green verdict changes nothing");
assert.strictEqual(scoreOrder(safetyScore(risky)).recall >= 0, true);
// Poor reviews cannot hide behind a clean recall check and a possible technology (the Redmi 15C: 3.1 stars, 53% positive, no recall)
const redmi = { recall: "no_matching_notice_found", level: "green", tech: { verdict: "possible", claims: [{ result: "possible" }] },
  reviews: { tone: "poor", positiveShare: 0.53, flagCount: 0 }, seller: { verdict: "third_party" }, price: { verdict: "normal" }, age: { verdict: "established" } };
s = safetyScore(redmi);
assert.ok(s.score <= 59 && s.band.key !== "good", `poor reviews scored ${s.score}`);
assert.match(s.cap, /buyer reviews/);
assert.ok(safetyScore({ ...redmi, reviews: { tone: "mixed", positiveShare: 0.6, flagCount: 0 } }).score >= 60, "mixed reviews are not capped");
assert.strictEqual(safetyScore({ ...redmi, seller: { verdict: "third_party" }, age: { verdict: "new" } }).cap, "buyer reviews coming out poor");
console.log("score ok");
