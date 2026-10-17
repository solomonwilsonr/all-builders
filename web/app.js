// SafeShelf judges' page. Plain modules, no build step, no keys: it calls the same API as the extension, signed in
// with Google (auth.js); nothing runs until the person signs in.
// Samples replay a saved run of the live API at real speed; "Run it live" streams a new one
// (POST /v1/agent/sessions/stream, server-sent events), capped per browser so the demo's Gemini budget lasts.
// The API (or ?api=http://localhost:PORT), and what a shopper can do with an answer: actions.js.
import { API, afterBlock, badgeEl, listenBlock, setListing, setUpAsk, setUpRedteam } from "./actions.js";
import { authFetch, requireSignIn } from "./auth.js";
import { renderPage, setAddress, startClock } from "./desk.js";

const LIVE_PER_DAY = 10;
const LONG_WAIT_MS = 3000; // in a replay, a wait longer than this is shortened to SHORT_WAIT_MS (and the page says so)
const SHORT_WAIT_MS = 1000;

const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role") e.setAttribute(k, v); // data-*, aria-*: attributes, not properties
    else e[k] = v;
  }
  e.append(...kids.filter((k) => k !== null && k !== undefined && k !== false));
  return e;
};
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// --- The agents of the Investigate pipeline, in the order a judge reads them ---
const AGENTS = [
  ["page_reader", "Page reader", "matches the listing to a product SafeShelf knows"],
  ["is_it_real", "Is it real?", "price, website age, copied photos, specs, hidden AI text"],
  ["safety_radar", "Safety Radar", "Gemini reads buyer reviews for fire, burn and shock"],
  ["recall_checker", "Recall checker", "official notices from 7 regulators; only the exact model counts"],
  ["cert_verifier", "Safety marks", "the BIS licence or energy rating against the registry"],
  ["twin_finder", "Twin finder", "the same hardware sold under other brand names"],
  ["verdict", "Verdict, set by code", "plain code turns the checks into colours"],
  ["verdict_writer", "Gemini writes the answer", "explains the verdict in plain words; it can't change it"],
];
const WORDS = { red: "⛔ Danger or not real", amber: "⚠️ Be careful: under review", green: "✅ Nothing found in what was checked", unknown: "❔ Not enough evidence yet" };
const SHORT = { red: "⛔ Red", amber: "⚠️ Amber", green: "✅ Green", unknown: "❔ Not enough evidence" };

// The light on each agent's row comes from what it reported.
function levelOf(agent, summary = "") {
  if (/^Skipped/.test(summary)) return "skipped";
  if (agent === "is_it_real") {
    if (/hidden AI/.test(summary)) return "red";
    const n = Number(summary.match(/(\d+) warning sign/)?.[1] || 0);
    return n >= 2 ? "red" : n === 1 ? "amber" : "done"; // "no warning signs" is not green: some checks may not have run
  }
  if (agent === "safety_radar") return /officially recalled/.test(summary) ? "red" : summary.match(/verdict (red|amber|green)\b/)?.[1] || "done";
  if (agent === "recall_checker") return /No recall/.test(summary) ? "green" : /linked recall/.test(summary) ? "amber" : "done";
  if (agent === "cert_verifier") return /mismatch/.test(summary) ? "amber" : /verified|valid/.test(summary) ? "green" : "done";
  if (agent === "verdict") return summary.match(/overall (red|amber|green)\b/)?.[1] || "done";
  return "done";
}
const readable = (s = "") => s.replace(/not_enough_evidence/g, "not enough evidence");

