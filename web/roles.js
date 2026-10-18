// "Who are you?": one check, shown four ways. The same product (the HAIARA W5PRO power bank, recalled in Japan) runs
// through every view, so a judge sees one engine serving a shopper, a marketplace analyst, a regulator and a developer.
// Everything here is drawn from what the API really returned (samples/*.json, data/catalog.json); the developer view
// also calls the live API. The chosen view is kept in the address (?for=marketplace, or #for=…) and on this browser.
// Plain module, no build step. Text is always set as text, never as HTML.
import { API, el } from "./actions.js?v=20261017v";
import { authFetch, quota } from "./auth.js?v=20261018u";

const STORY = "recall_jp"; // the sample every view tells
const KEY = "safeshelf-view";
// Eddy, the mascot, in each person's pose (site/assets/eddy-<view>.png)
const VIEWS = [
  { id: "shopper", label: "Shopper", who: "Rahul, about to buy a power bank", ask: "Is it safe to buy?" },
  { id: "marketplace", label: "Marketplace or seller", who: "Anjali, trust and safety at a marketplace", ask: "Which listings need action first?" },
  { id: "regulator", label: "Regulator or researcher", who: "A product-safety officer at the ACCC or BIS", ask: "What is the evidence, and where is it from?" },
  { id: "developer", label: "Developer or AI agent", who: "A shopping app or a Gemini buying agent", ask: "Can my agent ask the same thing?" },
];
const TONE = { red: "red", amber: "amber", green: "green", unknown: "grey" };
const WORD = { red: "Don't buy", amber: "Be careful", green: "No problems found", unknown: "Can't tell yet" };
const RANK = { red: 0, amber: 1, unknown: 2, green: 3 };
const STATE = { checked_live: "Notice found (read live)", checked_cache: "Notice found (stored copy)", no_matching_notice_found: "No matching notice",
  source_unavailable: "Couldn't be checked", not_supported: "Not checked" };
const AGENT = { page_reader: "Page reader", twin_finder: "Twin finder", recall_checker: "Recall checker", cert_verifier: "Safety marks",
  research_agent: "Research agent", safety_radar: "Safety Radar", is_it_real: "Is it real?", official_sources: "Official sources",
  verdict: "Verdict, set by code", verdict_writer: "Gemini writes the answer" };

const resultOf = (sample) => sample.events.find((e) => e.type === "done")?.result;
const money = (n, cur) => { try { return new Intl.NumberFormat("en", { style: "currency", currency: cur, maximumFractionDigits: 0 }).format(n); } catch (_) { return `${cur} ${n}`; } };
const pct = (x) => `${Math.round(100 * x)}%`;
const getJSON = (path) => fetch(path).then((r) => { if (!r.ok) throw new Error(path); return r.json(); });

// --- Shared data, loaded once ---
let presets = [];
let story = null; // { preset, result }
const samples = new Map();
let stopLeft = null; // the developer view's "checks left" line, redrawn when the quota changes
const recorded = (id) => getJSON(`samples/${id}.json`);
async function sample(id) {
  if (!samples.has(id)) samples.set(id, recorded(id).then(resultOf));
  return samples.get(id);
}

