// SafeShelf site: the Help chat on every page. Questions about SafeShelf and the site go to the API's
// /v1/support/ask (engine/support.py: Gemini, answering only from support-kb.json). When the API can't answer
// (offline, rate-limited, or MOCK=1), the same support-kb.json is searched here in the browser, so a visitor always
// gets the closest section of the site. A product check ("is this charger safe?") is handed to Eddy on chat.html.
// The conversation is kept for this tab (sessionStorage) so it follows the visitor between pages.
// Test against a local API: ?api=http://localhost:8080 (remembered for the tab).
(() => {
  if (new URLSearchParams(location.search).get("embed") === "1") return;
  const KB_URL = new URL("support-kb.json", document.currentScript?.src || location.href);
  const LIVE = "https://safeshelf-api-368488022657.asia-south1.run.app";
  const store = {
    get(k) { try { return JSON.parse(sessionStorage.getItem(`safeshelf-help-${k}`)); } catch (_) { return null; } },
    set(k, v) { try { sessionStorage.setItem(`safeshelf-help-${k}`, JSON.stringify(v)); } catch (_) { /* storage off */ } },
  };
  const apiParam = new URLSearchParams(location.search).get("api");
  if (apiParam && /^https?:\/\//.test(apiParam)) store.set("api", apiParam.replace(/\/$/, ""));
  const API = store.get("api") || LIVE;
  const SUGGEST = ["What is SafeShelf?", "How many free checks do I get?", "How do I install the Android app?",
    "Does it work on my phone?", "How do I connect my AI agent?", "What do the colours mean?"];
  const GREETING = "Hi, I'm SafeShelf Help. Ask me anything about the site: what SafeShelf does, signing in and limits, "
    + "the Android app, the API, or how a check works. To check a product, use Chat with Eddy.";

  const icon = (d, cls = "") => `<svg viewBox="0 0 24 24" class="${cls}" aria-hidden="true">${d}</svg>`;
  const make = (tag, props = {}, html = "") => Object.assign(document.createElement(tag), props, html ? { innerHTML: html } : {});

  // ---- DOM
  const launch = make("button", { type: "button", className: "sup-launch", ariaLabel: "Open SafeShelf Help" },
    icon('<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.3 2.4c-.5.2-.8.6-.8 1.1v.5"/><path d="M12 16.5h.01"/>') + "<span>Help</span>");
  launch.setAttribute("aria-expanded", "false");
  launch.setAttribute("aria-controls", "sup-panel");
  const panel = make("section", { id: "sup-panel", className: "sup-panel", hidden: true });
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "SafeShelf Help");
  panel.innerHTML = `
    <div class="sup-head"><span class="sup-mark" aria-hidden="true">S</span>
      <div><b>SafeShelf Help</b><small>Answers from this site's pages</small></div>
      <button type="button" class="sup-new" title="Start a new conversation">New chat</button>
      <button type="button" class="sup-x" aria-label="Close Help">${icon('<path d="M6 6l12 12M18 6 6 18"/>')}</button></div>
    <div class="sup-log" aria-live="polite"></div>
    <div class="sup-chips"></div>
    <form class="sup-form"><label class="sr-only" for="sup-q" style="position:absolute;left:-9999px">Your question</label>
      <textarea id="sup-q" rows="1" maxlength="1000" placeholder="Ask about SafeShelf…"></textarea>
      <button type="submit" aria-label="Send" disabled>${icon('<path d="M5 12h14M13 6l6 6-6 6"/>')}</button></form>
    <div class="sup-foot">Help can be wrong; each answer links its page. <a href="https://github.com/solomonwilsonr/all-builders/issues" target="_blank" rel="noopener">Report a problem</a></div>`;
  document.body.append(launch, panel);
  const log = panel.querySelector(".sup-log"), chips = panel.querySelector(".sup-chips");
  const form = panel.querySelector(".sup-form"), box = form.querySelector("textarea"), send = form.querySelector("button");

  // ---- rendering: answers are plain text; URLs and "- " lines are the only formatting
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const linkify = (s) => esc(s).replace(/\bhttps?:\/\/[^\s<)]+[^\s<).,;:!?]/g, (u) => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`);
  const format = (text) => {
    const out = []; let list = null;
    for (const line of text.split(/\n+/).map((l) => l.trim()).filter(Boolean)) {
      if (/^[-•*]\s+/.test(line)) { (list ||= []).push(`<li>${linkify(line.replace(/^[-•*]\s+/, ""))}</li>`); continue; }
      if (list) { out.push(`<ul>${list.join("")}</ul>`); list = null; }
      out.push(`<p>${linkify(line)}</p>`);
    }
    if (list) out.push(`<ul>${list.join("")}</ul>`);
    return out.join("");
  };
  // links in the knowledge file are relative to site/; resolve them there, so they work from the judges' page too
  const safeUrl = (u) => new URL(/^(https?:\/\/|\.\.\/|[\w-]+\.html)/.test(u || "") ? u : "index.html", KB_URL).href;
  const draw = (m) => {
    const el = make("div", { className: `sup-msg ${m.role === "user" ? "sup-me" : "sup-bot"}` });
    if (m.role === "user") { el.textContent = m.text; return el; }
    el.innerHTML = format(m.text);
    if (m.sources?.length) {
      const src = make("div", { className: "sup-src" });
      m.sources.forEach((s) => src.append(make("a", { href: safeUrl(s.url), textContent: s.page && s.page !== s.title ? `${s.page}: ${s.title}` : s.title })));
      el.append(src);
    }
    if (m.handoff) el.append(make("a", { className: "sup-hand", href: safeUrl(m.handoff.url), textContent: m.handoff.label }));
    if (m.note) el.append(make("div", { className: "sup-note", textContent: m.note }));
    return el;
  };

  let turns = store.get("turns") || [];
  const render = () => {
    log.replaceChildren(draw({ role: "assistant", text: GREETING }), ...turns.map(draw));
    chips.hidden = turns.length > 0;
    log.scrollTop = log.scrollHeight;
  };
  chips.append(...SUGGEST.map((q) => {
    const b = make("button", { type: "button", textContent: q });
    b.onclick = () => ask(q);
    return b;
  }));

  // ---- the local answer: the closest section of support-kb.json, by word overlap (BM25)
  let kbPromise = null;
  const kb = () => (kbPromise ||= fetch(KB_URL)
    .then((r) => (r.ok ? r.json() : { chunks: [] })).catch(() => ({ chunks: [] })));
  const STOP = new Set("a an and are as at be but by can do does for from get go how i if in into is it its me my no not of on or our so that the this to was we what when where which who why will with you your about there their them they then than too very just also any some have has had been would should could please tell know want many much".split(" "));
  const words = (s) => (s.toLowerCase().normalize("NFKD").match(/[\p{L}\p{N}]+/gu) || [])
    .filter((w) => !STOP.has(w) && w.length > 1).map((w) => w.replace(/(ies|es|s)$/, (m) => (m === "ies" ? "y" : "")));
  const localAnswer = async (q) => {
    const { chunks } = await kb();
    const qw = [...new Set(words(q))];
    if (!chunks.length || !qw.length) return null;
    const docs = chunks.map((c) => ({ c, t: words(c.title), w: words(c.text) }));
    const avg = docs.reduce((n, d) => n + d.w.length, 0) / docs.length;
    const df = (w) => docs.filter((d) => d.w.includes(w) || d.t.includes(w)).length;
    const idf = Object.fromEntries(qw.map((w) => [w, Math.log(1 + (docs.length - df(w) + 0.5) / (df(w) + 0.5))]));
    const scored = docs.map((d) => {
      let s = 0;
      for (const w of qw) {
        const tf = d.w.filter((x) => x === w).length;
        s += idf[w] * ((tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * d.w.length / avg)) + (d.t.includes(w) ? 0.8 : 0));
      }
      return { c: d.c, s };
    }).sort((a, b) => b.s - a.s);
    if (scored[0].s < 1.2) return null;
    const best = scored[0].c;
    // the sentences that match the question best, in the page's order (".in" or "debug.apk" never ends a sentence)
    const sentences = best.text.split(/\n+/).flatMap((line) => line.split(/(?<=[.!?])\s+(?=[\p{Lu}\p{N}"“(])/u))
      .map((s, at) => ({ s: s.trim(), at, n: [...new Set(words(s))].reduce((n, w) => n + (idf[w] || 0), 0) }))
      .filter((x) => x.s.length > 24 || x.n > 0);
    const picked = [];
    let room = 420;
    for (const x of [...sentences].sort((a, b) => b.n - a.n || a.at - b.at)) {
      if (x.s.length > room && picked.length) continue;
      picked.push(x); room -= x.s.length;
      if (room < 60) break;
    }
    const text = picked.sort((a, b) => a.at - b.at).map((x) => (/[.!?]$/.test(x.s) ? x.s : `${x.s}.`)).join(" ");
    const related = scored.slice(1).filter((x) => x.s > scored[0].s * 0.6 && x.c.url !== best.url).slice(0, 2).map((x) => x.c);
    return { text: text.trim(), sources: [best, ...related].map(({ title, page, url }) => ({ title, page, url })) };
  };
  const looksLikeProductCheck = (q) => /https?:\/\/|amazon\.|flipkart\.|\/dp\/|\b(is|are) (this|these|it|my)\b.*\b(safe|real|fake|genuine|recalled)\b|\bsafe to (buy|use)\b/i.test(q)
    && !/safeshelf|site|page|sign|app|account/i.test(q);

  // ---- asking
  let busy = false;
  const ask = async (question) => {
    question = question.trim();
    if (!question || busy) return;
    busy = true; send.disabled = true;
    const history = turns.slice(-6).map(({ role, text }) => ({ role, text }));
    turns.push({ role: "user", text: question });
    render();
    const typing = make("div", { className: "sup-msg sup-bot" }, '<span class="sup-dots" aria-label="Help is typing"><i></i><i></i><i></i></span>');
    log.append(typing); log.scrollTop = log.scrollHeight;
    const chatLink = { label: "Ask Eddy on the Chat page", url: `chat.html?${new URLSearchParams({ q: question })}` };
    let reply = null;
    try {
      const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), 25000);
      const res = await fetch(`${API}/v1/support/ask`, {
        method: "POST", headers: { "content-type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ question, history, language: navigator.language || "English", page: location.pathname }),
      });
      clearTimeout(timer);
      if (res.ok && res.headers.get("X-SafeShelf-Source") === "real") {
        const body = await res.json();
        if (body.answer) reply = { role: "assistant", text: body.answer, sources: body.sources || [],
          handoff: body.kind === "product_check" ? chatLink : null };
      }
    } catch (_) { /* offline or slow: answered below from the site's pages */ }
    if (!reply) {
      if (looksLikeProductCheck(question)) {
        reply = { role: "assistant", text: "Checking a specific product or listing is Eddy's job: paste the link on the Chat page and Eddy checks recalls, reviews and the seller, with sources.", handoff: chatLink };
      } else {
        const found = await localAnswer(question);
        reply = found
          ? { role: "assistant", text: found.text, sources: found.sources, note: "Quick answer: the closest part of the site." }
          : { role: "assistant", text: "I couldn't find that on the site. Try the FAQs, or report it on GitHub and the team will help.",
            sources: [{ title: "Frequently asked questions", page: "Home", url: "index.html#faq" },
              { title: "GitHub issues", page: "", url: "https://github.com/solomonwilsonr/all-builders/issues" }] };
      }
    }
    turns.push(reply);
    turns = turns.slice(-20);
    store.set("turns", turns);
    busy = false; send.disabled = !box.value.trim();
    render();
  };

  // ---- open, close, type
  const open = (on) => {
    panel.hidden = !on;
    launch.setAttribute("aria-expanded", String(on));
    document.documentElement.classList.toggle("sup-open", on);
    store.set("open", on);
    if (on) { render(); kb(); setTimeout(() => box.focus(), 30); } else launch.focus();
  };
  launch.onclick = () => open(panel.hidden);
  panel.querySelector(".sup-x").onclick = () => open(false);
  panel.querySelector(".sup-new").onclick = () => { turns = []; store.set("turns", turns); render(); box.focus(); };
  panel.addEventListener("keydown", (e) => { if (e.key === "Escape") open(false); });
  const grow = () => { box.style.height = "auto"; box.style.height = `${Math.min(box.scrollHeight, 120)}px`; };
  box.addEventListener("input", () => { grow(); send.disabled = busy || !box.value.trim(); });
  box.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
  });
  form.addEventListener("submit", (e) => { e.preventDefault(); const q = box.value; box.value = ""; grow(); ask(q); });
  if (store.get("open") && innerWidth > 520) open(true);
})();
