// Save keeps the shelf in this browser (no API call); the chat refuses example answers and shows the API's own errors.
import assert from "node:assert";
const store = {}; let calls = [];
globalThis.chrome = { storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o) }, onChanged: { addListener() {} } },
  runtime: { onMessage: { addListener: (fn) => (globalThis.__h = fn) }, onConnect: { addListener: (fn) => (globalThis.__c = fn) }, onInstalled: { addListener() {} }, onStartup: { addListener() {} } }, action: { setBadgeText() {}, setBadgeBackgroundColor() {} }, tabs: {} };
let mode = "real";
globalThis.fetch = async (url, o = {}) => {
  calls.push((o.method || "GET") + " " + url.replace(/^https?:\/\/[^/]+/, ""));
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

// Chat through the API
calls = []; mode = "mock";
r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en" });
assert.ok(!r.ok && /not live on the SafeShelf API yet/.test(r.error), "an example answer must be refused");
mode = "busy"; r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en" });
assert.match(r.error, /busy right now/);
mode = "real"; r = await send({ type: "safeshelf:chat", product_id: "unmatched", message: "why?", language: "en", session_id: "s1", context: { summary: "x" }, history: [] });
assert.ok(r.ok && r.result.text === "Price matches." && r.result.evidence_ids[0] === "EV-1F3B0227");
console.log("ok  save_chat");