// --- Small building blocks ---
function copyBtn(label, text) {
  const b = el("button", { type: "button", className: "small", textContent: label });
  b.onclick = async () => {
    try { await navigator.clipboard.writeText(typeof text === "function" ? text() : text); b.textContent = "Copied"; }
    catch (_) { b.textContent = "Couldn't copy"; }
    setTimeout(() => { b.textContent = label; }, 1600);
  };
  return b;
}
function download(name, data) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const a = el("a", { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const step = (n, title, ...body) => el("li", { className: "fv-step" }, el("span", { className: "fv-n", textContent: String(n) }),
  el("div", { className: "fv-body" }, el("h4", { textContent: title }), ...body));
const next = (...links) => el("div", { className: "fv-next" }, el("span", { textContent: "Next" }), ...links);
const go = (href, text, line = true) => el("a", { className: `jbtn${line ? " line" : ""}`, href, textContent: text });
const recordLink = (r) => el("a", { href: r.url, target: "_blank", rel: "noopener", textContent: `Read the official ${r.authority} notice` });

// Open the demo browser on the story's tab (test pages, not the real browser, so it opens at once)
function openStory() {
  document.getElementById("tab-shop-page")?.click();
  const panel = document.getElementById("shop-page");
  if (panel?.dataset.mode === "choose") document.getElementById("test-start")?.click();
  const pickTab = (tries = 0) => {
    const tab = [...document.querySelectorAll("#samples button")].find((b) => b.title.startsWith(story.preset.what) || b.textContent.includes(story.preset.name));
    if (tab) tab.click();
    else if (tries < 20) setTimeout(() => pickTab(tries + 1), 150); // the tabs are still loading
  };
  pickTab();
  document.querySelector(".mac")?.scrollIntoView({ behavior: "smooth", block: "start" });
}
const openTab = (id) => () => { document.getElementById(`tab-${id}`)?.click(); document.getElementById("try")?.scrollIntoView({ behavior: "smooth", block: "start" }); };

// The answer the shopper sees, in brief
function answerCard(v) {
  const r = v.lead_record;
  return el("div", { className: `fv-answer ${TONE[v.overall]}` },
    el("b", { textContent: `${WORD[v.overall]}: ${v.headline.split(":")[0]}` }),
    el("p", { textContent: v.reasons[0]?.text || v.headline }),
    el("p", { className: "muted", textContent: "What to do: don't buy it. If you already have one, stop using it and ask the seller for a refund." }),
    r ? recordLink(r) : null);
}

// Country by country: what was found, and from which official sources
const covTable = (countries) => el("div", { className: "table-wrap" }, el("table", { className: "fv-queue fv-cov" },
  el("thead", {}, el("tr", {}, ...["Country", "Result", "Sources"].map((h) => el("th", { textContent: h })))),
  el("tbody", {}, ...countries.map((c) => el("tr", { className: c.matched ? "hit" : "" },
    el("td", { textContent: c.name.replace(/^the /, "") + (c.is_market ? " · shop's country" : "") }),
    el("td", { textContent: STATE[c.state] || c.state }),
    el("td", { textContent: c.sources.filter((s) => s.state !== "not_supported").map((s) => `${s.authority}${s.mode === "live" ? " (live)" : ""}`).join(", ") || "–" }))))));

// --- The four views ---
const BUILD = {
  shopper() {
    const v = story.result.verdict;
    return [
      el("ol", { className: "fv-steps" },
        step(1, "Open the listing", el("p", { textContent: "Rahul is about to buy this power bank. With the SafeShelf extension, a Check button sits on the page's right edge." }),
          el("button", { type: "button", className: "primary small", textContent: "Open it in the demo browser", onclick: openStory })),
        step(2, "Read one plain answer", answerCard(v)),
        step(3, "Already bought one?", el("p", { textContent: "Save it to My Shelf for recall alerts, get a refund request and complaint drafts, or ask by voice in 26 languages." }),
          el("div", { className: "fv-btns" }, go("site/chat.html", "Ask Eddy about it"),
            el("button", { type: "button", className: "small", textContent: "Ask out loud", onclick: openTab("ask-out-loud") })))),
      next(go("site/get.html", "Get SafeShelf", false), go("#check-own", "Check your own listing"), go("site/chat.html", "Open the chat")),
    ];
  },

  async marketplace() {
    let catalog = null;
    try { catalog = await getJSON("data/catalog.json"); } catch (_) { /* the stats card says so */ }
    const rows = (await Promise.all(presets.map(async (p) => {
      try { return { p, r: await sample(p.id) }; } catch (_) { return null; }
    }))).filter((x) => x?.r).sort((a, b) => RANK[a.r.verdict.overall] - RANK[b.r.verdict.overall]);

    const pack = el("div", { className: "fv-pack" });
    const showPack = ({ p, r }) => {
      const v = r.verdict;
      const found = (v.coverage?.countries || []).filter((c) => c.matched).map((c) => c.name);
      pack.replaceChildren(
        el("div", { className: "fv-packhead" }, el("span", { className: `fv-chip ${TONE[v.overall]}`, textContent: WORD[v.overall] }), el("b", { textContent: p.name })),
        el("dl", { className: "fv-dl" },
          el("dt", { textContent: "Case" }), el("dd", { textContent: r.investigation_id }),
          el("dt", { textContent: "Finding" }), el("dd", { textContent: v.headline }),
          el("dt", { textContent: "Evidence" }), el("dd", { textContent: `${v.evidence_strength || "–"} evidence · identity ${v.identity_confidence || "not matched"}` }),
          el("dt", { textContent: "Notices found" }), el("dd", { textContent: found.length ? found.join(", ") : "None in the sources checked" })),
        v.lead_record ? recordLink(v.lead_record) : null,
        el("div", { className: "fv-btns" },
          el("button", { type: "button", className: "primary small", textContent: "Download evidence pack", onclick: () => download(`safeshelf-${r.investigation_id}.json`, r) }),
          copyBtn("Copy note to the seller", () => `SafeShelf case ${r.investigation_id}: ${p.name}. ${v.headline}. ${v.reasons.map((x) => x.text).join(" ")}`)));
    };

    const queue = el("table", { className: "fv-queue" },
      el("thead", {}, el("tr", {}, ...["Priority", "Listing", "Finding", "Case"].map((h) => el("th", { textContent: h })))),
      el("tbody", {}, ...rows.map((row, i) => {
        const tr = el("tr", { tabIndex: 0, "aria-label": `Open the evidence pack for ${row.p.name}` },
          el("td", {}, el("span", { className: `fv-chip ${TONE[row.r.verdict.overall]}`, textContent: WORD[row.r.verdict.overall] })),
          el("td", {}, el("b", { textContent: row.p.name }), el("small", { textContent: row.p.market })),
          el("td", { textContent: row.r.verdict.headline.replace(/ \((this is )?not [^)]*\)$/, "") }),
          el("td", { className: "mono", textContent: row.r.investigation_id }));
        const pick = () => { queue.querySelectorAll("tr").forEach((t) => t.removeAttribute("aria-current")); tr.setAttribute("aria-current", "true"); showPack(row); };
        tr.onclick = pick;
        tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } };
        if (i === 0) setTimeout(pick);
        return tr;
      })));

    return [
      el("ol", { className: "fv-steps fv-queue-layout" },
        step(1, "Scan the whole catalog", catalog
          ? el("div", { className: "fv-stats" },
            el("div", {}, el("b", { textContent: catalog.rows.toLocaleString("en-IN") }), "listings scanned"),
            el("div", {}, el("b", { textContent: String(catalog.findings) }), "need attention"),
            el("div", {}, el("b", { textContent: pct(catalog.precision) }), "of flags were right"),
            el("div", {}, el("b", { textContent: pct(catalog.recall) }), "of planted problems found"))
          : el("p", { className: "muted", textContent: "The catalog results could not be loaded." }),
        catalog ? el("p", { className: "muted", textContent: `${catalog.summary}. Test catalog with ${catalog.expected_findings} planted problems.` }) : null),
        step(2, "Work the queue, worst first", el("p", { className: "muted", textContent: "Seven listings SafeShelf checked, ranked by the colour code set. Pick a row." }),
          el("div", { className: "table-wrap" }, queue)),
        step(3, "Send the evidence pack", pack)),
      next(go("#check-own", "Check a seller's listing", false), go("site/agents.html", "Connect your catalog"), go("site/get.html", "Talk to us")),
    ];
  },

  regulator() {
    const r = story.result;
    const v = r.verdict;
    const rec = v.lead_record;
    const countries = v.coverage?.countries || [];
    const steps = (r.steps || []).filter((s) => AGENT[s.agent]);
    const total = steps.reduce((t, s) => t + (s.seconds || 0), 0);
    return [
      el("ol", { className: "fv-steps" },
        step(1, "The official record", el("dl", { className: "fv-dl" },
          el("dt", { textContent: "Authority" }), el("dd", { textContent: `${rec.authority} (${rec.jurisdiction})` }),
          el("dt", { textContent: "Notice" }), el("dd", { textContent: rec.title }),
          el("dt", { textContent: "Record" }), el("dd", { className: "mono", textContent: rec.record_id }),
          el("dt", { textContent: "Published" }), el("dd", { textContent: rec.published }),
          el("dt", { textContent: "Match" }), el("dd", { textContent: `Exact model (${v.identity_confidence}); a look-alike's recall is never applied` })),
        recordLink(rec)),
        step(2, "Where it was checked", covTable(countries.filter((c) => c.matched || c.is_market)),
          el("details", { className: "fv-more" }, el("summary", { textContent: `${countries.filter((c) => !c.matched && !c.is_market).length} more countries checked` }),
            covTable(countries.filter((c) => !c.matched && !c.is_market)))),
        step(3, "How the answer was reached", el("ol", { className: "fv-trace" }, ...steps.map((s) => el("li", { className: /^Skipped/.test(s.summary) ? "fv-skipped" : "" },
          el("b", { textContent: AGENT[s.agent] }), el("span", { textContent: s.summary.replace(/not_enough_evidence/g, "not enough evidence") }),
          el("small", { textContent: [s.model, s.seconds != null ? `${s.seconds} s` : null].filter(Boolean).join(" · ") })))),
        el("p", { className: "muted", textContent: `Case ${r.investigation_id}, ${steps.length} steps, ${total.toFixed(1)} s of work. Code set the colour; Gemini only wrote the words.` }),
        el("div", { className: "fv-btns" }, el("button", { type: "button", className: "small", textContent: "Download the full trace", onclick: () => download(`safeshelf-trace-${r.investigation_id}.json`, r) })))),
      next(go("#accuracy", "Is it accurate?", false), go("#attack", "Can it be fooled?"), go("site/results.html", "All results")),
    ];
  },

  // An API playground: request on the left, response on the right, one Send button. REST runs here (a recorded
  // real response, or live on Cloud Run); A2A fetches the real agent card; MCP needs a key, so it gives the config.
  async developer() {
    const rec = await recorded(STORY).catch(() => null);
    const base = story.preset.request.listing;
    const caseId = rec?.events.find((e) => e.type === "open")?.investigation_id || "SS-I-…";
    const TOOLS = [
      ["check_listing", "listing", "Is it real? Copied photos, impossible price, brand-new website, conflicting specs, hidden AI instructions."],
      ["identify_product", "listing", "Which product is this listing? Returns a SafeShelf product_id for the other tools."],
      ["product_safety", "product", "Official recall status, hazard reports found in reviews and photos, safety-mark checks."],
      ["find_copies", "product", "The same product under other listings or brands, with reasons."],
      ["safety_marks", "product", "Safety and energy marks the listing claims, checked against official registries."],
      ["safer_alternatives", "product", "Similar products with no recall and no hazard reports, with the reason for each."],
      ["owner_guidance", "product", "For someone who already owns it: stop or take care, recall remedy, return, report."],
      ["product_history", "product", "Everything that ever changed about this product, and its recalls."],
      ["case_file", "product", "Findings with evidence IDs and quotes, and the code rule behind the verdict."],
      ["investigation_trace", "trace", "Every step of an investigation: tool, model, time, tokens, estimated cost."],
    ];
    const TABS = {
      rest: { label: "REST API", note: "Runs here", method: "POST", path: "/v1/agent/sessions/stream" },
      mcp: { label: "MCP", note: "For AI assistants", method: "POST", path: "/mcp" },
      a2a: { label: "A2A", note: "Agent to agent", method: "GET", path: "/.well-known/agent-card.json" },
    };
    let tab = "rest";
    let mode = "instant";
    let tool = "check_listing";
    let busy = false;

    // --- Request: the listing (REST), a tool (MCP) or nothing to fill in (A2A) ---
    const input = (value, attrs = {}) => el("input", { value: value ?? "", autocomplete: "off", spellcheck: false, ...attrs });
    const f = { title: input(base.title), url: input(base.url, { inputMode: "url" }), price: input(base.price, { inputMode: "decimal" }), currency: input(base.currency, { maxLength: 3 }) };
    const field = (label, i, cls = "") => el("label", { className: `pg-field ${cls}` }, el("span", { textContent: label }), i);
    const edited = () => ["title", "url", "currency"].some((k) => f[k].value.trim() !== String(base[k] ?? "")) || Number(f.price.value) !== Number(base.price);
    const listing = () => {
      if (!edited()) return base;
      const out = {};
      for (const k of ["title", "url", "currency"]) if (f[k].value.trim()) out[k] = f[k].value.trim();
      if (f.price.value.trim() && !Number.isNaN(Number(f.price.value))) out.price = Number(f.price.value);
      return out;
    };
    const toolSel = el("select", { className: "pg-select", "aria-label": "MCP tool" }, ...TOOLS.map(([n]) => el("option", { value: n, textContent: n })));
    const toolNote = el("p", { className: "pg-hint" });
    const restForm = el("div", { className: "pg-form" },
      el("p", { className: "pg-label", textContent: "Body · the listing to check" }),
      field("Product title", f.title),
      el("div", { className: "pg-grid" }, field("Link", f.url, "wide"), field("Price", f.price), field("Currency", f.currency)),
      el("button", { type: "button", className: "link", textContent: "Reset to the sample listing", onclick: () => { Object.entries(f).forEach(([k, i]) => { i.value = base[k] ?? ""; }); draw(); } }));
    const mcpForm = el("div", { className: "pg-form" }, el("p", { className: "pg-label", textContent: "Tool to call" }), toolSel, toolNote,
      el("p", { className: "pg-hint", textContent: "All 10 tools are read-only: an agent can check a listing, never buy, report or act for the shopper." }));
    const a2aForm = el("div", { className: "pg-form" }, el("p", { className: "pg-label", textContent: "No body needed" }),
      el("p", { className: "pg-hint", textContent: "Another agent first reads SafeShelf's agent card to learn what it can do, then sends it a listing in plain words over message/send." }));

    const snippet = () => {
      if (tab === "rest") return `curl -N -X POST ${API}/v1/agent/sessions/stream \\\n  -H 'content-type: application/json' \\\n  -H "authorization: Bearer $FIREBASE_ID_TOKEN" \\\n  -d '${JSON.stringify({ mode: "investigate", product_id: "unmatched", listing: listing() })}'`;
      if (tab === "mcp") {
        const kind = TOOLS.find((t) => t[0] === tool)[1];
        const { url, title, price, currency } = listing();
        const args = kind === "listing" ? { url, title, price, currency } : kind === "trace" ? { investigation_id: caseId } : { product_id: "<from identify_product>" };
        return `// 1. Add SafeShelf to your MCP client\n${JSON.stringify({ mcpServers: { safeshelf: { url: `${API}/mcp`, headers: { "x-api-key": "YOUR_KEY" } } } }, null, 2)}\n\n// 2. Your agent then calls\n${JSON.stringify({ method: "tools/call", params: { name: tool, arguments: args } }, null, 2)}`;
      }
      return `curl ${API}/.well-known/agent-card.json\n\n# then, from your agent (x-api-key: YOUR_KEY)\ncurl -X POST ${API}/a2a/ -H 'content-type: application/json' \\\n  -d '${JSON.stringify({ jsonrpc: "2.0", id: 1, method: "message/send", params: { message: { role: "user", messageId: "1", parts: [{ kind: "text", text: `Is this safe to buy? ${listing().url || ""}` }] } } })}'`;
    };
    const code = el("pre", { className: "pg-code" });
    const copy = copyBtn("Copy", snippet);
    copy.className = "pg-copy";
    const codeBox = el("details", { className: "pg-codebox" }, el("summary", {}, el("span", { textContent: "See it as code" }), copy), code);

    const method = el("span", { className: "pg-method" });
    const path = el("span", { className: "pg-path" });
    const urlBar = el("div", { className: "pg-url" }, method, path);

    // --- Send: Instant or Live on REST, Fetch on A2A, Copy on MCP ---
    const seg = el("div", { className: "pg-seg", role: "radiogroup", "aria-label": "How to run it" });
    const segBtn = (m, title, sub) => {
      const b = el("button", { type: "button", role: "radio", "data-mode": m }, el("b", { textContent: title }), el("small", { textContent: sub }));
      b.onclick = () => { if (!busy) { mode = m; draw(); } };
      seg.append(b);
    };
    segBtn("instant", "Instant", "Recorded real response");
    segBtn("live", "Live", "Cloud Run, now");
    const send = el("button", { type: "button", className: "primary pg-send" });
    const sendHint = el("p", { className: "pg-hint" });
    stopLeft?.();
    stopLeft = quota.onChange(() => draw());

    // --- Response ---
    const status = el("div", { className: "pg-status" });
    const verdictBox = el("div", { className: "pg-verdict", hidden: true });
    const timeline = el("ol", { className: "pg-timeline" });
    const raw = el("pre", { className: "pg-raw" });
    const rawBox = el("details", { className: "pg-rawbox", hidden: true }, el("summary", { textContent: "Raw response" }), raw);
    const empty = el("div", { className: "pg-empty" });
    const setStatus = (kind, text, sub = "") => { status.className = `pg-status is-${kind}`; status.replaceChildren(el("i"), el("b", { textContent: text }), sub ? el("span", { textContent: sub }) : ""); };
    const clearResponse = () => {
      verdictBox.hidden = true; timeline.replaceChildren(); raw.textContent = ""; rawBox.hidden = true; rawBox.open = false;
      const goRest = el("button", { type: "button", className: "small", textContent: "Try it on the REST tab", onclick: () => pickTab("rest") });
      if (tab === "rest") { setStatus("idle", "No request sent yet"); empty.replaceChildren(el("b", { textContent: "Press Send to see the answer" }), el("p", { textContent: "Every agent step shows up here as it streams in, then the verdict." })); }
      if (tab === "mcp") { setStatus("idle", "Runs inside your agent"); empty.replaceChildren(el("b", { textContent: "MCP needs your API key" }), el("p", { textContent: "Your MCP client (Claude, Gemini or any other) calls the tools with your key, so it can't run from this page. The REST tab runs the same check here." }), goRest); }
      if (tab === "a2a") { setStatus("idle", "No request sent yet"); empty.replaceChildren(el("b", { textContent: "Press Send to fetch the agent card" }), el("p", { textContent: "A real call to Cloud Run. Public, no sign-in, no check used." })); }
      empty.hidden = false;
    };
    const rows = new Map();
    const row = (agent) => {
      if (!rows.has(agent)) {
        const li = el("li", { className: "is-run" }, el("i"), el("div", {}, el("b", { textContent: AGENT[agent] || agent }), el("span", { textContent: "Working…" })), el("small"));
        rows.set(agent, li);
        timeline.append(li);
      }
      return rows.get(agent);
    };
    const handle = (e, ms) => {
      raw.textContent += `data: ${JSON.stringify(e)}\n\n`;
      if (e.type === "open") setStatus("run", "200 OK · streaming", `case ${e.investigation_id}`);
      if (e.type === "start" && e.agent) row(e.agent);
      if (e.type === "step" && e.agent) {
        const li = row(e.agent);
        const skipped = /^Skipped/.test(e.summary || "");
        li.className = skipped ? "is-skip" : "is-done";
        li.querySelector("span").textContent = skipped ? "Not needed for this listing" : e.summary;
        li.querySelector("small").textContent = skipped ? "" : `${(Number(e.seconds) || 0).toFixed(1)} s`;
      }
      status.querySelector("span")?.replaceChildren(`${(ms / 1000).toFixed(1)} s`);
    };
    const finish = (result, ms, how) => {
      const v = result.verdict;
      raw.textContent += `data: {"type":"done", ...}\n`;
      setStatus("ok", "200 OK · done", `${how} · ${(ms / 1000).toFixed(1)} s`);
      verdictBox.className = `pg-verdict ${TONE[v.overall]}`;
      verdictBox.replaceChildren(el("span", { textContent: "result.verdict" }), el("b", { textContent: WORD[v.overall] }), el("p", { textContent: v.headline }),
        el("div", { className: "pg-kv" }, ...[["overall", v.overall], ["safe", v.safe], ["real", v.real], ["outcome", v.outcome]].map(([k, x]) => el("code", { textContent: `${k}: ${x}` }))),
        v.lead_record?.url ? recordLink(v.lead_record) : "");
      verdictBox.hidden = false;
    };
    const start = (how) => { rows.clear(); clearResponse(); empty.hidden = true; rawBox.hidden = false; setStatus("run", "Sending…", how); };

    const runInstant = async () => {
      Object.entries(f).forEach(([k, i]) => { i.value = base[k] ?? ""; });
      draw();
      start("Recorded response");
      const t0 = performance.now();
      for (const e of rec.events) {
        const wait = (e._ms || 0) - (performance.now() - t0);
        if (wait > 0) await new Promise((ok) => setTimeout(ok, wait));
        if (e.type === "done") finish(e.result, e._ms || 0, `recorded ${String(rec.recorded_at || "").slice(0, 10)}`); else handle(e, e._ms || 0);
      }
    };
    const runLive = async () => {
      if (!quota.left()) { setStatus("err", "No checks left", quota.usedUpText()); return; }
      quota.take().catch(() => {});
      start("Live on Cloud Run");
      const t0 = performance.now();
      const ms = () => performance.now() - t0;
      try {
        const res = await authFetch(`${API}/v1/agent/sessions/stream`, { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "investigate", product_id: "unmatched", listing: listing() }), signal: AbortSignal.timeout(170000) });
        if (!res.ok) {
          const detail = (await res.json().catch(() => ({}))).detail;
          throw new Error(typeof detail === "string" ? detail : `the API answered ${res.status}`);
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let result = null;
        while (!result) {
          const { value, done } = await reader.read();
          if (done) throw new Error("the connection closed before the answer");
          buffer += decoder.decode(value, { stream: true });
          let cut;
          while (!result && (cut = buffer.indexOf("\n\n")) >= 0) {
            const data = buffer.slice(0, cut).split("\n").filter((x) => x.startsWith("data:")).map((x) => x.slice(5)).join("\n");
            buffer = buffer.slice(cut + 2);
            if (!data) continue;
            const e = JSON.parse(data);
            if (e.type === "error") throw new Error(e.detail || "the agents could not finish");
            if (e.type === "done") result = e.result; else handle(e, ms());
          }
        }
        reader.cancel().catch(() => {});
        finish(result, ms(), "live on Cloud Run");
      } catch (err) {
        setStatus("err", "Didn't finish", err.name === "TimeoutError" ? "No answer within about 3 minutes. Instant still works." : `${err.message}. Instant still works.`);
      }
    };
    const runCard = async () => {
      start("GET agent card");
      const t0 = performance.now();
      try {
        const res = await fetch(`${API}/.well-known/agent-card.json`, { signal: AbortSignal.timeout(20000) });
        if (!res.ok) throw new Error(`the API answered ${res.status}`);
        const c = await res.json();
        setStatus("ok", `${res.status} OK`, `live on Cloud Run · ${Math.round(performance.now() - t0)} ms`);
        verdictBox.className = "pg-verdict card";
        verdictBox.replaceChildren(el("span", { textContent: "Agent card" }), el("b", { textContent: c.name || "SafeShelf" }), el("p", { textContent: c.description || "" }),
          el("div", { className: "pg-kv" }, ...(c.skills || []).map((s) => el("code", { textContent: s.name }))));
        verdictBox.hidden = false;
        raw.textContent = JSON.stringify(c, null, 2);
      } catch (err) { setStatus("err", "Couldn't reach the API", err.message); }
    };
    send.onclick = async () => {
      if (busy) return;
      if (tab === "mcp") { try { await navigator.clipboard.writeText(snippet()); send.textContent = "Copied"; } catch (_) { send.textContent = "Couldn't copy"; } setTimeout(draw, 1600); return; }
      busy = true;
      draw();
      try { await (tab === "a2a" ? runCard() : mode === "live" ? runLive() : runInstant()); } finally { busy = false; draw(); }
    };

    // --- Tabs, and redrawing everything that follows the choices ---
    const tabRow = el("div", { className: "pg-tabs", role: "tablist", "aria-label": "How your agent connects" });
    const tabBtns = Object.entries(TABS).map(([id, t]) => {
      const b = el("button", { type: "button", role: "tab", "data-tab": id }, el("b", { textContent: t.label }), el("small", { textContent: t.note }));
      b.onclick = () => pickTab(id);
      tabRow.append(b);
      return b;
    });
    const formSlot = el("div");
    const pickTab = (id) => { if (busy) return; tab = id; clearResponse(); draw(); };
    const draw = () => {
      tabBtns.forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
      method.textContent = TABS[tab].method;
      method.dataset.m = TABS[tab].method;
      path.textContent = `${API.replace(/^https?:\/\//, "")}${tab === "mcp" ? "/mcp · tools/call" : TABS[tab].path}`;
      formSlot.replaceChildren(tab === "rest" ? restForm : tab === "mcp" ? mcpForm : a2aForm);
      toolSel.value = tool;
      toolNote.textContent = TOOLS.find((t) => t[0] === tool)[2];
      code.textContent = snippet();
      seg.hidden = tab !== "rest";
      seg.querySelectorAll("button").forEach((b) => { b.setAttribute("aria-checked", String(b.dataset.mode === mode)); b.disabled = busy || (b.dataset.mode === "instant" && !rec); });
      Object.values(f).forEach((i) => { i.disabled = busy; });
      tabBtns.forEach((b) => { b.disabled = busy && b.dataset.tab !== tab; });
      send.disabled = busy || (tab === "rest" && mode === "live" && !quota.left());
      send.textContent = busy ? "Running…" : tab === "mcp" ? "Copy MCP setup" : tab === "a2a" ? "Send" : mode === "live" ? "Send live" : "Send";
      sendHint.textContent = tab === "mcp" ? "Paste it into your MCP client's settings." : tab === "a2a" ? "Fetches the real agent card from Cloud Run."
        : mode === "live" ? `Runs all the agents on Cloud Run now (about 10 to 40 s). Uses 1 check · ${quota.text()}.`
        : "Replays a real response this API sent for the sample listing, at its real speed. No sign-in.";
    };
    toolSel.onchange = () => { tool = toolSel.value; draw(); };
    Object.values(f).forEach((i) => { i.oninput = () => { if (mode === "instant" && edited()) mode = "live"; draw(); }; });

    // a quiet ping, so the title bar shows whether the API is up
    const ping = el("span", { className: "pg-ping", textContent: "Checking the API…" });
    (async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(`${API}/.well-known/agent-card.json`, { signal: AbortSignal.timeout(8000) });
        if (!r.ok) throw new Error();
        ping.className = "pg-ping on"; ping.textContent = `API up · ${Math.round(performance.now() - t0)} ms`;
      } catch (_) { ping.textContent = "API not reachable"; }
    })();

    clearResponse();
    draw();
    return [
      el("ol", { className: "steps3", "aria-label": "How to use it" },
        el("li", {}, el("b", { textContent: "1" }), "Pick how your agent connects"),
        el("li", {}, el("b", { textContent: "2" }), "Press ", el("em", { textContent: "Send" })),
        el("li", {}, el("b", { textContent: "3" }), "Watch each agent answer on the right")),
      el("div", { className: "pg-stage" },
        el("div", { className: "pg-win" },
          el("div", { className: "pg-bar" }, el("span", { className: "lights", "aria-hidden": "true" }, el("i"), el("i"), el("i")),
            el("b", { textContent: "SafeShelf API playground" }), ping),
          tabRow,
          el("div", { className: "pg-main" },
            el("section", { className: "pg-req", "aria-label": "Request" },
              el("h4", { textContent: "Request" }), urlBar, formSlot,
              el("div", { className: "pg-actions" }, seg, send), sendHint, codeBox),
            el("section", { className: "pg-res", "aria-label": "Response", "aria-live": "polite" },
              el("h4", { textContent: "Response" }), status, empty, verdictBox, timeline, rawBox)))),
      next(go("site/agents.html", "For developers", false), go(`${API}/docs`, "API docs"), go("https://github.com/solomonwilsonr/all-builders", "Source on GitHub")),
    ];
  },
};

