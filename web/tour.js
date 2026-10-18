// Eddy's tour of the judges' page: a centred card with one slide per feature. Each slide has Eddy (the mascot, cut from
// the brand sheet into site/assets/guide/) in a pose that fits, a big title, one line, and a moving picture of the
// feature with a cursor using it. "Show me on the page" closes the card, opens the right Try it tab and lights up that
// part of the page. The last slide takes a product name and puts it into Paste a listing for the real live check.
// Navigation: Back / Next, clickable dots, arrow keys, swipe, Esc. It opens once by itself after sign-in (remembered
// on this browser; ?notour turns that off) and any time from Eddy's button at the bottom right. Slides for parts the
// chosen view hides (roles.js) are left out. Plain module, no build step; the pictures are fixed markup.

const KEY = "safeshelf-tour-seen";
const POSE = (name) => `site/assets/guide/eddy-${name}.webp`;
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const $id = (id) => document.getElementById(id);
const SHIELD = `<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M4 8a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v8c0 7-5.5 12-12 14C9.5 28 4 23 4 16z" fill="#0271E4"/><path d="m10.5 16 4 4 7-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const HAND = `<svg class="tg-hand" viewBox="0 0 24 28" aria-hidden="true"><path d="M8.5 13V4.2a1.8 1.8 0 0 1 3.6 0V12l.1-1.6a1.8 1.8 0 0 1 3.5.2l.1 1.6.2-1a1.7 1.7 0 0 1 3.4.3l.1 1.3a1.7 1.7 0 0 1 3.3.5v5.2c0 4.2-2.9 7.5-7 7.5h-1.6c-2.4 0-4.2-1-5.6-3l-4-5.6a1.8 1.8 0 0 1 2.8-2.2z" fill="#fff" stroke="#001123" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
const BAR = (url) => `<div class="tm-bar"><span class="tm-lights"><i></i><i></i><i></i></span><span class="tm-url">${url}</span></div>`;

// the shop-page tab shows two choices first (app.js); the test browser is the one to point at
const toTestPages = () => { if ($id("shop-page")?.dataset.mode === "choose") $id("test-start")?.click(); };
// the tour shows the real tool, not its preview card (app.js)
const openTab = (id) => { const t = $id(`tab-${id}`); if (t && t.getAttribute("aria-selected") !== "true") t.click(); const p = $id(id); if (p?.dataset.view) p.dataset.view = "live"; };
const setField = (form, name, value) => { const f = form?.elements[name]; if (f) { f.value = value; f.dispatchEvent(new Event("input", { bubbles: true })); } };