// --- Live runs left on this browser (the API also limits every caller and the whole day) ---
const quota = {
  key: "safeshelf-live-runs",
  today: () => new Date().toISOString().slice(0, 10),
  used() {
    try { const v = JSON.parse(localStorage.getItem(this.key) || "{}"); return v.day === this.today() ? v.used : 0; } catch (_) { return 0; }
  },
  take() { try { localStorage.setItem(this.key, JSON.stringify({ day: this.today(), used: this.used() + 1 })); } catch (_) { /* private mode: no cap kept */ } },
  left() { return Math.max(0, LIVE_PER_DAY - this.used()); },
};
const quotaText = () => (quota.left() ? `${quota.left()} live run${quota.left() === 1 ? "" : "s"} left today on this browser` : "Live runs used up on this browser today");
const refreshQuota = () => document.querySelectorAll("[data-quota]").forEach((q) => { q.textContent = quotaText(); });

// --- One run on screen: the agents light up as events arrive, then the verdict ---
let current = 0; // a newer run makes older ones stop drawing
function runView(box, { title, sub, expect, pill }) {
  const id = ++current;
  const alive = () => id === current;
  const rows = new Map();
  const list = el("ol", { className: "agents" });
  for (const [key, who, what] of AGENTS) {
    const said = el("div", { className: "said", textContent: what });
    const li = el("li", {}, el("span", { className: "dot", "aria-hidden": "true" }), el("div", {}, el("div", { className: "who", textContent: who }), said));
    rows.set(key, { li, said, who: li.querySelector(".who") });
    list.append(li);
  }
  const timer = el("span", { className: "timer", textContent: "0.0 s" });
  const out = el("div");
  box.replaceChildren(el("h2", { textContent: title }), el("p", { className: "sub", textContent: sub }),
    el("div", { className: "runbar" }, pill, timer), list, out);
  box.hidden = false;

  const step = (e) => {
    const row = rows.get(e.agent);
    if (!row) {
      if (e.tool === "cache") out.append(el("p", { className: "muted", textContent: `${e.summary}.` }));
      return;
    }
    const level = levelOf(e.agent, e.summary);
    row.li.className = level === "skipped" ? "skipped" : level;
    row.said.textContent = readable(e.summary) + (e.seconds ? ` · ${e.seconds} s` : "");
    row.who.querySelector(".model")?.remove();
    if (e.model) row.who.append(el("span", { className: "model", textContent: e.model }));
  };

  return {
    alive,
    clock(ms) { if (alive()) timer.textContent = `${(ms / 1000).toFixed(1)} s`; },
    event(e) {
      if (!alive()) return;
      if (e.type === "start") { const row = rows.get(e.agent); if (row && !row.li.className) row.li.className = "working"; }
      if (e.type === "step") step(e);
    },
    finish(result, extra) {
      if (!alive()) return;
      // A cached answer brings its steps only at the end: light up any row the stream didn't.
      for (const s of result.steps || []) if (rows.get(s.agent) && !/green|amber|red|done|skipped/.test(rows.get(s.agent).li.className)) step(s);
      for (const { li } of rows.values()) if (li.className === "working" || !li.className) li.className = "skipped";
      out.replaceChildren(...verdictBlock(result, expect), ...(extra ? [extra] : []));
    },
    fail(message) { if (alive()) out.replaceChildren(el("p", { className: "error", textContent: `SafeShelf could not finish: ${message}` })); },
  };
}

// Plan v2.2: the code's outcome, what was checked country by country, the official records, and what would change it.
const STATES = { checked_live: ["●", "notice found (live)"], checked_cache: ["●", "notice found (stored copy)"],
  no_matching_notice_found: ["○", "no matching notice"], source_unavailable: ["!", "couldn't be checked"], not_supported: ["–", "not checked"] };
const OUTCOMES = { confirmed_recall: "Confirmed recall in this country", substantiated_hazard_signal: "Substantiated hazard reports",
  potential_concern: "Potential concern", no_matching_notice_found: "No matching notice (not proof of safety)", insufficient_evidence: "Not enough evidence" };

