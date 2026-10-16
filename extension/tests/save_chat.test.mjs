// Save keeps the shelf in this browser (no API call); the chat refuses example answers and shows the API's own errors.
import assert from "node:assert";
const store = { session: { idToken: "id-1", refreshToken: "r-1", expiresAt: Date.now() + 3600e3, email: "ann@example.com", role: "shopper" } }; let calls = []; let auths = [];
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } },
  runtime: { onMessage: { addListener: (fn) => (globalThis.__h = fn) }, onMessageExternal: { addListener() {} }, onConnect: { addListener: (fn) => (globalThis.__c = fn) }, onInstalled: { addListener() {} }, onStartup: { addListener() {} } }, action: { setBadgeText() {}, setBadgeBackgroundColor() {} }, tabs: {} };
let mode = "real";
globalThis.fetch = async (url, o = {}) => {
  calls.push((o.method || "GET") + " " + url.replace(/^https?:\/\/[^/]+/, ""));
  auths.push(o.headers?.Authorization);
  if (mode === "busy") return { ok: false, status: 503, headers: { get: () => "real" }, json: async () => ({ detail: "The AI is busy right now. Please try again in a minute." }) };
  return { ok: true, status: 200, headers: { get: () => mode }, json: async () => ({ messages: [{ role: "assistant", text: "Price matches.", evidence_ids: ["EV-1F3B0227"] }] }) };
};
await import(new URL("../background.js", import.meta.url));
const send = (msg) => new Promise((res) => __h(msg, {}, res));

// Save: local only, no API call, works with or without a product match
let r = await send({ type: "safeshelf:save", product_id: null, meta: { title: "A", url: "https://x/dp/A", host: "x", level: null } });
assert.ok(r.ok && r.result.synced === false); assert.deepStrictEqual(calls, [], "SHELF_SYNC is off: Save must not call the API");
await send({ type: "safeshelf:save", product_id: "SS-P-1", meta: { title: "B", url: "https://x/dp/B", host: "x", level: "amber" } });
assert.strictEqual(store.shelf.length, 2); assert.strictEqual(store.shelf[0].level, "amber");
await send({ type: "safeshelf:save", product_id: "SS-P-1", meta: { title: "B again", url: "https://x/dp/B", host: "x", level: "red" } });
assert.strictEqual(store.shelf.length, 2, "saving the same page twice updates it");

// Product cards retain the original listing image; non-web URLs are discarded.
await send({ type: "safeshelf:save", product_id: "SS-P-1", meta: { title: "B", url: "https://x/dp/B", image_url: "https://m.media-amazon.com/images/I/product.jpg" } });
assert.strictEqual(store.shelf[0].image_url, "https://m.media-amazon.com/images/I/product.jpg");
await send({ type: "safeshelf:save", product_id: "SS-P-1", meta: { title: "B", url: "https://x/dp/B", image_url: "javascript:alert(1)" } });
assert.strictEqual(store.shelf[0].image_url, null);

// Chat through the API
calls = []; mode = "mock";
r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en" });
assert.ok(!r.ok && /Demo data was rejected/.test(r.error), "an example answer must be refused");
r = await send({ type: "safeshelf:check", page: { url: "https://www.amazon.in/dp/TEST", title: "Actual listing" } });
assert.ok(!r.ok && /Demo data was rejected/.test(r.error), "mock product verdicts must never reach the card");
mode = "busy"; r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en" });
assert.match(r.error, /busy right now/);
mode = "real"; r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en", session_id: "s1", context: { summary: "x" }, history: [] });
assert.ok(r.ok && r.result.text === "Price matches." && r.result.evidence_ids[0] === "EV-1F3B0227");
assert.ok(auths.length && auths.every((a) => a === "Bearer id-1"), "every API call carries the sign-in");

// Signed out: nothing is sent, and the answer says to sign in
delete store.session; calls = [];
r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en" });
assert.ok(!r.ok && r.signin && /Sign in/.test(r.error)); assert.deepStrictEqual(calls, [], "no API call without a sign-in");
console.log("ok  save_chat");
