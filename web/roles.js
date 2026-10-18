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

  // The agent console: the same request an agent sends, replayed (Instant) or run on Cloud Run (Live)
  async developer() {
    const rec = await recorded(STORY).catch(() => null);
    const base = story.preset.request.listing;
    const caseId = rec?.events.find((e) => e.type === "open")?.investigation_id || "SS-I-…";
    const recSteps = rec ? rec.events.filter((e) => e.type === "step").length : 10;
    const recMs = rec?.events.find((e) => e.type === "done")?._ms;
    const TOOLS = [
      ["check_listing", "listing", "Is it real? Copied photos, impossible price, brand-new website, conflicting specs, hidden AI instructions."],
      ["identify_product", "listing", "Which product is this listing? Returns a SafeShelf product_id for the other tools."],
      ["product_safety", "product", "Official recall status, hazard reports found in reviews and photos, safety-mark checks."],
      ["find_copies", "product", "The same product under other listings or brands: exact model, rebrand, variant or look-alike, with reasons."],
      ["safety_marks", "product", "Safety and energy marks the listing claims, checked against official registries."],
      ["safer_alternatives", "product", "Similar products with no recall and no hazard reports, with the reason for each."],
      ["owner_guidance", "product", "For someone who already owns it: stop or take care, recall remedy, return, report."],
      ["product_history", "product", "Everything that ever changed about this product, and its recalls."],
      ["case_file", "product", "Findings with evidence IDs and quotes, and the code rule behind the verdict. Never sent anywhere."],
      ["investigation_trace", "trace", "Every step of an investigation: tool, model, time, tokens, estimated cost."],
    ];
    const PROTO = { rest: "REST · server-sent events", mcp: "MCP · tools/call", a2a: "A2A · message/send" };
    let proto = "rest";
    let tool = "check_listing";

    // --- The request form (left) ---
    const input = (name, value, attrs = {}) => el("input", { name, value: value ?? "", autocomplete: "off", spellcheck: false, ...attrs });
    const f = { title: input("title", base.title), url: input("url", base.url, { inputMode: "url" }),
      price: input("price", base.price, { inputMode: "decimal" }), currency: input("currency", base.currency, { maxLength: 3 }) };
    const field = (label, ...kids) => el("label", { className: "dv-field" }, el("span", { textContent: label }), ...kids);
    const edited = () => ["title", "url", "currency"].some((k) => f[k].value.trim() !== String(base[k] ?? "")) || Number(f.price.value) !== Number(base.price);
    const listing = () => {
      if (!edited()) return base;
      const out = {};
      for (const k of ["title", "url", "currency"]) if (f[k].value.trim()) out[k] = f[k].value.trim();
      if (f.price.value.trim() && !Number.isNaN(Number(f.price.value))) out.price = Number(f.price.value);
      return out;
    };
    const short = () => { const { title, url, price, currency } = listing(); return { url, title, price, currency }; };
    const snippet = () => {
      if (proto === "rest") return `curl -N -X POST ${API}/v1/agent/sessions/stream \\\n  -H 'content-type: application/json' \\\n  -H "authorization: Bearer $FIREBASE_ID_TOKEN" \\\n  -d '${JSON.stringify({ mode: "investigate", product_id: "unmatched", listing: listing() })}'`;
      if (proto === "mcp") {
        const kind = TOOLS.find((t) => t[0] === tool)[1];
        const args = kind === "listing" ? short() : kind === "trace" ? { investigation_id: caseId } : { product_id: "<product_id from identify_product>" };
        return `POST ${API}/mcp\nx-api-key: YOUR_KEY\n\n${JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: tool, arguments: args } }, null, 2)}`;
      }
      return `GET  ${API}/.well-known/agent-card.json\nPOST ${API}/a2a/\nx-api-key: YOUR_KEY\n\n${JSON.stringify({ jsonrpc: "2.0", id: 1, method: "message/send", params: { message: { role: "user", messageId: "1",
        parts: [{ kind: "text", text: `Is this safe to buy? ${listing().url || listing().title || ""}` }] } } }, null, 2)}`;
    };
    const code = el("pre", { className: "dv-code" });
    const toolNote = el("p", { className: "dv-note" });
    const select = el("select", { className: "dv-select", "aria-label": "How your agent asks" },
      ...Object.entries(PROTO).map(([value, textContent]) => el("option", { value, textContent })));
    const toolBtns = [];
    const feats = [];
    const draw = () => {
      code.textContent = snippet();
      select.value = proto;
      const t = TOOLS.find((x) => x[0] === tool);
      toolNote.textContent = proto === "mcp" ? `${t[0]}: ${t[2]}` : proto === "rest" ? "The full investigation, every agent step streamed back as it happens." : "Another agent hands SafeShelf the listing in plain words and gets the answer back.";
      toolBtns.forEach((b) => b.setAttribute("aria-current", String(proto === "mcp" && b.dataset.tool === tool)));
      feats.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.proto === proto)));
    };
    const pick = (p, t) => { proto = p; if (t) tool = t; draw(); };
    select.onchange = () => pick(select.value);
    Object.values(f).forEach((i) => { i.oninput = draw; });

    // --- The investigation panel (right) ---
    const ORDER = ["page_reader", "is_it_real", "safety_radar", "twin_finder", "recall_checker", "cert_verifier", "research_agent", "official_sources", "verdict", "verdict_writer"];
    const rows = new Map(ORDER.map((id) => {
      const fill = el("span", { className: "dv-fill" });
      const time = el("small", { textContent: "–" });
      const row = el("div", { className: "dv-agent" }, el("span", { className: "dv-an", textContent: AGENT[id] }), el("span", { className: "dv-track" }, fill), time);
      return [id, { row, fill, time }];
    }));
    const word = el("b", { className: "dv-word", textContent: "Waiting" });
    const head = el("p", { className: "dv-headline", textContent: "Press Instant or Run live to watch the agents work." });
    const meta = el("p", { className: "dv-meta" });
    const verdictBox = el("div", { className: "dv-verdict grey" }, el("span", { className: "dv-label", textContent: "Answer" }), word, head, meta);
    const log = el("pre", { className: "dv-log" });
    const logBox = el("details", { className: "dv-logbox" }, el("summary", { textContent: "Raw event stream" }), log);
    let n = 0;
    const reset = (how) => {
      n = 0;
      for (const r of rows.values()) { r.row.className = "dv-agent"; r.fill.style.width = "0"; r.time.textContent = "–"; }
      verdictBox.className = "dv-verdict grey"; word.textContent = "Checking…"; head.textContent = how; meta.textContent = "";
      log.textContent = `# ${PROTO.rest} · ${how}\n`;
    };
    const handle = (e, ms) => {
      const t = `+${(ms / 1000).toFixed(1)}s`.padEnd(7);
      log.textContent += `${t} ${JSON.stringify(e).slice(0, 220)}\n`;
      log.scrollTop = log.scrollHeight;
      const r = rows.get(e.agent);
      if (e.type === "start" && r) r.row.className = "dv-agent is-run";
      if (e.type === "step") {
        n += 1;
        meta.textContent = `${n} of about ${recSteps} steps · ${(ms / 1000).toFixed(1)} s`;
        if (!r) return;
        const skipped = /^Skipped/.test(e.summary || "");
        const s = Number(e.seconds) || 0;
        r.row.className = `dv-agent ${skipped ? "is-skip" : "is-done"}`;
        r.row.title = e.summary || "";
        r.fill.style.width = skipped ? "100%" : `${Math.max(6, Math.min(100, (s / 5) * 100))}%`;
        r.time.textContent = skipped ? "skipped" : `${s.toFixed(1)} s`;
      }
      if (e.type === "verdict" && e.verdict) { verdictBox.className = `dv-verdict ${TONE[e.verdict.overall]}`; word.textContent = WORD[e.verdict.overall]; }
    };
    const finish = (result, ms, how) => {
      const v = result.verdict;
      log.textContent += `+${(ms / 1000).toFixed(1)}s`.padEnd(7) + ` done\n\n# result.verdict\n${JSON.stringify({ overall: v.overall, safe: v.safe, real: v.real, outcome: v.outcome, headline: v.headline,
        lead_record: v.lead_record ? { authority: v.lead_record.authority, record_id: v.lead_record.record_id } : null }, null, 2)}\n`;
      verdictBox.className = `dv-verdict ${TONE[v.overall]}`;
      word.textContent = WORD[v.overall];
      head.textContent = v.headline;
      meta.textContent = `${how} · ${n} steps · ${(ms / 1000).toFixed(1)} s · case ${result.investigation_id}`;
      if (v.lead_record?.url) meta.append(" · ", recordLink(v.lead_record));
    };

    // --- Instant, Live, and the agent card ---
    const status = el("span", { className: "dv-status", textContent: "Checking the API…" });
    const replay = el("button", { type: "button", className: "small", textContent: "Instant replay" });
    const runLive = el("button", { type: "button", className: "primary small", textContent: "Run live" });
    const left = el("small", { className: "dv-quota" });
    let busy = false;
    const lock = (on) => { busy = on; replay.disabled = on || !rec; runLive.disabled = on || !quota.left(); };
    const showLeft = () => { left.textContent = `Run live uses 1 check. ${quota.text()}.`; if (!busy) runLive.disabled = !quota.left(); };
    stopLeft?.();
    stopLeft = quota.onChange(showLeft);
    showLeft();
    replay.onclick = async () => {
      if (busy || !rec) return;
      lock(true);
      Object.entries(f).forEach(([k, i]) => { i.value = base[k] ?? ""; });
      draw();
      const how = `Recorded run, ${String(rec.recorded_at || "").slice(0, 10)}`;
      reset(how);
      const t0 = performance.now();
      for (const e of rec.events) {
        const wait = (e._ms || 0) - (performance.now() - t0);
        if (wait > 0) await new Promise((ok) => setTimeout(ok, wait));
        if (e.type === "done") finish(e.result, e._ms || 0, "Instant replay at real timing"); else handle(e, e._ms || 0);
      }
      lock(false);
    };
    runLive.onclick = async () => {
      if (busy) return;
      if (!quota.left()) { head.textContent = quota.usedUpText(); return; }
      lock(true);
      quota.take().catch(() => {});
      reset("Live from Cloud Run");
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
        finish(result, ms(), "Live from Cloud Run");
      } catch (err) {
        const why = err.name === "TimeoutError" ? "no answer within about 3 minutes" : err.message;
        verdictBox.className = "dv-verdict grey"; word.textContent = "Didn't finish";
        head.textContent = `Couldn't finish live: ${why}. Instant replay still works.`;
        log.textContent += `\n# stopped: ${why}\n`;
      }
      lock(false);
      showLeft();
    };
    lock(false);
    const card = el("button", { type: "button", className: "dv-sync", textContent: "Fetch the agent card (A2A, no sign-in)" }, el("span", { "aria-hidden": "true", textContent: "→" }));
    const getCard = async (quiet) => {
      const t0 = performance.now();
      try {
        const res = await fetch(`${API}/.well-known/agent-card.json`, { signal: AbortSignal.timeout(quiet ? 8000 : 20000) });
        if (!res.ok) throw new Error(`the API answered ${res.status}`);
        const c = await res.json();
        status.className = "dv-status on";
        status.textContent = `API live · ${Math.round(performance.now() - t0)} ms`;
        if (!quiet) {
          log.textContent = `# GET /.well-known/agent-card.json\n${JSON.stringify({ name: c.name, version: c.version, url: c.supportedInterfaces?.[0]?.url, skills: (c.skills || []).map((x) => x.name) }, null, 2)}\n`;
          logBox.open = true;
        }
      } catch (err) {
        status.className = "dv-status";
        status.textContent = "API not reachable";
        if (!quiet) { log.textContent = `# couldn't reach the API: ${err.message}\n`; logBox.open = true; }
      }
    };
    card.onclick = () => getCard(false);
    getCard(true);

    // --- The page around the console ---
    const mark = (text) => el("span", { className: "dv-tag", textContent: text });
    const feat = (p, title, text) => {
      const b = el("button", { type: "button", className: "dv-feat", "data-proto": p, "aria-pressed": "false" },
        el("b", {}, el("i", { "aria-hidden": "true" }), title), el("span", { textContent: text }));
      b.onclick = () => pick(p);
      feats.push(b);
      return b;
    };
    const stat = (big, text) => el("div", { className: "dv-stat" }, el("b", { textContent: big }), el("span", { textContent: text }));
    const toolList = el("nav", { className: "dv-tools", "aria-label": "MCP tools" }, el("span", { textContent: "MCP tools" }),
      ...TOOLS.map(([name]) => {
        const b = el("button", { type: "button", "data-tool": name, textContent: name });
        b.onclick = () => pick("mcp", name);
        toolBtns.push(b);
        return b;
      }));
    const copy = copyBtn("Copy", snippet);
    copy.className = "dv-copy";
    const win = el("div", { className: "dv-win" },
      el("div", { className: "dv-bar" },
        el("span", { className: "dv-app" }, el("img", { src: "site/assets/eddy-face.png", alt: "" }), "SafeShelf Agent Console"),
        el("span", { className: "dv-barr" }, status, select)),
      el("div", { className: "dv-main" },
        el("div", { className: "dv-form" },
          el("h4", { textContent: "Check a listing" }),
          el("p", { className: "dv-sub", textContent: "The request your agent sends. Change it and the code follows." }),
          el("div", { className: "dv-row" }, field("Title", f.title)),
          el("div", { className: "dv-row two" }, field("Link", f.url), el("div", { className: "dv-row two" }, field("Price", f.price), field("Currency", f.currency))),
          el("div", { className: "dv-codebox" }, el("div", { className: "dv-codehead" }, el("span", { textContent: "Request" }), copy), code),
          toolNote,
          el("div", { className: "dv-actions" }, left, el("span", { className: "dv-btns" }, replay, runLive))),
        el("div", { className: "dv-right" },
          el("div", { className: "dv-panel" },
            el("span", { className: "dv-ptitle", textContent: "Investigation" }),
            el("p", { className: "dv-sub", textContent: "Ten agents, one listing. Code sets the colour; Gemini only writes the words." }),
            verdictBox,
            el("div", { className: "dv-agents" }, ...[...rows.values()].map((r) => r.row)),
            logBox),
          card)));
    draw();
    return [
      el("div", { className: "dv" },
        el("div", { className: "dv-feats" },
          feat("rest", "Ask over REST", "POST a listing. Each agent step streams back as a server-sent event."),
          feat("mcp", "Plug in MCP", "Ten read-only tools for any MCP client, from identify to case file."),
          feat("a2a", "Talk over A2A", "Another agent hands SafeShelf a listing and gets the answer back.")),
        el("div", { className: "dv-intro" }, mark("For developers"), el("h3", { textContent: "One engine, three ways in" })),
        el("div", { className: "dv-stage" }, win),
        el("aside", { className: "dv-side" },
          stat("10", "read-only tools over MCP"),
          stat(String((story.result.verdict.coverage?.countries || []).length || "–"), "countries' official sources checked"),
          stat(recMs ? `${(recMs / 1000).toFixed(1)} s` : "–", "for the recorded check, end to end"),
          toolList),
        el("div", { className: "dv-safe" },
          el("div", {}, mark("Read-only by design"), el("h3", { textContent: "It can look. It can never act." })),
          el("p", { textContent: "No tool can buy, report or contact anyone for the shopper. Every answer cites the official notice or the review it came from." }),
          el("div", { className: "dv-seals" }, el("span", { textContent: "Code sets the verdict" }), el("span", { textContent: "Evidence on every answer" })))),
      next(go("site/agents.html", "For developers", false), go(`${API}/docs`, "API docs"), go("https://github.com/solomonwilsonr/all-builders", "Source on GitHub")),
    ];
  },

};