// The answer in everyday words (engine/plain.py) leads; the country table and records stay under "Show details".
const MARKS = { ok: "✓", warn: "!", maybe: "?", skip: "–" };
function plainBlock(v) {
  const p = v.plain;
  if (!p) return null;
  return el("div", { className: "plain" },
    el("h3", { className: `ptitle ${p.tone}`, textContent: p.title }),
    el("p", { className: "pwhy", textContent: p.why }),
    el("div", { className: "ptodo" }, el("strong", { textContent: "What you can do" }), el("p", { textContent: p.todo }),
      ...(p.link?.url ? [el("a", { href: p.link.url, target: "_blank", rel: "noopener", textContent: p.link.label })] : [])),
    el("div", { className: "pplaces" }, el("strong", { textContent: "Where we checked official recall lists" }),
      el("ul", {}, ...(p.checked || []).map((c) => el("li", { className: c.mark },
        el("span", { className: "pm", textContent: MARKS[c.mark] || "–" }), `${c.flag} `,
        el("b", { textContent: `${c.name}${c.yours ? " (shopper's country)" : ""}: ` }), c.status, " ", badgeEl(c.badge))))),
    el("p", { className: "muted", textContent: p.note }));
}

function coverageBlock(v) {
  const countries = v.coverage?.countries || [];
  if (!v.outcome || !countries.length) return null;
  const rows = countries.slice(0, 8).map((c) => {
    const [mark, words] = STATES[c.state] || ["–", c.state];
    const how = (c.sources || []).filter((x) => x.state !== "not_supported").map((x) => x.authority).join(", ");
    return el("tr", { className: c.state }, el("td", { className: "mark", textContent: mark }),
      el("td", {}, el("strong", { textContent: c.name }), c.is_market ? " (shopper's country)" : ""),
      el("td", { textContent: words }), el("td", { className: "muted", textContent: how }));
  });
  const records = (v.matches || []).filter((m) => m.tier !== "lookalike" && /^https:/.test(m.url || "")).slice(0, 4).map((m) =>
    el("li", {}, el("a", { href: m.url, target: "_blank", rel: "noopener", textContent: `${m.authority} ${m.record_id}` }),
      ` · ${m.local ? "this country" : `another country (${m.jurisdiction})`} · ${m.tier.replace("_", " ")}, ${m.scope.replace(/_/g, " ")}`));
  const next = (v.what_would_change || []).slice(0, 3).map((w) => el("li", { textContent: `${w.fact} (${w.how})` }));
  const market = countries.find((c) => c.is_market);
  return el("details", { className: "coverage", open: true },
    el("summary", { textContent: `${OUTCOMES[v.outcome] || v.outcome}: what was checked${v.source_mode === "partial" ? " (some sources couldn't be read)" : ""}` }),
    el("p", { className: "headline", textContent: v.headline || "" }),
    el("table", {}, el("tbody", {}, ...rows)),
    ...(market?.notes?.length ? [el("p", { className: "muted", textContent: market.notes.join(" ") })] : []),
    ...(records.length ? [el("h4", { textContent: "Official records" }), el("ul", {}, ...records)] : []),
    ...(next.length ? [el("h4", { textContent: "What would change this answer" }), el("ul", {}, ...next)] : []),
    el("p", { className: "muted", textContent: `Set by code (policy ${v.policy_version || "?"}). A country with no matching notice is not an all-clear.` }));
}

