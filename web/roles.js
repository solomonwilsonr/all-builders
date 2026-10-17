// "Who are you?": one check, shown four ways. The same product (the HAIARA W5PRO power bank, recalled in Japan) runs
// through every view, so a judge sees one engine serving a shopper, a marketplace analyst, a regulator and a developer.
// Everything here is drawn from what the API really returned (samples/*.json, data/catalog.json); the developer view
// also calls the live API. The chosen view is kept in the address (?for=marketplace, or #for=…) and on this browser.
// Plain module, no build step. Text is always set as text, never as HTML.
import { API, el } from "./actions.js?v=20261017v";

const STORY = "recall_jp"; // the sample every view tells
const KEY = "safeshelf-view";
const ICONS = {
  shopper: "M6 7h12l-1 13H7zM9 7a3 3 0 0 1 6 0",
  marketplace: "M4 10h16M5 10l1-5h12l1 5M6 10v9h12v-9M10 19v-5h4v5",
  regulator: "M12 3 3 8h18zM5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18",
  developer: "m8 7-5 5 5 5M16 7l5 5-5 5",
};
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

const svg = (d) => {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("viewBox", "0 0 24 24");
  s.setAttribute("aria-hidden", "true");
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d);
  s.append(p);
  return s;
};
const resultOf = (sample) => sample.events.find((e) => e.type === "done")?.result;
const money = (n, cur) => { try { return new Intl.NumberFormat("en", { style: "currency", currency: cur, maximumFractionDigits: 0 }).format(n); } catch (_) { return `${cur} ${n}`; } };
const pct = (x) => `${Math.round(100 * x)}%`;
const getJSON = (path) => fetch(path).then((r) => { if (!r.ok) throw new Error(path); return r.json(); });

// --- Shared data, loaded once ---
let presets = [];
let story = null; // { preset, result }
const samples = new Map();
async function sample(id) {
  if (!samples.has(id)) samples.set(id, getJSON(`samples/${id}.json`).then(resultOf));
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

  developer() {
    const l = story.preset.request.listing;
    const curl = `curl -N -X POST \\\n  ${API}/v1/agent/sessions/stream \\\n  -H 'content-type: application/json' \\\n  -H "authorization: Bearer $FIREBASE_ID_TOKEN" \\\n  -d '${JSON.stringify({ mode: "investigate", product_id: "unmatched", listing: l })}'`;
    const mcp = JSON.stringify({ mcpServers: { safeshelf: { url: `${API}/mcp`, headers: { "x-api-key": "YOUR_KEY" } } } }, null, 2);
    const v = story.result.verdict;
    const answer = JSON.stringify({ overall: v.overall, safe: v.safe, real: v.real, outcome: v.outcome, headline: v.headline,
      lead_record: { authority: v.lead_record.authority, record_id: v.lead_record.record_id, url: v.lead_record.url } }, null, 2);
    const out = el("pre", { className: "fv-code", textContent: answer });
    const state = el("span", { className: "fv-live", textContent: "Stored answer for this listing" });
    const run = el("button", { type: "button", className: "primary small", textContent: "Run it live: fetch the agent card" });
    run.onclick = async () => {
      run.disabled = true;
      state.textContent = "Calling Cloud Run…";
      const t0 = performance.now();
      try {
        const res = await fetch(`${API}/.well-known/agent-card.json`, { signal: AbortSignal.timeout(20000) });
        if (!res.ok) throw new Error(`The API answered ${res.status}`);
        const card = await res.json();
        out.textContent = JSON.stringify({ name: card.name, version: card.version, url: card.supportedInterfaces?.[0]?.url,
          skills: (card.skills || []).map((s) => s.name) }, null, 2);
        state.textContent = `Live from Cloud Run · ${Math.round(performance.now() - t0)} ms`;
      } catch (err) { state.textContent = `Couldn't reach the API: ${err.message}`; }
      run.disabled = false;
    };
    return [
      el("ol", { className: "fv-steps" },
        step(1, "Ask over REST", el("p", { className: "muted", textContent: "The same listing. The investigation streams each step as server-sent events." }),
          el("pre", { className: "fv-code", textContent: curl }), copyBtn("Copy", curl)),
        step(2, "Or plug in MCP and A2A", el("p", { className: "muted", textContent: "Ten read-only tools. An agent can check a listing; it can never buy, report or act for the shopper." }),
          el("pre", { className: "fv-code", textContent: mcp }), copyBtn("Copy", mcp),
          el("p", { className: "fv-tools" }, ...["check_listing", "identify_product", "product_safety", "find_copies", "safety_marks", "safer_alternatives",
            "owner_guidance", "product_history", "case_file", "investigation_trace"].map((t) => el("code", { textContent: t })))),
        step(3, "What comes back", el("div", { className: "fv-btns" }, run, state), out)),
      next(go("site/agents.html", "For developers", false), go(`${API}/docs`, "API docs"), go("https://github.com/solomonwilsonr/all-builders", "Source on GitHub")),
    ];
  },
};

// --- The rest of the page follows the view: each person sees only their sections, ways to try it and products ---
const SAY = {
  shopper: { try: "Three ways to check before you buy. Pick one.", "prod-h": "Where you can use it", "prod-p": "Check a product wherever you shop.",
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
      el("span", { className: "fv-i" }, svg(ICONS[view.id])),
      el("span", { className: "fv-t" }, el("b", { textContent: view.label }), el("small", { textContent: view.ask })));
    b.onclick = () => show(view.id, { scroll: matchMedia("(max-width: 640px)").matches });
    cards.append(b);
  }
  const first = chosen();
  await show(first, { save: false });
  if (/[?&]for=|#for=/.test(location.search + location.hash)) document.getElementById("for")?.scrollIntoView({ block: "start" });
}
