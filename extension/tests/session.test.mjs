// session.js: the sign-in token goes with every call, is renewed before it runs out and once more on a 401,
// a dead sign-in signs out, and only the sign-in page's origin can hand over a session.
import assert from "node:assert";
const store = {}; const listeners = {};
const tabs = [];
globalThis.chrome = {
  storage: { local: { get: async (k) => ({ [k]: store[k] }), set: async (o) => Object.assign(store, o), remove: async (k) => { delete store[k]; } }, onChanged: { addListener() {} } },
  runtime: { id: "ext-1", onMessage: { addListener: (fn) => (listeners.msg = fn) }, onMessageExternal: { addListener: (fn) => (listeners.ext = fn) }, onConnect: { addListener() {} }, onInstalled: { addListener() {} }, onStartup: { addListener() {} } },
  action: { setBadgeText() {}, setBadgeBackgroundColor() {} },
  tabs: { create: async (t) => tabs.push(t.url), remove: async () => {} },
};
const jwt = (exp) => `h.${Buffer.from(JSON.stringify({ exp, sub: "u1", email: "ann@example.com", role: "business" })).toString("base64url")}.s`;
let calls = []; let api401 = 0; let renewStatus = 200;
globalThis.fetch = async (url, o = {}) => {
  // Firestore is My Shelf's background sync after sign-in (shelf_sync.test.mjs covers it), not an API call
  if (!url.startsWith("https://firestore.googleapis.com/"))
    calls.push(url.includes("securetoken") ? "renew" : `${o.headers?.Authorization} ${url.replace(/^https?:\/\/[^/]+/, "")}`);
  if (url.includes("securetoken")) {
    if (renewStatus !== 200) return { ok: false, status: renewStatus, json: async () => ({}) };
    return { ok: true, status: 200, json: async () => ({ id_token: "id-new", refresh_token: "r-new", expires_in: "3600" }) };
  }
  if (url.startsWith("https://firestore.googleapis.com/")) return {ok: true, status: 200, json: async () => ({fields: {role: {stringValue: "user"}}})};
  if (url.endsWith("/v1/me")) return o.headers.Authorization === "Bearer bad" ? { ok: false, status: 401, json: async () => ({ detail: "Your sign-in has expired or is not valid. Sign in again." }) }
    : { ok: true, status: 200, json: async () => ({ uid: "u1", email: "ann@example.com", role: "business" }) };
  if (api401-- > 0) return { ok: false, status: 401, headers: { get: () => null }, json: async () => ({ detail: "Sign in" }) };
  return { ok: true, status: 200, headers: { get: () => "real" }, json: async () => ({ ok: 1 }) };
};
await import(new URL("../background.js", import.meta.url));
const { api } = await import(new URL("../check.js", import.meta.url));
const send = (msg) => new Promise((res) => listeners.msg(msg, {}, res));
const handOff = (msg, origin) => new Promise((res) => { if (listeners.ext(msg, { origin, tab: { id: 7 } }, res) !== true) res(undefined); });

// Signed out
assert.strictEqual((await send({ type: "safeshelf:account" })).result, null);
await send({ type: "safeshelf:signin" });
const { SIGNIN_URL } = await import(new URL("../config.js", import.meta.url));  // local or deployed build
assert.strictEqual(tabs[0], `${SIGNIN_URL}?ext=ext-1`);

// A session from another site is ignored; malformed or expired tokens are not kept
assert.strictEqual(await handOff({ type: "safeshelf:session", idToken: jwt(9e9), refreshToken: "r" }, "https://evil.example"), undefined);
assert.strictEqual(store.session, undefined);
let r = await handOff({ type: "safeshelf:session", idToken: "bad", refreshToken: "r" }, "https://shelf2026-3656b.web.app");
assert.ok(!r.ok); assert.strictEqual(store.session, undefined);

r = await handOff({ type: "safeshelf:session", idToken: jwt(1), refreshToken: "r" }, "http://localhost:8095");
assert.ok(!r.ok && /Sign in again/.test(r.error));
assert.strictEqual(store.session, undefined);

// Sign-in succeeds while the application API is offline, with no API requests.
const onlineFetch = globalThis.fetch;
calls = [];
globalThis.fetch = async () => { calls.push("unexpected API request"); throw new Error("Local API offline"); };
r = await handOff({ type: "safeshelf:session", idToken: jwt(Date.now() / 1000 + 3600), refreshToken: "r-1", name: "Ann" }, "https://shelf2026-3656b.web.app");
assert.deepStrictEqual(r, { ok: true, role: "business" });
assert.deepStrictEqual(calls, []);
assert.strictEqual(store.session.uid, "u1");
assert.strictEqual(store.session.refreshToken, "r-1");
assert.strictEqual((await send({ type: "safeshelf:account", check: true })).result.email, "ann@example.com");
globalThis.fetch = onlineFetch;
assert.deepStrictEqual((await send({ type: "safeshelf:account" })).result, { email: "ann@example.com", name: "Ann", role: "business" });

// Calls carry the token; one about to run out is renewed first
calls = [];
await api("/v1/recalls");
assert.match(calls[0], /^Bearer h\..+ \/v1\/recalls$/);
store.session.expiresAt = Date.now() + 30_000;
calls = [];
await api("/v1/recalls");
assert.deepStrictEqual(calls, ["renew", "Bearer id-new /v1/recalls"]);
assert.strictEqual(store.session.refreshToken, "r-new");

// A 401 is asked once more with a fresh token; two in a row means sign in again
calls = []; api401 = 1;
await api("/v1/recalls");
assert.deepStrictEqual(calls, ["Bearer id-new /v1/recalls", "renew", "Bearer id-new /v1/recalls"]);
api401 = 2;
await assert.rejects(() => api("/v1/recalls"), (e) => e.name === "SignInNeeded");

// A revoked sign-in signs out
store.session.expiresAt = 0; renewStatus = 400;
await assert.rejects(() => api("/v1/recalls"), (e) => e.name === "SignInNeeded" && /has ended/.test(e.message));
assert.strictEqual(store.session, undefined);

// Sign out
renewStatus = 200;
await handOff({ type: "safeshelf:session", idToken: jwt(Date.now() / 1000 + 3600), refreshToken: "r-2" }, "https://shelf2026-3656b.web.app");
store.costGuard = true;
const deniedSetting = await send({ type: "safeshelf:set-cost-guard", enabled: false });
assert.strictEqual(deniedSetting.ok, false);
assert.match(deniedSetting.error, /Administrator access required/);
assert.strictEqual(store.costGuard, true);
await send({ type: "safeshelf:signout" });
assert.strictEqual(store.session, undefined);
console.log("ok  session");
