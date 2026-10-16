// ops.js: an endpoint that is not live is never called, and an example (mock) answer is never treated as data.
import assert from "node:assert";
const calls = [];
globalThis.chrome = { storage: { local: { get: async () => ({ session: { idToken: "t", refreshToken: "r", expiresAt: Date.now() + 3600e3 } }), set: async () => {} } } };
globalThis.fetch = async (url, o = {}) => {
  calls.push((o.method || "GET") + " " + url.replace(/^https?:\/\/[^/]+/, ""));
  if (url.endsWith("/health")) return { ok: true, json: async () => ({ real_endpoints: ["getCertifications", "getAlternatives"] }) };
  return { ok: true, status: 200, headers: { get: () => (url.includes("alternatives") ? "mock" : "real") }, json: async () => ({ checks: [] }) };
};
const { callOp, opsStatus, OPS } = await import(new URL("../ops.js", import.meta.url));

assert.deepStrictEqual(await callOp("history", { product_id: "P1" }), { live: false });
assert.ok(!calls.some((c) => c.includes("history")), "a not-live endpoint must not be called at all");
assert.deepStrictEqual(await callOp("certifications", { product_id: "P 1" }), { live: true, data: { checks: [] } });
assert.ok(calls.includes("GET /v1/products/P%201/certifications"), "ids must be URL-encoded");
await assert.rejects(() => callOp("alternatives", { product_id: "P1" }), /Demo data was rejected/);
await assert.rejects(() => callOp("nope"), /Unknown operation/);
const status = await opsStatus();
assert.strictEqual(status.length, Object.keys(OPS).length + 4, "the status board lists every endpoint");
console.log("ok  ops");