// --- The rest of the page follows the view: each person sees only their sections, ways to try it and products ---
const SAY = {
  shopper: {
    "cta-h": "Check before you pay, wherever you shop.", "cta-p": "The Chrome extension and the WhatsApp number are coming soon. The web page works today, on a phone too.",
    "cta-btns": [["site/get.html", "Get SafeShelf"], ["site/chat.html", "Open the chat"]] },
  marketplace: { try: "Paste a seller's listing and watch every check run live.", "prod-h": "What marketplaces use", "prod-p": "Scan the whole catalog, or check each listing as it goes live.",
    "cta-h": "Scan your catalog with SafeShelf", "cta-p": "Send a product list; get back the listings that need action, each with its evidence.",
    "cta-btns": [["site/get.html", "Talk to us"], ["site/agents.html", "Connect over the API"]], "hero-2": ["#check-own", "Check a listing"] },
  regulator: { try: "Paste any listing and watch the investigation run, step by step.", "hero-2": ["#accuracy", "See the proof"] },
  developer: { "prod-h": "What you build on", "prod-p": "The same engine, as read-only tools for your agent.",
    "cta-h": "Build on the evidence", "cta-p": "Read-only tools, sourced answers, and a verdict set by code.",
    "cta-btns": [["site/agents.html", "For developers"], [`${API}/docs`, "API docs"]], "hero-1": ["#for", "See the developer view"], "hero-2": ["#accuracy", "See the proof"] },
};
const SHARED = { // the proof sections each person still sees
  shopper: [],
  marketplace: [["#accuracy", "how accurate it is"]],
  regulator: [["#accuracy", "how accurate it is"], ["#attack", "whether it can be fooled"]],
  developer: [["#accuracy", "how accurate it is"], ["#attack", "whether it can be fooled"]],
};
function applyView(id) {
  for (const e of document.querySelectorAll("[data-for]")) e.hidden = !e.dataset.for.split(" ").includes(id);
  const visible = (sel) => [...document.querySelectorAll(sel)].filter((e) => !e.hidden);
  const lastOn = (items) => items.forEach((e, i) => e.classList.toggle("last-on", i === items.length - 1));

  // the jump menu keeps only the sections this person sees
  const blocks = visible("main > section.block");
  const jump = document.querySelector(".jump");
  const links = [...jump.querySelectorAll("a")];
  links.forEach((a) => { a.hidden = !blocks.some((b) => `#${b.id}` === a.getAttribute("href")); });
  const shown = links.filter((a) => !a.hidden);
  jump.style.setProperty("--n", shown.length);
  lastOn(shown);

  // ways to try it: if the open one is gone, open the first one left; one way alone needs no tab row
  const tabs = [...document.querySelectorAll(".trytabs [role=tab]")];
  const tabsOn = tabs.filter((t) => !t.hidden);
  const row = document.querySelector(".trytabs");
  row.style.setProperty("--n", tabsOn.length || 1);
  row.classList.toggle("solo", tabsOn.length < 2);
  lastOn(tabsOn);
  if (tabsOn.length && !tabsOn.some((t) => t.getAttribute("aria-selected") === "true")) {
    const keep = location.hash;
    tabsOn[0].click();
    try { history.replaceState(null, "", location.pathname + location.search + keep); } catch (_) { /* file:// */ }
  }

  const prods = document.querySelector(".prods");
  prods?.style.setProperty("--n", Math.max(3, visible(".prod-card").length)); // one or two cards keep their usual width

  // words for this person
  for (const e of document.querySelectorAll("[data-say]")) {
    if (!("was" in e.dataset)) e.dataset.was = e.dataset.say === "cta-btns" ? e.innerHTML : e.textContent;
    const say = SAY[id]?.[e.dataset.say];
    if (e.dataset.say === "cta-btns") {
      if (say) e.replaceChildren(...say.map(([href, text], i) => el("a", { className: `jbtn${i ? " line" : ""}`, href, textContent: text })));
    } else if (e.dataset.say.startsWith("hero-")) {
      if (!("wasHref" in e.dataset)) e.dataset.wasHref = e.getAttribute("href");
      const [href, text] = say || [e.dataset.wasHref, e.dataset.was];
      e.href = href;
      e.textContent = text;
    } else e.textContent = say || e.dataset.was;
  }
}

