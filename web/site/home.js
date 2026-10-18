// Home page: the Ask Eddy example questions and the FAQ chat. The rest (menu, product tabs, agent code) is site.js.
(() => {
  const $ = (id) => document.getElementById(id);
  const row = (code, tag, cls, note) => `<div class="r"><code>${code}</code><span class="tag ${cls}">${tag}</span><small>${note}</small></div>`;

  // Homepage-wide motion uses the native cursor and never intercepts input.
  const pageMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)");
  const runningEffects = new Set();
  const play = (element, frames, options) => {
    const animation = element.animate(frames, options);
    runningEffects.add(animation);
    animation.finished.catch(() => {}).finally(() => runningEffects.delete(animation));
    return animation;
  };
  const revealTargets = document.querySelectorAll([
    ".top .logo", ".nav .links", ".nav-end", ".h-hero-grid > div > *",
    ".h-win", ".h-logos > small", ".works > span", ".h-logos > h2", ".wall > li",
    ".h-head > *", ".bento > .cell", ".ask", ".agent > div", ".plan",
    ".plans-note", ".h-faq > div:first-child", ".faq-chat", ".rec",
    ".h-cta > :not(.fly)", ".foot .cols > div", ".foot-bar",
  ].join(","));
  if ("IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      let stagger = 0;
      entries.forEach(({ target, isIntersecting }) => {
        if (!isIntersecting) return;
        revealObserver.unobserve(target);
        if (pageMotion.matches) return;
        play(target, [
          { opacity: 0, translate: "0 20px" },
          { opacity: 1, translate: "0 0" },
        ], { duration: 650, delay: Math.min(stagger++ * 65, 300),
          easing: "cubic-bezier(.22, 1, .36, 1)", fill: "backwards" });
      });
    }, { threshold: .08 });
    revealTargets.forEach((target) => revealObserver.observe(target));
  }

  const cursor = document.createElement("div");
  cursor.className = "home-cursor";
  cursor.setAttribute("aria-hidden", "true");
  const clickLayer = document.createElement("div");
  clickLayer.className = "home-click-layer";
  clickLayer.setAttribute("aria-hidden", "true");
  document.body.append(cursor, clickLayer);
  let cursorFrame = 0, pointerX = 0, pointerY = 0;
  const hideCursor = () => cursor.classList.remove("is-visible");
  document.addEventListener("pointermove", (event) => {
    if (pageMotion.matches || !finePointer.matches || event.pointerType !== "mouse") return;
    pointerX = event.clientX;
    pointerY = event.clientY;
    cursor.classList.add("is-visible");
    cursor.classList.toggle("is-action", !!event.target.closest("a, button, input, textarea, select"));
    if (!cursorFrame) cursorFrame = requestAnimationFrame(() => {
      cursor.style.left = `${pointerX}px`;
      cursor.style.top = `${pointerY}px`;
      cursorFrame = 0;
    });
  }, { passive: true });
  document.addEventListener("pointerleave", hideCursor);
  window.addEventListener("blur", hideCursor);
  document.addEventListener("scroll", hideCursor, { passive: true });

  document.addEventListener("click", (event) => {
    if (pageMotion.matches || event.detail === 0) return;
    // A bounded burst at the actual click point, including links and controls.
    while (clickLayer.childElementCount >= 4) clickLayer.firstElementChild.remove();
    const burst = document.createElement("div");
    burst.className = "home-click-burst";
    burst.style.left = `${event.clientX}px`;
    burst.style.top = `${event.clientY}px`;
    const ring = document.createElement("i");
    ring.className = "home-click-ring";
    burst.append(ring);
    clickLayer.append(burst);
    const ringMotion = play(ring, [
      { transform: "scale(.25)", opacity: .8 },
      { transform: "scale(1.7)", opacity: 0 },
    ], { duration: 620, easing: "ease-out" });
    for (let index = 0; index < 6; index++) {
      const spark = document.createElement("i");
      spark.className = "home-click-spark";
      burst.append(spark);
      const angle = index * Math.PI / 3;
      play(spark, [
        { transform: "translate(0, 0) scale(1)", opacity: .9 },
        { transform: `translate(${Math.cos(angle) * 32}px, ${Math.sin(angle) * 32}px) scale(0)`, opacity: 0 },
      ], { duration: 480, easing: "cubic-bezier(.16, 1, .3, 1)" });
    }
    ringMotion.finished.catch(() => {}).finally(() => burst.remove());
    const control = event.target.closest("button, .btn");
    if (control && !control.classList.contains("motion-replay")) {
      play(control, [{ scale: "1" }, { scale: ".96", offset: .3 }, { scale: "1" }],
        { duration: 260, easing: "ease-out" });
    }
  });
  pageMotion.addEventListener("change", () => {
    hideCursor();
    if (pageMotion.matches) {
      runningEffects.forEach((animation) => animation.cancel());
      clickLayer.replaceChildren();
    }
  });
  finePointer.addEventListener("change", hideCursor);

  // Decorative demos keep their sample data intact and run only while visible.
  const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
  const cards = [...document.querySelectorAll(".bento > .cell")];
  cards.forEach((card) => {
    card.querySelectorAll(".funnel p, .tl p, .recent p, .rings > div, .hist i, .copies p")
      .forEach((item, index) => item.style.setProperty("--step", index));
    const graphic = card.querySelector(".cell-b");
    const replay = document.createElement("button");
    replay.type = "button";
    replay.className = "motion-replay";
    replay.setAttribute("aria-label", `Replay ${card.querySelector(".cell-h b").textContent} animation`);
    const cue = document.createElement("span");
    cue.className = "motion-replay-cue";
    cue.textContent = "↻ Replay";
    replay.append(cue);
    graphic.append(replay);
    replay.addEventListener("click", (event) => {
      if (motionPreference.matches) return;
      // Restart only the CSS demo loops, leaving the interaction feedback alone.
      card.getAnimations({ subtree: true }).forEach((animation) => {
        if (animation instanceof CSSAnimation) animation.currentTime = 0;
      });
      replay.querySelectorAll(".motion-ripple").forEach((ripple) => ripple.remove());
      const bounds = replay.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "motion-ripple";
      ripple.style.left = `${event.detail ? event.clientX - bounds.left : bounds.width / 2}px`;
      ripple.style.top = `${event.detail ? event.clientY - bounds.top : bounds.height / 2}px`;
      replay.append(ripple);
      const feedback = ripple.animate([
        { transform: "translate(-50%, -50%) scale(.2)", opacity: .65 },
        { transform: "translate(-50%, -50%) scale(3)", opacity: 0 },
      ], { duration: 650, easing: "ease-out" });
      feedback.onfinish = () => ripple.remove();
    });
  });
  if ("IntersectionObserver" in window) {
    const visibleCards = new Set();
    const syncMotion = () => cards.forEach((card) => {
      card.classList.toggle("motion-demo", !motionPreference.matches);
      card.classList.toggle("motion-running", visibleCards.has(card) && !document.hidden);
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(({ target, isIntersecting }) => {
        if (isIntersecting) visibleCards.add(target);
        else visibleCards.delete(target);
      });
      syncMotion();
    }, { threshold: 0.15 });
    cards.forEach((card) => observer.observe(card));
    motionPreference.addEventListener("change", syncMotion);
    document.addEventListener("visibilitychange", syncMotion);
    syncMotion();
  }

  // Ask Eddy: each example question swaps the answer and the records behind it
  const ASK = {
    child: { q: "Is this charger safe for my child's room?", lang: "English", ids: "EV-201 · EV-207",
      a: "<b>Not yet.</b> 9 reports of the USB-C port overheating are under review. Keep it out of children's reach until the review is done.",
      rows: [row("EV-201 · review photo", "REVIEW", "warn", "USB-C port overheating, buyer photo"), row("EV-207 · 9 reports", "REVIEW", "warn", "heat reports from separate buyers"), row("Recalls · 8 regions", "NONE", "ok", "no recall for this exact model")] },
    seller: { q: "Is the seller authorised?", lang: "English", ids: "EV-114",
      a: "<b>No.</b> MegaDealz24 is not on the brand's list of sellers, and the shop opened 19 days ago. The photos are copied from the official listing.",
      rows: [row("EV-114 · brand seller list", "FLAG", "flag", "MegaDealz24 not listed"), row("website_age", "FLAG", "flag", "registered 19 days ago"), row("copied_photos", "FLAG", "flag", "matches the official listing")] },
    hindi: { q: "विक्रेता अधिकृत है?", lang: "हिन्दी", ids: "EV-114",
      a: "<b>नहीं।</b> MegaDealz24 ब्रांड की विक्रेता सूची में नहीं है, और यह दुकान 19 दिन पहले खुली है।",
      rows: [row("EV-114 · brand seller list", "FLAG", "flag", "MegaDealz24 not listed"), row("website_age", "FLAG", "flag", "registered 19 days ago"), row("translation", "MACHINE", "warn", "Gemini, polite form; the record stays in English")] },
    safer: { q: "Is there a safer one?", lang: "English", ids: "EV-207",
      a: "<b>Same model, safer seller:</b> Appario Retail sells the genuine CX-65 at ₹1,349. The 9 heat reports apply to every CX-65, so watch the review either way.",
      rows: [row("Appario Retail · ₹1,349", "EXACT", "ok", "verified seller, same model number"), row("price", "OK", "ok", "in line with the genuine price"), row("EV-207 · 9 reports", "REVIEW", "warn", "applies to the model, not the seller")] },
  };
  const chips = [...document.querySelectorAll("[data-ask]")];
  const ask = $("ask");
  const question = $("ask-q");
  const answer = $("ask-a");
  const evidence = $("ask-rows");
  const tools = ask.querySelector(".ask-tools");
  const who = ask.querySelector(".ask-who span");
  const status = document.createElement("span");
  status.className = "ask-motion-status";
  status.setAttribute("role", "status");
  ask.append(status);
  let conversation = 0, selectedQuestion = "child", started = false;
  const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const segmenter = typeof Intl.Segmenter === "function"
    ? new Intl.Segmenter(undefined, { granularity: "grapheme" }) : null;
  const letters = (text) => segmenter ? [...segmenter.segment(text)].map((part) => part.segment) : Array.from(text);
  const renderConversation = (key) => {
    const d = ASK[key];
    chips.forEach((chip) => chip.setAttribute("aria-pressed", String(chip.dataset.ask === key)));
    question.textContent = d.q;
    question.lang = d.lang === "हिन्दी" ? "hi" : "en";
    answer.innerHTML = d.a;
    answer.lang = question.lang;
    $("ask-lang").textContent = d.lang;
    $("ask-ev-ids").textContent = d.ids;
    $("ask-ev-n").textContent = `${d.rows.length} records`;
    evidence.innerHTML = d.rows.join("");
    who.innerHTML = "<b>Eddy</b> · answered from 3 records";
    ask.classList.remove("ask-composing", "ask-thinking", "ask-streaming");
    answer.removeAttribute("aria-busy");
    [question, answer].forEach((element) => element.style.removeProperty("min-height"));
  };
  // Stream text nodes so emphasis and Hindi grapheme clusters remain intact.
  const typeText = async (element, token, duration) => {
    element.style.minHeight = `${element.getBoundingClientRect().height}px`;
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push({ node: walker.currentNode, chars: letters(walker.currentNode.textContent) });
    const total = nodes.reduce((count, item) => count + item.chars.length, 0);
    nodes.forEach(({ node }) => node.textContent = "");
    const began = performance.now();
    while (token === conversation) {
      let remaining = Math.ceil(Math.min(1, (performance.now() - began) / duration) * total);
      nodes.forEach(({ node, chars }) => {
        node.textContent = chars.slice(0, Math.max(0, remaining)).join("");
        remaining -= chars.length;
      });
      if (performance.now() - began >= duration) return;
      await pause(30);
    }
  };
  const runConversation = async (key) => {
    started = true;
    selectedQuestion = key;
    const token = ++conversation;
    renderConversation(key);
    if (pageMotion.matches || document.hidden) return;
    answer.setAttribute("aria-busy", "true");
    status.textContent = "Playing example conversation";
    ask.classList.add("ask-composing");
    await typeText(question, token, 1100);
    if (token !== conversation) return;
    ask.classList.remove("ask-composing");
    ask.classList.add("ask-thinking");
    who.innerHTML = '<b>Eddy</b> · checking the records <i class="ask-typing-dots" aria-hidden="true"><i></i><i></i><i></i></i>';
    await pause(900);
    if (token !== conversation) return;
    ask.classList.remove("ask-thinking");
    ask.classList.add("ask-streaming");
    who.innerHTML = "<b>Eddy</b> · writing a response";
    await typeText(answer, token, 2200);
    if (token !== conversation) return;
    renderConversation(key);
    status.textContent = "Example response complete. Three evidence records shown.";
    evidence.querySelectorAll(".r").forEach((record, index) => play(record, [
      { opacity: 0, translate: "0 10px" }, { opacity: 1, translate: "0 0" },
    ], { duration: 400, delay: index * 140, fill: "backwards", easing: "ease-out" }));
    play(tools, [{ opacity: 0 }, { opacity: 1 }], { duration: 350 });
  };
  chips.forEach((chip) => chip.addEventListener("click", () => runConversation(chip.dataset.ask)));
  if ("IntersectionObserver" in window) {
    const conversationObserver = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      if (!started) runConversation(selectedQuestion);
      conversationObserver.disconnect();
    }, { threshold: .35 });
    conversationObserver.observe(ask);
  }
  const settleConversation = () => {
    ++conversation;
    renderConversation(selectedQuestion);
    status.textContent = "";
  };
  pageMotion.addEventListener("change", () => { if (pageMotion.matches) settleConversation(); });
  document.addEventListener("visibilitychange", () => { if (document.hidden) settleConversation(); });

  // FAQ: a question pill posts the question and Eddy's answer into the chat
  const log = $("faq-log");
  const qs = [...document.querySelectorAll("#faq-qs button")];
  qs.forEach((b) => b.addEventListener("click", () => {
    const [q, a] = b.dataset.a.split("|");
    qs.forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
    log.innerHTML = `<p class="bubble me ask-fade"></p><p class="bubble bot ask-fade">${a}</p>`;
    log.firstChild.textContent = q;
  }));
  // Ask Eddy bar under the hero: a real form that opens the chat with the question and the answer language
  // (chat.html?q=…&lang=…). The language starts at the shopper's last pick on the chat page.
  const hcForm = $("hcForm"), hcQ = $("hcQ"), hcLang = $("hcLang");
  if (hcForm) {
    try { const saved = localStorage.getItem("safeshelf-lang"); if (saved && [...hcLang.options].some((o) => o.value === saved)) hcLang.value = saved; } catch (_) { /* storage off */ }
    const grow = () => { hcQ.style.height = "auto"; hcQ.style.height = `${Math.min(hcQ.scrollHeight, 160)}px`; };
    hcQ.addEventListener("input", grow);
    hcQ.addEventListener("keydown", (e) => { // Enter sends; Shift+Enter is a new line; never while an IME is composing
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); hcForm.requestSubmit(); }
    });
    hcForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = hcQ.value.trim();
      try { localStorage.setItem("safeshelf-lang", hcLang.value); } catch (_) { /* storage off */ }
      location.href = q ? `chat.html?${new URLSearchParams({ q, lang: hcLang.value })}` : "chat.html";
    });
    // Mic: dictate the question in the picked language, where the browser can
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const mic = $("hcMic");
    if (Recognition) {
      mic.hidden = false;
      let rec = null;
      mic.onclick = () => {
        if (rec) { rec.stop(); return; }
        rec = new Recognition();
        rec.lang = hcLang.value === "en" ? "en-IN" : hcLang.value.replace("zh-Hans", "zh-CN").replace("zh-Hant", "zh-TW");
        rec.interimResults = true;
        const before = hcQ.value ? `${hcQ.value.trimEnd()} ` : "";
        rec.onresult = (ev) => { hcQ.value = before + [...ev.results].map((r) => r[0].transcript).join(""); grow(); };
        rec.onend = () => { rec = null; mic.classList.remove("on"); hcQ.focus(); };
        mic.classList.add("on");
        rec.start();
      };
    }
  }
})();