const SLIDES = [
  { id: "hello", pose: "hi", title: "Meet Eddy, your safety wingman", text: "Take a quick tour of SafeShelf: it tells you if a product is safe and real before you pay, with the proof.",
    art: `<div class="tm-hello">
      <div class="tm-win">${BAR("amazon.co.jp/dp/W5PRO")}
        <div class="tm-shop"><span class="tm-thumb"></span><span class="tm-lines"><b>HAIARA W5PRO 10000mAh</b><i>¥2,980</i><em>Add to cart</em></span></div>
        <div class="tm-panel"><span class="tm-brand">${SHIELD}SafeShelf</span><div class="tm-verdict red"><b>Don't buy</b><small>Recalled in Japan for a fire risk</small></div><span class="tm-proof">CAA notice · exact model W5PRO</span></div>
      </div>
      <ul class="tm-facts"><li><b>8,689</b>official recalls</li><li><b>29,379</b>buyer reviews</li><li><b>26</b>languages</li></ul>
    </div>` },
  { id: "views", pose: "curious", target: "#for", title: "Pick who you are", text: "Shopper, marketplace, regulator or developer: the page keeps only the parts for you, and tells the same story your way.",
    art: `<div class="tm-views">${[["shopper", "Shopper"], ["marketplace", "Marketplace"], ["regulator", "Regulator"], ["developer", "Developer"]]
      .map(([v, l]) => `<span class="tm-view${v === "marketplace" ? " pick" : ""}"><img src="site/assets/eddy-${v}.png" alt=""><b>${l}</b></span>`).join("")}</div>${HAND}` },
  { id: "shop", pose: "pointing", tab: "shop-page", prep: toTestPages, target: "#shop-page .win", title: "Check right on the shop page", text: "Open a test shop page, or paste any product link, then press the shield. The answer opens beside the listing.",
    art: `<div class="tm-browser"><div class="tm-win">${BAR("example-deals-store.test")}<span class="tm-ext">${SHIELD}</span>
      <div class="tm-shop"><span class="tm-thumb b"></span><span class="tm-lines"><b>Kelvo CX-65 65W charger</b><i>₹299</i><em>Buy now</em></span></div>
      <div class="tm-panel slide"><span class="tm-brand">${SHIELD}SafeShelf</span><div class="tm-verdict red"><b>Don't buy</b><small>Not real: a fifth of the genuine price</small></div><span class="tm-proof">Photos copied from the official listing</span></div>
    </div></div>${HAND}` },
  { id: "chat", pose: "happy", tab: "chat", target: "#chat .chatwin", title: "Or just ask Eddy", text: "The real chat: pick a product or paste any link or screenshot, then ask in your own words. It remembers the conversation and shows its sources.",
    art: `<div class="tm-talk solo"><div class="tm-phone wa chat"><span class="tm-wahead">${SHIELD}Eddy · SafeShelf</span><span class="tm-msg me">Is this charger safe in a child's room?</span><span class="tm-msg bot"><b class="amber">Be careful</b>Buyers report it overheating.</span><span class="tm-msg bot">Sources: 3 buyer reviews · BIS registry</span></div></div>` },
  { id: "paste", pose: "excited", tab: "check-own", target: "#check-own", title: "Paste any listing, watch it think", text: "Copy a title from any shop. Eight agents check it live while you watch, then you get the answer.",
    art: `<div class="tm-paste">
      <div class="tm-form"><small>Product title</small><span class="tm-field"><span class="tm-typed">Anker PowerCore 10000 A1263</span></span><span class="tm-go">Check it live</span></div>
      <ol class="tm-agents"><li>Page reader</li><li>Is it real?</li><li>Safety Radar</li><li>Recall checker</li><li>Safety marks</li><li>Verdict, set by code</li></ol>
    </div>${HAND}` },
  { id: "talk", pose: "happy", tab: "ask-out-loud", target: "#ask-out-loud", alt: { tab: "whatsapp", target: "#whatsapp" }, title: "Ask out loud, or on WhatsApp", text: "Point the camera at the label and ask \"Is this safe?\", or forward a link on WhatsApp. Answers come back as a voice note, in 26 languages.",
    art: `<div class="tm-talk">
      <div class="tm-phone"><span class="tm-mic"><i></i></span><b>“Is this safe?”</b><small>Listening… हिन्दी · 日本語 · English</small></div>
      <div class="tm-phone wa"><span class="tm-wahead">SafeShelf</span><span class="tm-msg me">flipkart.com/kelvo-cx65…</span><span class="tm-msg bot"><b>⛔ Don't buy</b>Not the real product.</span><span class="tm-msg bot voice"><i></i>0:12</span></div>
    </div>` },
  { id: "answers", pose: "thinking", target: "#answers", title: "One clear answer, with proof", text: "Every listing gets one of four answers. Plain code picks the colour from the evidence; Gemini only explains it.",
    art: `<div class="tm-answers">
      <div class="tm-checks"><span>Official recalls</span><span>Buyer reviews</span><span>Safety marks</span><span>Is it real?</span></div>
      <ul class="tm-ans"><li class="red"><b>Don't buy</b>recalled or fake</li><li class="amber"><b>Be careful</b>reports under review</li><li class="green"><b>No problems found</b>in what was checked</li><li class="grey"><b>Can't tell yet</b>never a guess</li></ul>
    </div>` },
  { id: "proof", pose: "surprised", target: "#accuracy", alt: { target: "#attack" }, title: "Tested, and attacked on purpose", text: "Only 2 false alarms in 40 safe products, against 6 for Gemini alone. We also tried to fool it; see what it decided.",
    art: `<div class="tm-proof2">
      <div class="tm-bars"><small>False alarms out of 40</small><div><span>SafeShelf</span><i class="me" style="--w:18%"></i><b>2</b></div><div><span>Gemini alone</span><i style="--w:55%"></i><b>6</b></div><div><span>Keyword rules</span><i style="--w:100%"></i><b>11</b></div></div>
      <ul class="tm-attacks"><li>Fake regulator page</li><li>Look-alike model number</li><li>Hidden text aimed at AI</li></ul>
    </div>` },
  { id: "anywhere", pose: "flying", target: "#products", title: "Use it anywhere", text: "A Chrome extension, this web page, WhatsApp, catalog scans for marketplaces, and an API with 10 MCP tools for AI agents.",
    art: `<div class="tm-prods">${[["#0271e4", "Chrome extension"], ["#f0a020", "Web page"], ["#1d9b52", "WhatsApp"], ["#7b5cd6", "Catalog scan"], ["#001123", "API · MCP"]]
      .map(([c, l]) => `<span style="--c:${c}"><i></i>${l}</span>`).join("")}</div>` },
  { id: "go", pose: "waving", title: "Your turn", text: "Name a product and Eddy will set up a live check, or close this and explore. Eddy is at the bottom right if you need him.",
    art: `<form class="tm-try" autocomplete="off"><img src="${POSE("thumbs")}" alt=""><label class="sr" for="tg-product">A product to check</label><input id="tg-product" type="text" maxlength="200" placeholder="e.g. Anker PowerCore 10000 A1263"><button type="submit" class="primary">Set up the check</button></form>` },
];