// --- Switching from anywhere: a "Viewing as" pill in the jump bar, hidden only while the four cards are on screen ---
function switcher(pick, cards) {
  const face = el("img", { className: "fs-face", alt: "", decoding: "async" });
  const name = el("b");
  const btn = el("button", { type: "button", className: "fs-btn", "aria-haspopup": "true", "aria-expanded": "false" },
    face, el("span", { className: "fs-t" }, el("small", { textContent: "Viewing as" }), name),
    el("span", { className: "fs-caret", "aria-hidden": "true", textContent: "▾" }));
  const menu = el("div", { className: "fs-menu", role: "menu", hidden: true },
    el("p", { className: "fv-tag", textContent: "Switch view" }),
    ...VIEWS.map((v) => {
      const item = el("button", { type: "button", className: "fs-item", role: "menuitemradio", "data-view": v.id, "aria-checked": "false" },
        el("span", { className: `fs-av fs-tint ${v.id}` }, el("img", { src: `site/assets/eddy-${v.id}.png`, alt: "", decoding: "async" })),
        el("span", { className: "fs-t" }, el("b", { textContent: v.label }), el("small", { textContent: v.ask })));
      item.onclick = () => { open(false); pick(v.id); };
      return item;
    }));
  // the chip leads the sticky section bar; the menu lives outside it, since the bar scrolls sideways and would clip it
  btn.hidden = true;
  document.querySelector(".jump")?.prepend(btn);
  document.body.append(menu);

  const open = (on) => {
    menu.hidden = !on;
    btn.setAttribute("aria-expanded", String(on));
    if (!on) return;
    const r = btn.getBoundingClientRect();
    menu.style.top = `${r.bottom + 8}px`;
    menu.style.left = `${Math.max(12, Math.min(r.left, innerWidth - menu.offsetWidth - 12))}px`;
    (menu.querySelector("[aria-checked=true]") || menu.querySelector(".fs-item"))?.focus();
  };
  btn.onclick = () => open(menu.hidden);
  document.addEventListener("click", (e) => { if (!btn.contains(e.target) && !menu.contains(e.target)) open(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { open(false); btn.focus(); } });
  addEventListener("resize", () => open(false));

  // everywhere except while the four cards are on screen (they are the switch then)
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(([e]) => {
      btn.hidden = e.isIntersecting;
      if (e.isIntersecting) open(false);
    }).observe(cards);
  } else btn.hidden = false;

  return {
    sync(id) {
      const v = VIEWS.find((x) => x.id === id);
      face.src = `site/assets/eddy-${id}.png`;
      face.className = `fs-face fs-tint ${id}`;
      name.textContent = v.label;
      for (const i of menu.querySelectorAll(".fs-item")) i.setAttribute("aria-checked", String(i.dataset.view === id));
    },
  };
}