function verdictBlock(result, expect) {
  const v = result.verdict || { safe: "unknown", real: "unknown", overall: "unknown", reasons: [] };
  const chip = (name, level) => el("div", { className: `chip ${level}` }, el("small", { textContent: name }), SHORT[level] || SHORT.unknown);
  const parts = [el("div", { className: "verdict" }, chip("Is it safe?", v.safe), chip("Is it real?", v.real), chip("Overall", v.overall))];
  if (expect) {
    const ok = expect.overall.includes(v.overall);
    parts.push(el("p", { className: `check ${ok ? "green" : "red"}`,
      textContent: ok ? `✓ Right answer. Expected: ${expect.label}` : `✗ Expected ${expect.label}, but got ${WORDS[v.overall] || WORDS.unknown}` }));
  }
  const text = result.messages?.[0]?.text;
  if (text) parts.push(el("p", { className: "answer", textContent: text }));
  if (v.reasons?.length) {
    parts.push(el("details", { open: true }, el("summary", { textContent: `Why: ${v.reasons.length} reason${v.reasons.length === 1 ? "" : "s"}, written by code` }),
      el("ul", { className: "reasons" }, ...v.reasons.map((r) => el("li", { textContent: r.text })))));
  }
  const plain = plainBlock(v);
  if (plain) parts.push(plain);
  parts.push(listenBlock(v.plain, v.headline || text || ""));
  const cov = coverageBlock(v);
  if (cov) { cov.open = !plain; cov.querySelector("summary").textContent = plain ? "Show details: sources, records and rules" : cov.querySelector("summary").textContent; parts.push(cov); }
  const ids = [...new Set([...(result.messages?.[0]?.evidence_ids || []), ...(v.evidence_ids || [])])];
  if (ids.length) {
    const box = el("div", { className: "evidence" });
    const btn = el("button", { type: "button", textContent: `Show the evidence (${ids.length} quote${ids.length === 1 ? "" : "s"})` });
    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "Reading the evidence…";
      try {
        const res = await authFetch(`${API}/v1/evidence?ids=${encodeURIComponent(ids.join(","))}`, { signal: AbortSignal.timeout(60000) });
        if (!res.ok) throw new Error(`the API answered ${res.status}`);
        const items = await res.json();
        box.replaceChildren(...(Array.isArray(items) ? items : items.items || []).map((e) => el("blockquote", {},
          `“${e.quote}”`, el("cite", {}, `${e.source || e.type} · ${e.date || ""} · ${e.evidence_id} `,
            /^https?:/.test(e.url || "") && !/\.test\/|demo\.safeshelf\.app/.test(e.url) ? el("a", { href: e.url, target: "_blank", rel: "noopener", textContent: "open source" }) : null))));
        btn.remove();
      } catch (err) { btn.disabled = false; btn.textContent = `Couldn't load the evidence (${err.message}). Try again`; }
    };
    parts.push(el("div", {}, btn, box));
  }
  parts.push(afterBlock(result));
  parts.push(el("p", { className: "label" }, `${result.steps?.length || 0} agent steps · investigation ${result.investigation_id || "?"} · `,
    result.investigation_id ? traceLink(result.investigation_id) : "",
    result.label ? ` · ${result.label}` : ""));
  return parts;
}

// The trace needs the sign-in too, so a plain link can't open it: fetch it, then show the JSON in a new tab.
function traceLink(id) {
  const a = el("a", { href: "#", textContent: "full trace (model, tool, time)" });
  a.onclick = async (e) => {
    e.preventDefault();
    const tab = window.open("", "_blank");
    try {
      const res = await authFetch(`${API}/v1/investigations/${encodeURIComponent(id)}/trace`, { signal: AbortSignal.timeout(60000) });
      if (!res.ok) throw new Error(`the API answered ${res.status}`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(await res.json(), null, 2)], { type: "application/json" }));
      if (tab) tab.location = url; else location.assign(url);
    } catch (err) {
      tab?.close();
      a.textContent = `couldn't open the trace (${err.message})`;
    }
  };
  return a;
}

// --- A saved run, replayed at the speed it really happened ---
async function replay(view, rec) {
  const events = rec.events;
  let last = 0;
  for (const e of events) {
    const gap = e._ms - last;
    await wait(gap > LONG_WAIT_MS ? SHORT_WAIT_MS : gap);
    last = e._ms;
    if (!view.alive()) return;
    view.clock(e._ms);
    if (e.type === "done") return e.result;
    view.event(e);
  }
  throw new Error("the saved run has no answer");
}