const store = {
  get: () => { try { return localStorage.getItem(KEY); } catch (_) { return "1"; } }, // no storage: never open by itself
  set: () => { try { localStorage.setItem(KEY, "1"); } catch (_) { /* private window */ } },
};

// Where a slide points on the page, for the chosen view (roles.js hides the rest): its own part, or its fallback.
function placeOf(slide) {
  for (const p of [slide, slide.alt].filter(Boolean)) {
    if (!p.target) continue;
    const el = document.querySelector(p.target);
    if (!el) continue;
    if (p.tab) { const t = $id(`tab-${p.tab}`); if (t && !t.hidden && !$id("try")?.hidden) return { ...p, prep: slide.prep, el }; continue; }
    if (!el.closest("[hidden]")) return { ...p, el };
  }
  return null;
}
const wanted = (s) => !s.target || placeOf(s);

export function setUpTour() {
  for (const p of new Set(SLIDES.map((s) => s.pose))) { const i = new Image(); i.src = POSE(p); }

  // Eddy's button, bottom right, with a "Need a hand?" bubble until he has been met
  const launch = document.createElement("button");
  launch.type = "button";
  launch.className = "tg-launch";
  launch.setAttribute("aria-label", "Take the tour with Eddy");
  launch.innerHTML = `<span class="tg-hint" aria-hidden="true">Hi! Need a hand?</span><img src="${POSE("hi")}" alt="" width="68" height="68">`;
  if (!store.get()) launch.classList.add("fresh");
  document.body.append(launch);

  const wrap = document.createElement("div");
  wrap.className = "tg-modal";
  wrap.hidden = true;
  wrap.innerHTML = `<div class="tg-card" role="dialog" aria-modal="true" aria-labelledby="tg-title" aria-describedby="tg-text">
      <button type="button" class="tg-x" aria-label="Close the tour">×</button>
      <img class="tg-eddy" alt="" src="${POSE("hi")}">
      <h2 id="tg-title"></h2>
      <p id="tg-text"></p>
      <div class="tg-art" aria-hidden="true"><div class="tg-stage"></div></div>
      <button type="button" class="tg-show">Show me on the page <span aria-hidden="true">→</span></button>
      <div class="tg-foot">
        <button type="button" class="tg-back">Back</button>
        <span class="tg-dots" role="tablist" aria-label="Tour slides"></span>
        <button type="button" class="tg-next"></button>
      </div>
    </div>`;
  document.body.append(wrap);

  const q = (sel) => wrap.querySelector(sel);
  const card = q(".tg-card");
  const art = q(".tg-art");
  const stage = q(".tg-stage");
  let slides = [];
  let at = 0;
  let lastFocus = null;

  // the pictures are drawn at 520 × 270 and scaled to fit the card
  const fit = () => { stage.style.transform = `scale(${Math.min(1, art.clientWidth / 520)})`; art.style.height = `${270 * Math.min(1, art.clientWidth / 520)}px`; };

  function show(i) {
    at = Math.max(0, Math.min(i, slides.length - 1));
    const s = slides[at];
    const eddy = q(".tg-eddy");
    eddy.src = POSE(s.pose);
    q("#tg-title").textContent = s.title;
    q("#tg-text").textContent = s.text;
    stage.innerHTML = s.art;
    stage.dataset.slide = s.id;
    q(".tg-show").hidden = !s.target;
    q(".tg-back").textContent = at === 0 ? "Skip" : "Back";
    q(".tg-next").textContent = at === 0 ? "Take the tour" : at === slides.length - 1 ? "Done" : "Next";
    q(".tg-dots").replaceChildren(...slides.map((sl, j) => {
      const d = document.createElement("button");
      d.type = "button";
      d.setAttribute("role", "tab");
      d.setAttribute("aria-label", `${j + 1} of ${slides.length}: ${sl.title}`);
      d.setAttribute("aria-selected", String(j === at));
      d.onclick = () => show(j);
      return d;
    }));
    card.classList.remove("in");
    void card.offsetWidth; // restart the entrance and the picture's motion
    card.classList.add("in");
    fit();
    const form = stage.querySelector(".tm-try");
    art.setAttribute("aria-hidden", String(!form)); // only the last slide's picture is something to use
    if (form) form.onsubmit = (e) => { e.preventDefault(); tryProduct(form.elements[0].value.trim()); };
  }

  function open() {
    slides = SLIDES.filter(wanted);
    lastFocus = document.activeElement;
    store.set();
    launch.classList.remove("fresh");
    launch.hidden = true;
    wrap.hidden = false;
    document.documentElement.classList.add("tg-on");
    show(0);
    q(".tg-next").focus({ preventScroll: true });
  }

  function close(refocus = true) {
    wrap.hidden = true;
    launch.hidden = false;
    document.documentElement.classList.remove("tg-on");
    if (refocus) lastFocus?.focus?.({ preventScroll: true });
  }

  // close the card, open the right tab, and light up that part of the page for a moment
  function showOnPage(slide) {
    const p = placeOf(slide);
    if (!p) return;
    close(false);
    if (p.tab) openTab(p.tab);
    p.prep?.();
    const el = document.querySelector(p.target);
    if (!el) return;
    el.scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: el.offsetHeight > innerHeight * .7 ? "start" : "center" });
    el.classList.remove("tg-lit"); void el.offsetWidth; el.classList.add("tg-lit");
    setTimeout(() => el.classList.remove("tg-lit"), 2600);
  }

  // the last slide: put the product into Paste a listing, ready for the live check (the person presses it)
  function tryProduct(name) {
    const form = $id("own");
    if (!form || $id("tab-check-own")?.hidden) return close();
    close(false);
    openTab("check-own");
    if (name) setField(form, "title", name);
    form.scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "center" });
    form.classList.add("tg-lit");
    setTimeout(() => form.classList.remove("tg-lit"), 2600);
    (name ? form.querySelector("button[type=submit]") : form.elements.title)?.focus({ preventScroll: true });
  }

  launch.addEventListener("click", open);
  q(".tg-x").addEventListener("click", () => close());
  q(".tg-back").addEventListener("click", () => (at === 0 ? close() : show(at - 1)));
  q(".tg-next").addEventListener("click", () => (at < slides.length - 1 ? show(at + 1) : close()));
  q(".tg-show").addEventListener("click", () => showOnPage(slides[at]));
  wrap.addEventListener("click", (e) => { if (e.target === wrap) close(); });
  wrap.addEventListener("keydown", (e) => {
    if (e.key === "Escape") return close();
    if (e.target.matches?.("input")) return;
    if (e.key === "ArrowRight" && at < slides.length - 1) show(at + 1);
    else if (e.key === "ArrowLeft" && at > 0) show(at - 1);
    else if (e.key === "Tab") { // keep focus inside the card
      const f = [...card.querySelectorAll("button:not([hidden]), input")].filter((b) => b.offsetParent);
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f.at(-1).focus(); }
      else if (!e.shiftKey && document.activeElement === f.at(-1)) { e.preventDefault(); f[0].focus(); }
    }
  });
  let x0 = null; // swipe left / right on touch screens
  card.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  card.addEventListener("touchend", (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) > 50) show(at + (dx < 0 ? 1 : -1));
  });
  window.addEventListener("resize", () => { if (!wrap.hidden) fit(); });

  // first visit on this browser: open by itself once the page has drawn its views
  if (!store.get() && !new URLSearchParams(location.search).has("notour")) setTimeout(open, 1200);
  return { open };
}
