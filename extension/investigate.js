// Investigate: the Shopper Agent (SAFESHELF.md 12.2) in the shopper's own tab. Started only by the Investigate button.
// Each step: list what can be opened on the page (numbered), the API's agent picks one (POST /v1/agent/sessions,
// mode shopper_step), this script highlights it, opens it if that is safe, and reads what it shows. Then the
// Investigate pipeline runs on the listing plus everything read, and the overlay shows the verdict set by code.
// Rules: read-only. Never buy, cart, sign in, fill in or submit anything: checked here AND by the API before each
// click. Never leaves the page (links to other pages are read, not followed). At most 15 steps and 60 seconds.
// The Stop button and Esc end it at once. Page text is sent as data only.
{
  const MAX_STEPS = 15;
  const BUDGET_MS = 60000;
  const BLOCKED = /\b(buy|add to (cart|bag|basket|wish ?list)|cart|checkout|check out|pay|payment|place (your )?order|order now|subscribe|sign ?in|log ?in|sign ?up|register|account|submit|send|delete|confirm|redeem|one-?click|cash on delivery|emi)\b/i;
  const BLOCKED_HREF = /\/(cart|checkout|buy|signin|sign-in|login|log-in|register|account|ap\/signin|gp\/cart|gp\/buy|payment|wishlist|orders?)(\/|\?|$)|^(javascript|mailto|tel):/i;
  const LABEL_WORDS = /label|rating plate|bis|isi|energy|certif|regulatory|spec plate|marking/i;

  const clean = (t, n = 300) => (t || "").replace(/\s+/g, " ").trim().slice(0, n);
  const visibleText = (e) => clean([e.innerText, e.getAttribute?.("aria-label"), e.getAttribute?.("alt"), e.title,
    ...[...e.querySelectorAll?.("[aria-label], img[alt], svg text, figcaption") || []].map((x) => x.getAttribute("aria-label") || x.alt || x.textContent)].filter(Boolean).join(" "), 1200);

  const blocked = (e) => {
    const tag = e.tagName.toLowerCase();
    if (["input", "textarea", "select", "form", "option"].includes(tag) || e.type === "submit") return "a form field";
    if (BLOCKED_HREF.test(e.getAttribute("href") || "")) return "a link to buying or an account";
    if (BLOCKED.test(clean(e.innerText || e.value || "", 120) + " " + (e.getAttribute("aria-label") || ""))) return "a buy, account or submit control";
    return null;
  };

  // What a careful buyer would look at, best effort across shops (the demo pages, Amazon, Flipkart), plus the page's buttons.
  const GROUPS = [
    ["image", "#gallery figure, #altImages li.imageThumbnail, #altImages li.item, ._2r_T1I, [data-testid='image-thumbnail'], figure"],
    ["review_filter", "a, button"],
    ["review", "article.review, [data-hook='review'], .col.EPCmJX, .RcXBOT"],
    ["seller", "#seller, #sellerProfileTriggerId, #merchant-info a, a[href*='seller']"],
    ["specs", "table.specs, #productDetails_techSpec_section_1, #prodDetails table, #detailBullets_feature_div, ._1UhVsV"],
    ["button", "button, [role='button']"],
  ];
  const REVIEW_FILTER = /\b(1|one)[ -]?star|critical|lowest rat|with (photos|images)|see (all|more) reviews|all reviews/i;

  const collect = (read) => {
    const out = [];
    const seen = new Set();
    for (const [kind, sel] of GROUPS) {
      for (const e of document.querySelectorAll(sel)) {
        if (seen.has(e) || e.closest("[data-safeshelf-ui]") || !e.getClientRects().length) continue;
        if (kind === "review_filter" && !REVIEW_FILTER.test(clean(e.innerText, 80))) continue;
        if (kind === "button" && !blocked(e)) continue; // other buttons add nothing; blocked ones are listed so code can refuse them
        seen.add(e);
        const text = visibleText(e);
        if (!text) continue;
        const i = out.length;
        e.dataset.safeshelfI = String(i);
        out.push({ i, tag: e.tagName.toLowerCase(), type: e.type || "", kind: kind === "image" && LABEL_WORDS.test(text) ? "label" : kind,
          text: clean(text, 200), aria: clean(e.getAttribute("aria-label"), 120), href: e.getAttribute("href") || "", already_read: read.has(e) });
        if (out.length >= 60) return out;
      }
    }
    return out;
  };

  const STYLE = `
    :host { all: initial; }
    .ov { position: fixed; right: 16px; bottom: 16px; z-index: 2147483647; width: min(380px, calc(100vw - 32px)); max-height: 70vh; overflow: auto;
      font: 14px/1.45 system-ui, sans-serif; color: #14213d; background: #fff; border: 2px solid #14213d; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,.25); padding: 14px; }
    h2 { margin: 0 0 6px; font-size: 16px; } .now { font-weight: 600; margin: 6px 0; } ol { margin: 6px 0; padding-left: 20px; max-height: 30vh; overflow: auto; }
    li { margin: 2px 0; } li.skip { color: #8a1c1c; } .muted { color: #555; font-size: 12px; } .row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
    button { font: inherit; padding: 6px 12px; border-radius: 8px; border: 1px solid #14213d; background: #fff; color: #14213d; cursor: pointer; }
    button:focus-visible { outline: 3px solid #4361ee; outline-offset: 2px; }
    .verdict { padding: 8px 10px; border-radius: 8px; margin: 8px 0; font-weight: 600; }
    .red { background: #fde2e1; } .amber { background: #fff3cd; } .green { background: #e3f6e8; } .unknown { background: #eceff3; }
    @media (prefers-color-scheme: dark) { .ov { background: #111827; color: #f3f4f6; border-color: #f3f4f6; } button { background: #111827; color: #f3f4f6; border-color: #f3f4f6; }
      .muted { color: #b8c0cc; } .red { background: #5c1d1d; } .amber { background: #5a4510; } .green { background: #173d26; } .unknown { background: #2a3140; } li.skip { color: #ffb4b4; } }`;
  const HIGHLIGHT = "outline: 4px solid #4361ee !important; outline-offset: 3px !important; transition: transform .25s; transform: scale(1.04);";
  const WORDS = { red: "⛔ Danger or not real", amber: "⚠️ Be careful: under review", green: "✅ Nothing found in what was checked", unknown: "❔ Not enough evidence yet" };

  const agent = (body, timeout) => new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ type: "safeshelf:agent", body, timeout }, (res) => (res?.ok ? resolve(res.result) : reject(new Error(res?.error || chrome.runtime.lastError?.message || "no answer"))));
  });
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  // The Investigate pipeline live: onEvent sees each check finish and the verdict as soon as code sets it.
  const agentLive = (body, onEvent, timeout = 240000) => new Promise((resolve, reject) => {
    const port = chrome.runtime.connect({ name: "safeshelf-agent" });
    let finished = false;
    port.onMessage.addListener((m) => {
      if (m.type === "event") return onEvent(m.event);
      finished = true;
      port.disconnect();
      if (m.type === "done") resolve(m.result); else reject(new Error(m.error || "no answer"));
    });
    port.onDisconnect.addListener(() => { if (!finished) reject(new Error(chrome.runtime.lastError?.message || "connection closed")); });
    port.postMessage({ body, timeout });
  });

  let running = null;

  const investigate = async (page) => {
    if (running) return running.focus();
    const host = document.createElement("div");
    host.dataset.safeshelfUi = "investigate";
    const root = host.attachShadow({ mode: "open" });
    const ov = document.createElement("div");
    ov.className = "ov";
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-label", "SafeShelf is investigating this page");
    ov.innerHTML = `<style>${STYLE}</style><h2>SafeShelf is investigating</h2><p class="muted">Looking at this page the way a careful buyer would. It never buys, signs in or fills in anything.</p>
      <p class="now" aria-live="polite"></p><ol></ol><div class="out"></div><div class="row"><button type="button" class="stop">Stop (Esc)</button></div>`;
    root.append(ov);
    document.body.append(host);
    const now = ov.querySelector(".now");
    const list = ov.querySelector("ol");
    const out = ov.querySelector(".out");
    const stopBtn = ov.querySelector(".stop");
    let stopped = false;
    const stop = () => { stopped = true; stopBtn.textContent = "Close"; stopBtn.onclick = close; };
    const close = () => { host.remove(); document.removeEventListener("keydown", onKey, true); running = null; };
    const onKey = (e) => { if (e.key === "Escape") { e.stopPropagation(); stopped ? close() : stop(); } };
    document.addEventListener("keydown", onKey, true);
    stopBtn.onclick = stop;
    running = { focus: () => stopBtn.focus() };
    stopBtn.focus();
    const say = (text, skip = false) => {
      now.textContent = text;
      const li = document.createElement("li");
      li.textContent = text;
      if (skip) li.className = "skip";
      list.append(li);
      li.scrollIntoView({ block: "nearest" });
    };

    const started = Date.now();
    const sessionId = `SS-I-${Math.random().toString(16).slice(2, 10).toUpperCase()}`;
    const observations = [];
    const read = new Set();
    try {
      for (let step = 1; step <= MAX_STEPS && !stopped && Date.now() - started < BUDGET_MS; step++) {
        const elements = collect(read);
        const next = await agent({ mode: "shopper_step", session_id: sessionId, step, url: page.url, title: page.title, elements,
          observations: observations.map(({ kind, text }) => ({ kind, text: clean(text, 200) })) });
        if (stopped) break;
        if (next.action === "done") { say(next.narration || "Finished looking around the page"); break; }
        const target = document.querySelector(`[data-safeshelf-i="${next.element}"]`);
        const why = next.action === "skip" ? next.reason : target ? blocked(target) : "it is no longer on the page";
        if (!target || why) { say(`Skipped: ${why}`, true); continue; }
        say(next.narration);
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        const before = target.getAttribute("style") || "";
        target.setAttribute("style", before + HIGHLIGHT);
        // Opening is a click only when it stays on this page; a link to another page is read where it is.
        const href = target.getAttribute("href") || "";
        if (next.action === "open" && (!href || href.startsWith("#")) && !blocked(target)) target.click();
        await wait(900);
        const meta = elements.find((x) => x.i === next.element) || {};
        const stars = Number((target.querySelector("[aria-label*='out of 5']")?.getAttribute("aria-label") || "").match(/([\d.]+) out of 5/)?.[1]) || undefined;
        observations.push({ kind: meta.kind || "text", text: visibleText(target), ...(stars && { rating: stars }) });
        read.add(target);
        target.setAttribute("style", before);
      }
      // Hidden text on the page goes in as data, so the pipeline can report it as a warning sign. It is never obeyed.
      const hidden = [...document.querySelectorAll("[aria-hidden='true'], [hidden], [style*='-9999px']")].map((e) => clean(e.textContent, 400)).filter((t) => t.length > 20);
      hidden.slice(0, 3).forEach((text) => observations.push({ kind: "hidden_text", text }));
      say(stopped ? "Stopped. Checking what was read so far…" : "Putting it all together…");
      const { product_id, listing_id, ...listing } = page;
      const CHECKS = { is_it_real: "Shop and price checked", safety_radar: "Recalls and reviews read", twin_finder: "Copies looked up", recall_checker: "Recall notices checked", cert_verifier: "Safety marks checked" };
      const v = await agentLive({ mode: "investigate", session_id: sessionId, product_id: product_id || "unmatched", listing, page_evidence: { observations }, recall_sites: true }, (e) => {
        if (e.type === "step" && CHECKS[e.agent]) say(`${CHECKS[e.agent]}: ${e.summary}`);
        if (e.type === "verdict") { now.textContent = `${WORDS[e.verdict.overall] || WORDS.unknown}. Searching official recall sites for this market…`; }
        if (e.type === "start" && e.tool === "recall_sites") say("Searching the official recall sites for this market (up to a minute)…");
        if (e.type === "research") (e.reasons || []).forEach((r) => say(`Recall sites: ${r.text}`));
      }, 280000);
      const level = v.verdict?.overall || "unknown";
      out.innerHTML = "";
      const box = document.createElement("div");
      box.className = `verdict ${level}`;
      box.textContent = WORDS[level] || WORDS.unknown;
      const summary = document.createElement("p");
      summary.textContent = v.messages?.[0]?.text || "";
      const reasons = document.createElement("ul");
      for (const r of v.verdict?.reasons || []) {
        const li = document.createElement("li");
        li.textContent = r.text + (r.evidence_ids?.length ? ` [${r.evidence_ids.join(", ")}]` : "");
        reasons.append(li);
      }
      const foot = document.createElement("p");
      foot.className = "muted";
      foot.textContent = `${v.steps?.length || 0} agent steps · investigation ${v.investigation_id}: open the SafeShelf Lab → Investigation trace to see each step, model and cost. ${v.label || ""}`;
      out.append(box, summary, reasons, foot);
      now.textContent = `Done: ${box.textContent}`;
      // The Research Agent: a browser on SafeShelf's server searches official recall sites for this model.
      if (v.product_id && !v.research) { // recall sites not searched yet (e.g. no Research Agent on this server)
        const deep = document.createElement("button");
        deep.type = "button";
        deep.textContent = "Check official recall sites (1-3 min)";
        const found = document.createElement("div");
        deep.onclick = async () => {
          deep.disabled = true;
          found.textContent = "The Research Agent is searching CPSC, the EU Safety Gate and ACCC…";
          try {
            const res = await agent({ mode: "research", product_id: v.product_id, session_id: sessionId }, 280000);
            found.innerHTML = "";
            const ul = document.createElement("ul");
            for (const src of res.research?.sources || []) {
              const li = document.createElement("li");
              const hits = (src.matches || []).filter((m) => m.covers_this_model !== "no");
              li.textContent = `${src.site}: ${src.status === "blocked" || src.status === "captcha" ? "the site blocked the automated check, so a person needs to look"
                : hits.length ? hits.map((m) => `${m.covers_this_model === "yes" ? "notice names this model" : "may cover it"}: "${m.title}"`).join("; ") : "no notice found for this model"}`;
              for (const m of hits.filter((x) => x.url).slice(0, 2)) {
                const a = document.createElement("a");
                a.href = m.url; a.target = "_blank"; a.rel = "noopener"; a.textContent = " (open)";
                li.append(a);
              }
              ul.append(li);
            }
            const note = document.createElement("p");
            note.className = "muted";
            note.textContent = `${res.research?.seconds ?? "?"} s. ${res.research?.label || ""}`;
            found.append(ul, note);
          } catch (err) { found.textContent = `The Research Agent could not finish: ${err.message}`; }
          deep.disabled = false;
        };
        out.append(deep, found);
      }
    } catch (err) {
      say(`SafeShelf could not finish: ${err.message}`, true);
    }
    stop();
    stopBtn.focus();
  };

  window.__safeshelfInvestigate = investigate;
}
