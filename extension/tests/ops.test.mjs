// ops.js: an endpoint that is not live is never called, and an example (mock) answer is never treated as data.
import assert from "node:assert";
const calls = [];
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
assert.deepStrictEqual(await callOp("alternatives", { product_id: "P1" }), { live: false }, "an example answer must be rejected even if listed as live");
await assert.rejects(() => callOp("nope"), /Unknown operation/);
const status = await opsStatus();
assert.strictEqual(status.length, Object.keys(OPS).length + 4, "the status board lists every endpoint");
console.log("ok  ops");