// --- The rest of the page follows the view: each person sees only their sections, ways to try it and products ---
const SAY = {
  shopper: { try: "Four ways to check before you buy. Pick one.", "prod-h": "Where you can use it", "prod-p": "Check a product wherever you shop.",
    "cta-h": "Check before you pay, wherever you shop.", "cta-p": "The Chrome extension and the WhatsApp number are coming soon. The web page works today, on a phone too.",
    "cta-btns": [["site/get.html", "Get SafeShelf"], ["site/chat.html", "Open the chat"]], "hero-2": ["#try", "Try it now"] },
  marketplace: { try: "Paste a seller's listing and watch every check run live.", "prod-h": "What marketplaces use", "prod-p": "Scan the whole catalog, or check each listing as it goes live.",
    "cta-h": "Scan your catalog with SafeShelf", "cta-p": "Send a product list; get back the listings that need action, each with its evidence.",
    "cta-btns": [["site/get.html", "Talk to us"], ["site/agents.html", "Connect over the API"]], "hero-2": ["#check-own", "Check a listing"] },
  regulator: { try: "Paste any listing and watch the investigation run, step by step.", "hero-2": ["#accuracy", "See the proof"] },
  developer: { "prod-h": "What you build on", "prod-p": "The same engine, as read-only tools for your agent.",
    "cta-h": "Build on the evidence", "cta-p": "Read-only tools, sourced answers, and a verdict set by code.",
    "cta-btns": [["site/agents.html", "For developers"], [`${API}/docs`, "API docs"]], "hero-2": ["#accuracy", "See the proof"] },
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

  // sections and the jump menu, numbered again in order
  const blocks = visible("main > section.block");
  blocks.forEach((b, i) => { const n = b.querySelector(".block-n"); if (n) n.textContent = String(i + 1).padStart(2, "0"); });
  const jump = document.querySelector(".jump");
  const links = [...jump.querySelectorAll("a")];
  links.forEach((a) => { a.hidden = !blocks.some((b) => `#${b.id}` === a.getAttribute("href")); });
  const shown = links.filter((a) => !a.hidden);
  shown.forEach((a, i) => { a.querySelector("span").textContent = String(i + 1).padStart(2, "0"); });
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
    } else if (e.dataset.say === "hero-2") {
      const [href, text] = say || ["#try", e.dataset.was];
      e.href = href;
      e.textContent = text;
    } else e.textContent = say || e.dataset.was;
  }
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
