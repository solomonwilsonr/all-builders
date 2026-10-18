// Before and after purchase, for the check card (content.js). Loaded as a normal script before content.js;
// exposes globalThis.SafeShelfAftercare. Everything it says comes from the check's code-set outcome.
//   speakPlain(plain)   voice mode: the verdict read aloud in the chat language (POST /v1/voice/verdict), short
//   autoSpeak(r)        speaks each new answer when "Speak every answer" is on
//   voiceToggle(el)     that switch, remembered
//   guardBuy(r, level)  a red or amber answer steps in when the shopper clicks Buy now / Add to cart: why, and a choice
//   afterPanel(el, r, page)  "I already bought it": steps, refund and regulator drafts, case file (POST /v1/after-purchase)
//   badge(el, b)        "Checked by code, not guessed", linked to the official record
(() => {
  // Same codes and locales as LANGS in content.js and engine/voice.py.
  const LOCALES = { en: "en-IN", hi: "hi-IN", bn: "bn-IN", mr: "mr-IN", te: "te-IN", ta: "ta-IN", gu: "gu-IN", ur: "ur-IN", kn: "kn-IN", or: "or-IN",
    ml: "ml-IN", pa: "pa-IN", ne: "ne-NP", si: "si-LK", ja: "ja-JP", ko: "ko-KR", "zh-Hans": "zh-CN", "zh-Hant": "zh-TW", id: "id-ID", ms: "ms-MY",
    th: "th-TH", vi: "vi-VN", fil: "fil-PH", my: "my-MM", km: "km-KH", lo: "lo-LA" };
  const store = {
    async get(key, fallback) { try { const v = (await chrome.storage.local.get(key))[key]; return v ?? fallback; } catch (_) { return fallback; } },
    async set(key, value) { try { await chrome.storage.local.set({ [key]: value }); } catch (_) { /* storage unavailable */ } },
  };
  const call = (op, args) => new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendMessage({ type: "safeshelf:call", op, args }, (res) => {
        if (!res?.ok) return reject(new Error(res?.error || chrome.runtime.lastError?.message || "no answer"));
        if (!res.result?.live) return reject(new Error("not available on this server yet"));
        resolve(res.result.data);
      });
    } catch (_) { reject(new Error("The extension was reloaded. Please refresh the page.")); }
  });

  const say = (text, locale) => {
    const base = locale.split("-")[0];
    const voices = speechSynthesis.getVoices();
    const voice = voices.find((v) => v.lang.replace("_", "-").toLowerCase() === locale.toLowerCase()) || voices.find((v) => v.lang.toLowerCase().startsWith(base));
    if (!voice && base !== "en" && voices.length) return false; // an English voice would read nonsense
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = locale;
    if (voice) u.voice = voice;
    u.rate = 0.95;
    speechSynthesis.speak(u);
    return true;
  };

  // Returns what was (or would have been) said, so the card can show it too.
  const speakPlain = async (plain) => {
    const lang = await store.get("chatLang", "en");
    const english = plain.say || `${plain.title}. ${plain.why || ""}`;
    let text = english, locale = LOCALES.en;
    if (lang !== "en" && LOCALES[lang]) {
      try { const v = await call("voice", { plain, language: lang }); text = v.text; locale = v.speech_locale; } catch (_) { /* English line instead */ }
    }
    return { text, spoken: say(text, locale) };
  };

  const autoSpeak = async (r) => { if (r?.outcome?.plain && await store.get("voiceMode", false)) speakPlain(r.outcome.plain); };

  const voiceToggle = (el) => {
    const box = el("input", { type: "checkbox" });
    store.get("voiceMode", false).then((on) => { box.checked = on; });
    box.onchange = () => store.set("voiceMode", box.checked);
    return el("label", { className: "voicetoggle", title: "Read every answer aloud, in your chat language" }, box, " Speak every answer");
  };

  const badge = (el, b) => {
    if (!b) return null;
    const text = `⚙ ${b.text || "Checked by code, not guessed"}`;
    return b.link?.url && /^https:/.test(b.link.url)
      ? el("a", { className: "codebadge", href: b.link.url, target: "_blank", rel: "noopener", title: `Official source: ${b.link.label}`, textContent: text })
      : el("span", { className: "codebadge", title: "Set by matching rules in code, not written by AI", textContent: text });
  };

  // --- Interrupt the buy click on a red or amber answer ---
  const BUY = /^(buy now|add to (cart|basket|bag)|buy with 1-click|place (your )?order|proceed to (buy|checkout)|今すぐ買う|カートに入れる|अभी खरीदें|कार्ट में जोड़ें)$/i;
  const BUY_SELECTORS = "#buy-now-button, #add-to-cart-button, input[name='submit.buy-now'], input[name='submit.add-to-cart'], #one-click-button";
  const guard = { r: null, level: null, allowUntil: 0, installed: false };
  const buyTarget = (node) => {
    const hit = node?.closest?.(BUY_SELECTORS);
    if (hit) return hit;
    const b = node?.closest?.("button, a, input[type=submit], input[type=button], [role=button]");
    const words = (b?.innerText || b?.value || b?.getAttribute?.("aria-label") || "").trim().replace(/\s+/g, " ");
    return b && words.length < 40 && BUY.test(words) ? b : null;
  };
  const modal = (r, onBuy) => {
    const plain = r.outcome?.plain || {};
    const host = document.createElement("div");
    const root = host.attachShadow({ mode: "open" });
    const red = guard.level === "red";
    const css = `:host{all:initial} .bg{position:fixed;inset:0;background:rgba(0,17,35,.45);z-index:2147483647;display:grid;place-items:center;font:16px/1.5 "Helvetica Neue",Helvetica,Arial,system-ui,sans-serif}
      .d{background:#fff;color:#001123;max-width:440px;margin:16px;border-radius:14px;border-top:4px solid ${red ? "#c93a2f" : "#f0a020"};padding:22px;box-shadow:0 24px 60px rgba(0,17,35,.3)}
      h2{margin:0 0 6px;font-size:22px;font-weight:600;letter-spacing:-.02em;color:${red ? "#c93a2f" : "#a35f00"}} p{margin:6px 0} .k{font-size:12px;color:#5d6874}
      .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px} button{font:inherit;font-weight:500;padding:11px 16px;border-radius:4px;border:1.5px solid #e4e7eb;background:#fff;color:#001123;cursor:pointer}
      button.stop{background:#0271e4;color:#fff;border-color:#0271e4}
      button.ghost{font-weight:500;border-color:transparent;background:transparent;color:#5d6874;padding:11px 10px}
      button:focus-visible{outline:2px solid #0271e4;outline-offset:2px}`;
    const stop = Object.assign(document.createElement("button"), { className: "stop", textContent: red ? "Don't buy it" : "Go back and check" });
    // On a red (recalled) verdict, "Buy anyway" is a plain text link, not a button of equal weight to "Don't buy it".
    const buy = Object.assign(document.createElement("button"), { className: red ? "ghost" : "", textContent: "Buy anyway" });
    const listen = Object.assign(document.createElement("button"), { textContent: "🔊 Listen" });
    const d = document.createElement("div");
    d.className = "d";
    d.setAttribute("role", "alertdialog");
    d.setAttribute("aria-modal", "true");
    d.setAttribute("aria-labelledby", "t");
    d.innerHTML = `<p class="k">SafeShelf · before you buy</p><h2 id="t"></h2><p class="why"></p><p class="todo"></p><div class="row"></div><p class="k">Checked by code against official recall lists. Your choice: SafeShelf never blocks a purchase.</p>`;
    // Matches the card's own severity wording (VERDICT_WORD in content.js) so the two never disagree on the same verdict.
    d.querySelector("h2").textContent = plain.title || (red ? "Don't buy — a safety problem was found" : "Be careful — check this before buying");
    d.querySelector(".why").textContent = plain.why || r.summary || "";
    d.querySelector(".todo").textContent = plain.todo || "";
    d.querySelector(".row").append(stop, buy, listen);
    const bg = document.createElement("div");
    bg.className = "bg";
    bg.append(d);
    root.append(Object.assign(document.createElement("style"), { textContent: css }), bg);
    const close = () => { speechSynthesis.cancel(); host.remove(); document.removeEventListener("keydown", esc, true); };
    const esc = (e) => { if (e.key === "Escape") { e.stopPropagation(); close(); } };
    stop.onclick = close;
    buy.onclick = () => { close(); onBuy(); };
    listen.onclick = () => speakPlain(plain);
    document.addEventListener("keydown", esc, true);
    document.documentElement.append(host);
    stop.focus();
    autoSpeak(r);
  };
  const onClick = (e) => {
    if (!guard.r || !["red", "amber"].includes(guard.level) || Date.now() < guard.allowUntil) return;
    const target = buyTarget(e.target);
    if (!target) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    modal(guard.r, () => { guard.allowUntil = Date.now() + 60000; target.click(); });
  };
  const guardBuy = (r, level) => {
    guard.r = r;
    guard.level = level;
    if (!guard.installed) { document.addEventListener("click", onClick, true); guard.installed = true; }
  };
  const unguard = () => { document.removeEventListener("click", onClick, true); guard.installed = false; };

  // --- I already bought it ---
  const afterPanel = (el, r, page) => {
    const out = el("div");
    const btn = el("button", { type: "button", className: "small", textContent: "I already bought it: what now?" });
    btn.onclick = async () => {
      btn.disabled = true;
      btn.textContent = "Writing your steps and drafts…";
      try {
        const a = await call("afterPurchase", { body: { investigation_id: r.outcome?.investigation_id, product_id: r.product_id || undefined, url: page.url, title: page.title, brand: page.brand,
          model: page.model, currency: page.currency, page_text: page.page_text, reviews: (page.reviews || []).slice(0, 60),
          purchase: { url: page.url } } });
        const draft = (d) => {
          const ta = el("textarea", { className: "draft", rows: 7, value: d.body });
          ta.setAttribute("aria-label", `${d.subject} (editable)`);
          const copy = el("button", { type: "button", className: "small", textContent: "Copy" });
          copy.onclick = async () => { try { await navigator.clipboard.writeText(ta.value); copy.textContent = "Copied ✓"; } catch (_) { ta.select(); copy.textContent = "Selected: copy it"; } };
          const ja = d.translations?.ja ? el("button", { type: "button", className: "small", textContent: "日本語" }) : null;
          if (ja) ja.onclick = () => { ta.value = d.translations.ja.body; };
          return el("div", { className: "draftbox" }, el("strong", { textContent: d.kind === "refund_request" ? `Refund request to ${d.to}` : `Report to ${d.to}` }),
            ...(d.how || []).map((h) => el("div", { className: "note", textContent: h })), ta, el("div", { className: "tools" }, ...[copy, ja].filter(Boolean)),
            el("div", { className: "note", textContent: d.status }));
        };
        const dl = el("button", { type: "button", className: "small", textContent: "Download the case file" });
        dl.onclick = () => {
          const a2 = el("a", { href: URL.createObjectURL(new Blob([a.case_file.markdown], { type: "text/markdown" })), download: `safeshelf-case-${a.investigation_id || "file"}.md` });
          a2.click();
        };
        out.replaceChildren(el("div", { className: "after" }, el("strong", { textContent: a.headline }),
          el("ol", {}, ...a.steps.map((s) => el("li", {}, el("b", { textContent: s.title }), ` ${s.detail}`,
            ...(s.url ? [" ", el("a", { href: s.url, target: "_blank", rel: "noopener", textContent: "Notice" })] : [])))),
          ...a.drafts.filter((d) => d.body).map(draft), el("div", { className: "tools" }, dl),
          el("div", { className: "note", textContent: a.label })));
        btn.remove();
        if (await store.get("voiceMode", false)) say(a.say, LOCALES.en);
      } catch (err) { btn.disabled = false; btn.textContent = `Couldn't load it (${err.message}). Try again`; }
    };
    return el("div", { className: "aftercare" }, btn, out);
  };

  const STYLE = `
    .codebadge { display:inline-block; margin-left:4px; font-size:10px; font-weight:600; padding:0 6px; border-radius:4px; background:#e8f2fd; color:#0271e4; text-decoration:none; white-space:nowrap; }
    a.codebadge:hover { background:#0271e4; color:#fff; }
    .aftercare { margin:10px 0; }
    .after { display:grid; gap:8px; padding:12px 14px; border-radius:10px; background:#f5f6f7; margin-top:8px; }
    .after ol { margin:0; padding-left:18px; display:grid; gap:4px; }
    .draftbox { display:grid; gap:4px; background:#fff; border-radius:8px; border:1px solid #e4e7eb; padding:8px 10px; }
    .draft { width:100%; box-sizing:border-box; font:12px/1.4 ui-monospace, Menlo, monospace; padding:8px; border:1px solid #e4e7eb; border-radius:4px; }
    .voicetoggle { font-size:13px; display:inline-flex; align-items:center; gap:4px; }`;

  globalThis.SafeShelfAftercare = { speakPlain, autoSpeak, voiceToggle, guardBuy, unguard, afterPanel, badge, buyTarget, STYLE };
})();