// --- A live run: the API's own event stream ---
async function live(view, request) {
  const started = performance.now();
  const tick = setInterval(() => view.clock(performance.now() - started), 100);
  try {
    const res = await authFetch(`${API}/v1/agent/sessions/stream`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request), signal: AbortSignal.timeout(170000) });
    if (!res.ok) {
      const detail = (await res.json().catch(() => ({}))).detail;
      throw new Error(typeof detail === "string" ? detail : `the API answered ${res.status}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let cut;
      while ((cut = buffer.indexOf("\n\n")) >= 0) {
        const data = buffer.slice(0, cut).split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5)).join("\n");
        buffer = buffer.slice(cut + 2);
        if (!data) continue;
        const event = JSON.parse(data);
        if (event.type === "done") return event.result;
        if (event.type === "error") throw new Error(event.detail || "the agents could not finish");
        view.event(event);
      }
    }
    throw new Error("the connection closed before the answer");
  } catch (err) {
    throw err.name === "TimeoutError" ? new Error("no answer within about 3 minutes; please try again") : err;
  } finally {
    clearInterval(tick);
    view.clock(performance.now() - started);
  }
}

function liveButton(onRun) {
  const btn = el("button", { type: "button", className: "primary" });
  const note = el("span", { className: "quota", "data-quota": "" });
  const draw = () => {
    btn.disabled = !quota.left();
    btn.textContent = quota.left() ? "Run it live with Gemini" : "Live runs used up today";
    note.textContent = quotaText();
  };
  draw();
  btn.onclick = () => { if (!quota.left()) return; quota.take(); refreshQuota(); onRun(); };
  return el("div", { className: "actions" }, btn, note);
}

// --- Try a sample ---
async function showSample(preset, button) {
  document.querySelectorAll(".samples button").forEach((b) => { b.setAttribute("aria-pressed", String(b === button)); b.setAttribute("aria-selected", String(b === button)); });
  const box = document.getElementById("run");
  setAddress(preset.request.listing.url);
  renderPage(document.getElementById("page"), { listing: preset.request.listing, preset, index: presetsAll.indexOf(preset), total: presetsAll.length });
  const sub = `${preset.what} · ${preset.market}`;
  let rec;
  try {
    rec = await (await fetch(`samples/${preset.id}.json`)).json();
    setListing(preset.request.listing);
  } catch (_) { box.replaceChildren(el("p", { className: "error", textContent: "This sample's saved run could not be loaded." })); return; }
  const runLive = () => {
    const view = runView(box, { title: preset.name, sub, expect: preset.expect, pill: el("span", { className: "pill live", textContent: "Live now · Gemini on Vertex AI" }) });
    live(view, preset.request).then((r) => view.finish(r, again())).catch((err) => view.fail(err.message));
  };
  const again = () => el("div", {}, el("p", { className: "muted", textContent: "Run it again for a fresh answer. The API reuses an answer for the same listing for 10 minutes, and says so." }), liveButton(runLive));
  const view = runView(box, { title: preset.name, sub, expect: preset.expect,
    pill: el("span", { className: "pill", textContent: `Saved run of the live API · ${rec.recorded_at} · waits over ${LONG_WAIT_MS / 1000} s shortened` }) });
  try {
    const result = await replay(view, rec);
    if (result) view.finish(result, el("div", {}, el("p", { className: "muted",
      textContent: `That run took ${(rec.events.at(-1)._ms / 1000).toFixed(1)} s on the live API. Now make Gemini do it again:` }), liveButton(runLive)));
  } catch (err) { view.fail(err.message); }
}

let presetsAll = [];
async function setUpSamples() {
  const { presets } = await (await fetch("samples/presets.json")).json();
  presetsAll = presets;
  const list = document.getElementById("samples");
  presets.forEach((p, i) => {
    // each sample is a tab of the browser window; its page is built from the sample's real listing
    const b = el("button", { type: "button", role: "tab", title: `${p.what} · Expected: ${p.expect.label}` },
      el("span", { className: "fav", "aria-hidden": "true", textContent: p.control ? "✓" : String(i + 1) }),
      el("span", { className: "name", textContent: p.name }),
      el("span", { className: "x", "aria-hidden": "true", textContent: "×" }));
    b.setAttribute("aria-pressed", "false");
    b.setAttribute("aria-selected", "false");
    b.onclick = () => showSample(p, b);
    list.append(el("li", { role: "presentation" }, b));
  });
  list.querySelector("button")?.click();
}

// The address bar: a link typed here is checked live, the same as "Check your own listing"
function setUpOmnibox() {
  const form = document.getElementById("omnibox");
  if (!form) return;
  const ext = document.getElementById("ext-toggle");
  ext?.addEventListener("click", () => {
    const run = document.getElementById("run");
    run.hidden = !run.hidden;
    ext.classList.toggle("on", !run.hidden);
    ext.setAttribute("aria-pressed", String(!run.hidden));
  });
  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const raw = document.getElementById("omni-url").value.trim();
    if (!raw) return;
    const url = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
    const box = document.getElementById("run");
    if (!quota.left()) { box.replaceChildren(el("p", { className: "error", textContent: "Live runs are used up on this browser today. The sample tabs still replay real runs." })); return; }
    document.querySelectorAll(".samples button").forEach((b) => { b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-selected", "false"); });
    const listing = { url };
    setListing(listing);
    setAddress(url);
    renderPage(document.getElementById("page"), { listing });
    quota.take();
    refreshQuota();
    const view = runView(box, { title: "Your link", sub: url, pill: el("span", { className: "pill live", textContent: "Live now · Gemini on Vertex AI" }) });
    live(view, { mode: "investigate", product_id: "unmatched", listing }).then((r) => view.finish(r)).catch((err) => view.fail(err.message));
  });
}

// --- Check your own listing ---
function setUpOwn() {
  const form = document.getElementById("own");
  const box = document.getElementById("own-run");
  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    if (!quota.left()) { box.hidden = false; box.replaceChildren(el("p", { className: "error", textContent: "Live runs are used up on this browser today. The samples still replay real runs." })); return; }
    const f = new FormData(form);
    const listing = {};
    for (const k of ["title", "url", "seller", "page_text", "currency"]) if (String(f.get(k) || "").trim()) listing[k] = String(f.get(k)).trim();
    if (String(f.get("price") || "").trim()) listing.price = Number(f.get("price"));
    setListing(listing);
    quota.take();
    refreshQuota();
    const view = runView(box, { title: listing.title, sub: listing.url || "No link given",
      pill: el("span", { className: "pill live", textContent: "Live now · Gemini on Vertex AI" }) });
    box.scrollIntoView({ behavior: "smooth", block: "start" });
    live(view, { mode: "investigate", product_id: "unmatched", listing }).then((r) => view.finish(r)).catch((err) => view.fail(err.message));
  });
}

// --- SafeShelf vs Gemini alone (the backtest) ---
const frac = (s) => { const [a, b] = String(s).split("/").map(Number); return { a, b }; };
function bars(rows, total, unit) {
  return el("div", { className: "bars" }, ...rows.map((r) => {
    const tip = el("span", { className: "tip", role: "tooltip", textContent: r.tip });
    return el("div", { className: `bar-row${r.us ? " us" : ""}`, tabIndex: 0, "aria-label": r.tip },
      el("span", { className: "who", textContent: r.name }),
      el("span", { className: "track" }, Object.assign(el("span", { className: "fill" }), { style: `display:block;width:${(100 * r.n) / total}%` })),
      el("span", { className: "val", textContent: `${r.n} of ${total}${unit ? ` (${Math.round((100 * r.n) / total)}%)` : ""}` }), tip);
  }));
}
async function setUpVs() {
  const box = document.getElementById("vs");
  let bench, agents, catalog;
  try {
    [bench, agents, catalog] = await Promise.all(["bench", "agent_eval", "catalog"].map((n) => fetch(`data/${n}.json`).then((r) => r.json())));
  } catch (_) { box.replaceChildren(el("p", { className: "error", textContent: "The results could not be loaded." })); return; }
  const t = bench.tasks.early_warning;
  const methods = [
    ["Keyword rules", t.keyword_rules], ["Gemini alone", t.gemini_alone], ["SafeShelf", t.safeshelf, true],
  ];
  const caught = methods.map(([name, m, us]) => ({ name, us, n: frac(m.recalls_flagged).a,
    tip: `${name}: warned on ${m.recalls_flagged} recalled products before their recall; median ${Math.round(m.median_lead_weeks)} weeks early` }));
  const alarms = methods.map(([name, m, us]) => ({ name, us, n: frac(m.false_alarms).a,
    tip: `${name}: raised an alarm on ${m.false_alarms} products that were never recalled (${Math.round(100 * m.false_alarm_rate)}%)` }));
  const test = bench.safeshelf_on_test_half;
  const weeks = (d) => (d == null ? "–" : `${Math.round(d / 7)} wk`);
  const reviews = bench.per_recall.reduce((s, r) => s + r.reviews_before_recall, 0);

  box.replaceChildren(
    el("h2", { className: "vs-head", textContent: "Could the reviews have warned buyers before the recall?" }),
    el("p", { className: "muted", textContent: `Backtest on 25 real CPSC recalls of products sold on Amazon, using the ${reviews.toLocaleString("en-IN")} reviews written before each recall, plus 40 products from the same brands that were never recalled. Each method read the same reviews.` }),
    el("div", { className: "headline card" }, el("b", { textContent: "Same early catches as Gemini alone, with a third of the false alarms." }),
      el("br"), `SafeShelf flagged ${t.safeshelf.recalls_flagged} recalls early, like Gemini alone, but cried wolf on ${t.safeshelf.false_alarms} safe products instead of ${t.gemini_alone.false_alarms}. Keyword rules catch more but raise false alarms on more than a quarter of safe products.`),
    el("div", { className: "vs-grid" },
      el("div", { className: "vs-card card" }, el("h3", { textContent: "Recalls flagged before the recall" }), el("p", { className: "muted", textContent: "Higher is better" }), bars(caught, 25, false)),
      el("div", { className: "vs-card card" }, el("h3", { textContent: "False alarms on products never recalled" }), el("p", { className: "muted", textContent: "Lower is better" }), bars(alarms, 40, true))),
    el("div", { className: "vs-grid" },
      el("div", { className: "vs-card card" }, el("h3", { textContent: "Why it's quieter: reviews pooled across copies" }),
        el("p", { textContent: `SafeShelf groups the same hardware sold under different brand names and reads all their reviews together. Without that pooling it caught ${t.safeshelf_no_pooling.recalls_flagged}; with it, ${t.safeshelf.recalls_flagged}. Gemini still reads every review; code decides when the reports add up to an alarm (at least ${bench.safeshelf_params.k} independent reports).` })),
      el("div", { className: "vs-card card" }, el("h3", { textContent: "Held-out half, never used for tuning" }),
        el("p", { textContent: `SafeShelf's alarm settings were tuned on half the recalls. On the other half it flagged ${test.recalls_flagged} recalls early with ${test.false_alarms} false alarms (${Math.round(100 * test.false_alarm_rate)}%).` }))),
    el("div", { className: "table-wrap card", style: "padding:14px 18px" },
      el("table", { className: "vs-table" },
        el("caption", { className: "muted", style: "text-align:left;padding-bottom:6px", textContent: "All methods, as a table" }),
        el("thead", {}, el("tr", {}, ...["Method", "Recalls flagged early", "False alarms", "Median warning"].map((h, i) => el("th", { className: i ? "n" : "", textContent: h })))),
        el("tbody", {}, ...[...methods, ["SafeShelf without pooling", t.safeshelf_no_pooling]].map(([name, m]) => el("tr", {},
          el("td", { textContent: name }), el("td", { className: "n", textContent: m.recalls_flagged }),
          el("td", { className: "n", textContent: `${m.false_alarms} (${Math.round(100 * m.false_alarm_rate)}%)` }),
          el("td", { className: "n", textContent: `${Math.round(m.median_lead_weeks)} weeks before` })))))),
    el("details", { className: "card" }, el("summary", { textContent: "Every recall in the backtest" }),
      el("div", { className: "table-wrap" }, el("table", { className: "vs-table" },
        el("thead", {}, el("tr", {}, ...["Recall", "Date", "Reviews before", "Keyword rules", "Gemini alone", "SafeShelf"].map((h, i) => el("th", { className: i > 1 ? "n" : "", textContent: h })))),
        el("tbody", {}, ...bench.per_recall.map((r) => el("tr", {},
          el("td", { textContent: r.title.replace(/ \(Recall Alert\)$/, "") }), el("td", { textContent: r.recall_date }),
          el("td", { className: "n", textContent: r.reviews_before_recall.toLocaleString("en-IN") }),
          el("td", { className: "n", textContent: weeks(r.keyword_rules_lead_days) }), el("td", { className: "n", textContent: weeks(r.gemini_alone_lead_days) }),
          el("td", { className: "n", textContent: weeks(r.safeshelf_lead_days) }))))))),
    el("details", { className: "card" }, el("summary", { textContent: "Other measured results" }),
      el("ul", { className: "caveats" },
        el("li", { textContent: `Agent test set: ${agents.passed}/${agents.cases} cases and ${agents.checks_passed}/${agents.checks} checks pass on the live API (${agents.run_at}). Investigate answers in a median ${agents.speed.investigate.median_s} s.` }),
        el("li", { textContent: `Catalog Scan for marketplaces: precision ${catalog.precision.toFixed(2)}, recall ${catalog.recall.toFixed(2)} on ${catalog.rows} listings with ${catalog.expected_findings} planted problems; ${catalog.unexpected_findings.length} unexpected findings.` }),
        el("li", { textContent: "Safety Radar: 20/20 on hand-labelled reviews, including traps like “this charger is fire 🔥”." }))),
    el("details", { className: "card" }, el("summary", { textContent: "Limits, stated plainly" }),
      el("ul", { className: "caveats" }, ...bench.caveats.map((c) => el("li", { textContent: c })),
        el("li", { textContent: "Gemini alone warned a little earlier on median (104 vs 93 weeks) on the recalls both caught." }))),
  );
}

// --- Tabs ---
function setUpTabs() {
  const tabs = [...document.querySelectorAll("[role=tab]")];
  const pick = (tab) => {
    for (const t of tabs) {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    }
    try { history.replaceState(null, "", `#${tab.id.replace("tab-", "")}`); } catch (_) { /* file:// */ }
  };
  tabs.forEach((t, i) => {
    t.onclick = () => pick(t);
    t.onkeydown = (e) => {
      const next = e.key === "ArrowRight" ? tabs[(i + 1) % tabs.length] : e.key === "ArrowLeft" ? tabs[(i - 1 + tabs.length) % tabs.length] : null;
      if (next) { pick(next); next.focus(); }
    };
  });
  const start = tabs.find((t) => t.id === `tab-${location.hash.slice(1)}`);
  if (start) pick(start);
}

await requireSignIn();
startClock();
setUpTabs();
setUpOmnibox();
setUpOwn();
refreshQuota();
setUpSamples();
setUpVs();
setUpAsk();
setUpRedteam(() => { if (!quota.left()) return false; quota.take(); refreshQuota(); return true; });