// --- The picker ---
function chosen() {
  const q = new URLSearchParams(location.search).get("for") || location.hash.match(/^#for=([a-z]+)/)?.[1];
  let saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) { /* private mode */ }
  return [q, saved].find((id) => VIEWS.some((v) => v.id === id)) || "shopper";
}

export async function setUpRoles() {
  const root = document.getElementById("for-views");
  if (!root) return;
  try {
    presets = (await getJSON("samples/presets.json")).presets;
    const preset = presets.find((p) => p.id === STORY);
    story = { preset, result: await sample(STORY) };
  } catch (_) { root.replaceChildren(el("p", { className: "error", textContent: "The demo views could not be loaded." })); return; }

  const l = story.preset.request.listing;
  const v = story.result.verdict;
  const strip = el("div", { className: "fv-story" },
    el("span", { className: "fv-tag", textContent: "Same product in every view" }),
    el("b", { textContent: story.preset.name }),
    el("span", { textContent: `${story.preset.market} · ${money(l.price, l.currency)}` }),
    el("span", { className: `fv-chip ${TONE[v.overall]}`, textContent: `${WORD[v.overall]} · ${v.lead_record.authority} notice, ${v.lead_record.published}` }));

  const cards = el("div", { className: "fv-picks", role: "group", "aria-label": "Choose your view" });
  const panel = el("div", { className: "fv-panel", id: "for-panel", "aria-live": "polite" });
  root.replaceChildren(cards, strip, panel);

  let run = 0;
  const dock = switcher((id) => show(id), cards);
  const show = async (id, { save = true, scroll = false } = {}) => {
    const view = VIEWS.find((x) => x.id === id);
    const mine = ++run;
    cards.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === id)));
    if (save) {
      try { localStorage.setItem(KEY, id); } catch (_) { /* private mode */ }
      try {
        const u = new URL(location.href);
        u.searchParams.set("for", id);
        if (/^#for=/.test(u.hash)) u.hash = "";
        history.replaceState(null, "", u);
      } catch (_) { /* file:// */ }
    }
    applyView(id);
    dock.sync(id);
    panel.replaceChildren(el("p", { className: "muted", textContent: "Loading…" }));
    const body = await BUILD[id]();
    if (mine !== run) return;
    const link = new URL(location.href);
    link.searchParams.set("for", id);
    link.hash = "for";
    panel.replaceChildren(
      el("div", { className: "fv-head" },
        el("div", {}, el("span", { className: "fv-tag", textContent: view.who }), el("h3", { textContent: view.ask })),
        copyBtn("Copy a link to this view", link.href)),
      ...body,
      ...(SHARED[id].length ? [el("p", { className: "fv-shared" }, "Below: ", ...SHARED[id].flatMap(([href, text], i) =>
        [i ? " and " : null, el("a", { href, textContent: text })]), ".")] : []));
    if (scroll) panel.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  for (const view of VIEWS) {
    const b = el("button", { type: "button", className: "fv-pick", "data-view": view.id, "aria-pressed": "false" },
      el("span", { className: `fv-art ${view.id}` }, el("img", { src: `site/assets/eddy-${view.id}.png`, alt: "", decoding: "async" })),
      el("span", { className: "fv-check", "aria-hidden": "true", textContent: "✓" }),
      el("span", { className: "fv-t" }, el("b", { textContent: view.label }), el("small", { textContent: view.ask })));
    b.onclick = () => show(view.id, { scroll: matchMedia("(max-width: 640px)").matches });
    cards.append(b);
  }
  const first = chosen();
  await show(first, { save: false });
  if (/[?&]for=|#for=/.test(location.search + location.hash)) document.getElementById("for")?.scrollIntoView({ block: "start" });
}
