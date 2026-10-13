// Every SafeShelf API operation the extension can call, behind one door.
// An operation is only called when the API's /health says it is live (has a real handler). Otherwise nothing is
// called and nothing is shown: the example answers the API gives for unfinished endpoints must never reach a screen.
import { API_BASE } from "./config.js";
import { api } from "./check.js";

export const OPS = {
  product: { id: "getProduct", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}` },
  safety: { id: "getSafety", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}/safety` },
  relationships: { id: "getRelationships", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}/relationships` },
  history: { id: "getHistory", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}/history` },
  certifications: { id: "getCertifications", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}/certifications` },
  alternatives: { id: "getAlternatives", method: "GET", path: (a) => `/v1/products/${enc(a.product_id)}/alternatives` },
  identify: { id: "identifyProduct", method: "POST", path: () => "/v1/products/identify", body: (a) => a.listing },
  duplicates: { id: "findDuplicates", method: "POST", path: () => "/v1/products/duplicates", body: (a) => ({ product_id: a.product_id, refresh: !!a.refresh }) },
  report: { id: "createReport", method: "POST", path: () => "/v1/reports", body: (a) => ({ product_id: a.product_id, description: a.description, photo_urls: a.photo_urls || [] }) },
  catalogScan: { id: "catalogScan", method: "POST", path: () => "/v1/catalog/scan", body: (a) => ({ csv_url: a.csv_url }) },
  trace: { id: "getTrace", method: "GET", path: (a) => `/v1/investigations/${enc(a.investigation_id)}/trace` },
  bench: { id: "getBenchResults", method: "GET", path: () => "/v1/bench/results" },
};
const enc = (v) => encodeURIComponent(String(v ?? ""));

// The operations with a real handler, from GET /health. Free to ask; remembered for 5 minutes.
let liveCache = null;
export async function liveOps(force = false) {
  if (!force && liveCache && Date.now() - liveCache.at < 5 * 60 * 1000) return liveCache.ids;
  const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(15000) });
  if (!res.ok) throw new Error(`/health answered ${res.status}`);
  const ids = new Set((await res.json()).real_endpoints || []);
  liveCache = { at: Date.now(), ids };
  return ids;
}

export async function callOp(op, args = {}) {
  const def = OPS[op];
  if (!def) throw new Error(`Unknown operation ${op}`);
  const live = await liveOps();
  if (!live.has(def.id)) return { live: false };
  const { body, source } = await api(def.path(args), def.method === "GET" ? {} : { method: def.method, body: JSON.stringify(def.body(args)) });
  if (source === "mock") return { live: false }; // belt and braces: a mock answer is never data
  return { live: true, data: body };
}

// Operations the extension calls directly (not through callOp), listed so the status board shows all of them.
const DIRECT = [
  { op: "trustCheck", id: "trustCheck", method: "POST", path: "/v1/listings/trust-check" },
  { op: "addShelfItem", id: "addShelfItem", method: "POST", path: "/v1/shelf/items" },
  { op: "startAgentSession", id: "startAgentSession", method: "POST", path: "/v1/agent/sessions" },
  { op: "getEvidence", id: "getEvidence", method: "GET", path: "/v1/evidence" },
];
// For the status board: every operation with whether it is live.
export async function opsStatus() {
  const live = await liveOps(true);
  const all = Object.entries(OPS).map(([op, d]) => ({ op, id: d.id, method: d.method, path: d.path({ product_id: "{product_id}", investigation_id: "{id}" }) }));
  return [...DIRECT, ...all].map((x) => ({ ...x, live: live.has(x.id) }));
}
