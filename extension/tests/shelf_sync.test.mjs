// shelf-sync.js: signed in, My Shelf is also kept in the account (Firestore) so the website shows it; items saved
// signed out go up on the next sync, items added or removed on the website come down, and a removal that couldn't
// reach Firestore is never brought back by a sync.
import assert from "node:assert";
const store = { enabled: true }; const listeners = {};
globalThis.chrome = {
  storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, structuredClone(o)), remove: async (k) => { delete store[k]; } }, onChanged: { addListener() {} } },
  runtime: { id: "ext-1", onMessage: { addListener: (fn) => (listeners.msg = fn) }, onMessageExternal: { addListener: (fn) => (listeners.ext = fn) }, onConnect: { addListener() {} }, onInstalled: { addListener() {} }, onStartup: { addListener() {} } },
  action: { setBadgeText() {}, setBadgeBackgroundColor() {} },
  tabs: { create: async () => {}, remove: async () => {} },
};
const docs = new Map(); // path -> fields, the fake Firestore
let calls = []; let deletesFail = false;
const PREFIX = "https://firestore.googleapis.com/v1/projects/shelf2026-3656b/databases/(default)/documents/";
globalThis.fetch = async (url, o = {}) => {
  if (!url.startsWith(PREFIX)) throw new Error(`unexpected request ${url}`);
  const path = url.slice(PREFIX.length).split("?")[0];
  calls.push(`${o.method || "GET"} ${path}`);
  assert.strictEqual(o.headers.Authorization, "Bearer id-1");
  if (o.method === "PATCH") { docs.set(path, JSON.parse(o.body).fields); return { ok: true, status: 200, json: async () => ({}) }; }
  if (o.method === "DELETE") { if (deletesFail) return { ok: false, status: 503 }; docs.delete(path); return { ok: true, status: 200, json: async () => ({}) }; }
  const documents = [...docs].filter(([p]) => p.startsWith(`${path}/`)).map(([name, fields]) => ({ name, fields }));
  return { ok: true, status: 200, json: async () => ({ documents }) };
};
await import(new URL("../background.js", import.meta.url));
const send = (msg) => new Promise((res) => listeners.msg(msg, {}, res));
const settle = () => new Promise((r) => setTimeout(r, 20));
const save = (title, url) => send({ type: "safeshelf:save", product_id: null, meta: { title, url, host: "x", level: null } });

// Signed out: saved here only, nothing sent
await save("A", "https://x/dp/A"); await settle();
assert.deepStrictEqual(calls, []);
let r = await send({ type: "safeshelf:shelf-sync" });
assert.strictEqual(r.result.signedIn, false);

// Signed in: the sync uploads A; a new save goes up by itself
store.session = { idToken: "id-1", refreshToken: "r", expiresAt: Date.now() + 3600e3, uid: "u1" };
r = await send({ type: "safeshelf:shelf-sync" });
assert.ok(r.result.synced, r.result.error); assert.match(r.result.website, /\/site\/shelf\.html$/);
assert.strictEqual(docs.size, 1);
assert.strictEqual(store.shelf[0].cloud, "u1");
await save("B", "https://x/dp/B"); await settle();
assert.strictEqual(docs.size, 2);
const fieldsB = [...docs.values()].find((f) => f.title.stringValue === "B");
assert.strictEqual(fieldsB.key.stringValue, "unmatched|https://x/dp/B");
assert.ok([...docs.keys()].every((p) => /^users\/u1\/shelf\/[0-9a-f]{40}$/.test(p)), "document ids hold no slashes");

// Added on the website (another device) comes down; removed on the website goes away here
docs.set("users/u1/shelf/web1", { key: { stringValue: "unmatched|https://x/dp/C" }, title: { stringValue: "C" }, url: { stringValue: "https://x/dp/C" }, saved_at: { stringValue: "2030-01-01T00:00:00Z" } });
const pathA = [...docs].find(([, f]) => f.title.stringValue === "A")[0];
docs.delete(pathA);
await send({ type: "safeshelf:shelf-sync" });
assert.deepStrictEqual(store.shelf.map((i) => i.title), ["C", "B"]);

// Remove here deletes it in the account
await send({ type: "safeshelf:shelf-remove", id: "unmatched|https://x/dp/C" });
assert.ok(![...docs.values()].some((f) => f.title.stringValue === "C"));
assert.deepStrictEqual(store.shelf.map((i) => i.title), ["B"]);

// A removal that fails is kept for later and not brought back by a sync
deletesFail = true;
await send({ type: "safeshelf:unsave", url: "https://x/dp/B" });
assert.strictEqual(store.shelf.length, 0); assert.strictEqual(store.shelfDeleted.length, 1);
r = await send({ type: "safeshelf:shelf-sync" });
assert.strictEqual(r.result.synced, false);
assert.strictEqual(store.shelf.length, 0, "B is not brought back");
deletesFail = false;
r = await send({ type: "safeshelf:shelf-sync" });
assert.ok(r.result.synced); assert.strictEqual(docs.size, 0); assert.deepStrictEqual(store.shelfDeleted, []);

console.log("ok  shelf sync: signed-out saves go up, website changes come down, failed removals don't come back");
