// A stand-in SafeShelf API for filming the real extension: it serves the page and the extension files, answers the
// streaming check by replaying a recorded run (web/samples/<id>.json) at its recorded pace, and answers the other
// endpoints from contracts/mock. No sign-in, no network, no Gemini credit.
// --record sends every API call to the live API once and saves the answers in recorded/<sample>/; after that the stub
// replays those real answers first (then the recorded stream, then contracts/mock).
// --delay holds each replayed answer that many ms, so the widget's "Checking" state can be filmed.
//   node stub-api.mjs [--sample recall_jp] [--port 8787] [--slow 1] [--delay 0] [--record]
import http from "node:http";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const arg = (n, f) => { const i = process.argv.indexOf(`--${n}`); return i > 0 ? process.argv[i + 1] : f; };
const sample = arg("sample", "recall_jp"), port = Number(arg("port", 8787)), slow = Number(arg("slow", 1)), delay = Number(arg("delay", 0));
const LIVE = "https://safeshelf-api-368488022657.asia-south1.run.app", record = process.argv.includes("--record");
const recDir = join(here, "recorded", sample);
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".jpg": "image/jpeg" };
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "GET,POST,OPTIONS" };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = [], misses = [];

async function file(res, path) {
  if (!existsSync(path)) { res.writeHead(404, cors).end(); return; }
  res.writeHead(200, { ...cors, "Content-Type": TYPES[extname(path)] || "application/octet-stream", "Cache-Control": "no-store" });
  res.end(await readFile(path));
}
const json = (res, code, body) => res.writeHead(code, { ...cors, "Content-Type": "application/json" }).end(JSON.stringify(body));

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`), p = url.pathname;
  if (req.method === "OPTIONS") return res.writeHead(204, cors).end();
  if (p.startsWith("/v1/") || p === "/health") log.push(`${req.method} ${p}`), console.log(`api ${req.method} ${p}`);
  if (p === "/_log") return json(res, 200, log);
  if (p === "/_misses") return json(res, 200, misses);
  if (p === "/health") return json(res, 200, { ok: true });
  if (p.startsWith("/v1/")) {
    const body = req.method === "POST" ? await new Promise((ok) => { let b = ""; req.on("data", (c) => (b += c)); req.on("end", () => ok(b)); }) : "";
    const key = `${req.method}_${p.slice(4).replace(/[^a-z0-9]+/gi, "_")}_${createHash("sha1").update(stable(body)).digest("hex").slice(0, 8)}`;
    const saved = join(recDir, `${key}.json`);
    if (record) return relay(req, res, p + url.search, body, saved);
    if (existsSync(saved)) {
      const r = JSON.parse(await readFile(saved, "utf8"));
      if (r.sse) return replaySSE(res, r.sse);
      await sleep(delay);
      return json(res, r.status, r.body);
    }
    // a sample that was recorded must be filmed from its recording only: a mock answer here would put made-up
    // content on screen, so it is logged and film.mjs refuses to save the stills
    if (existsSync(recDir)) { misses.push(`${req.method} ${p}`); console.log(`  MISS ${key} (not recorded; answering from the mock)`); }
    req.body = body;
  }
  if (p === "/v1/agent/sessions/stream") {  // no recorded answer: the judges' page recording
    const { events } = JSON.parse(await readFile(join(root, "web/samples", `${sample}.json`), "utf8"));
    res.writeHead(200, { ...cors, "Content-Type": "text/event-stream", "Cache-Control": "no-store" });
    let last = 0;
    for (const e of events) {
      await sleep(Math.max(0, (e._ms - last) * slow)); last = e._ms;
      const { _ms, ...ev } = e;
      res.write(`data: ${JSON.stringify(ev)}\n\n`);
    }
    return res.end();
  }
  if (p.startsWith("/v1/")) {
    // contracts/mock/<last-path-part>.json when there is one, else an empty answer the widget treats as "nothing found"
    const name = p.split("/").filter(Boolean).slice(-1)[0].replace(/-/g, "_");
    const mock = join(root, "contracts/mock", `${name}.json`);
    if (existsSync(mock)) return json(res, 200, JSON.parse(await readFile(mock, "utf8")));
    return json(res, 404, { detail: "not in the stub" });
  }
  if (p.startsWith("/ext/")) return file(res, join(root, "web", p));
  if (p.startsWith("/assets/")) return file(res, join(root, "web/site", p));
  return file(res, join(here, p === "/" ? "amazon.html" : p));
}).listen(port, () => console.log(`stub API and pages on http://localhost:${port} (sample ${sample})`));

// The same request body twice gets the same file, whatever order its keys were written in (session ids aside).
function stable(body) {
  try {
    const o = JSON.parse(body);
    const walk = (v) => Array.isArray(v) ? v.map(walk) : v && typeof v === "object"
      ? Object.fromEntries(Object.keys(v).sort().filter((k) => !/session_id|request_id|nonce/.test(k)).map((k) => [k, walk(v[k])])) : v;
    return JSON.stringify(walk(o));
  } catch { return body; }
}

async function relay(req, res, path, body, saved) {
  await mkdir(recDir, { recursive: true });
  const up = await fetch(LIVE + path, { method: req.method, headers: { "Content-Type": "application/json" }, body: req.method === "POST" ? body : undefined });
  const type = up.headers.get("content-type") || "";
  console.log(`  live ${up.status} ${path}`);
  if (type.includes("event-stream")) {
    res.writeHead(up.status, { ...cors, "Content-Type": "text/event-stream" });
    const sse = [], t0 = Date.now(), dec = new TextDecoder();
    for await (const chunk of up.body) { const text = dec.decode(chunk, { stream: true }); sse.push([Date.now() - t0, text]); res.write(text); }
    res.end();
    return writeFile(saved, JSON.stringify({ sse }));
  }
  const text = await up.text();
  let parsed; try { parsed = JSON.parse(text); } catch { parsed = text; }
  res.writeHead(up.status, { ...cors, "Content-Type": "application/json" }).end(text);
  return writeFile(saved, JSON.stringify({ status: up.status, body: parsed }, null, 1));
}

async function replaySSE(res, sse) {
  res.writeHead(200, { ...cors, "Content-Type": "text/event-stream" });
  let last = 0;
  for (const [ms, text] of sse) { await sleep(Math.max(0, (ms - last) * slow)); last = ms; res.write(text); }
  res.end();
}
