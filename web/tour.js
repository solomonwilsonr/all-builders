// Eddy's tour of the judges' page, one step per part of the page, in the page's order. The first and last steps are a
// centred card with Eddy (the mascot, cut from the brand sheet into site/assets/guide/) and a moving picture; every
// step between is a coachmark: the page scrolls to the real part (opening its Try it tab), a spotlight dims the rest,
// and a small card with an arrow points at it, with Eddy, the dots, Back / Next and "Seen this before? Skip the tour".
// The last step takes a product name and puts it into Paste a listing for the real live check.
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
  { id: "shop", pose: "pointing", tab: "shop-page", prep: toTestPages, target: "#shop-page .win", title: "Check right on the shop page", text: "Open a test shop page, or paste any product link, then press the shield. The answer opens beside the listing.",
    art: `<div class="tm-browser"><div class="tm-win">${BAR("example-deals-store.test")}<span class="tm-ext">${SHIELD}</span>
      <div class="tm-shop"><span class="tm-thumb b"></span><span class="tm-lines"><b>Kelvo CX-65 65W charger</b><i>₹299</i><em>Buy now</em></span></div>
      <div class="tm-panel slide"><span class="tm-brand">${SHIELD}SafeShelf</span><div class="tm-verdict red"><b>Don't buy</b><small>Not real: a fifth of the genuine price</small></div><span class="tm-proof">Photos copied from the official listing</span></div>
    </div></div>${HAND}` },
  { id: "paste", pose: "excited", tab: "check-own", target: "#check-own", title: "Paste any listing, watch it think", text: "Copy a title from any shop. Eight agents check it live while you watch, then you get the answer.",
    art: `<div class="tm-paste">
      <div class="tm-form"><small>Product title</small><span class="tm-field"><span class="tm-typed">Anker PowerCore 10000 A1263</span></span><span class="tm-go">Check it live</span></div>
      <ol class="tm-agents"><li>Page reader</li><li>Is it real?</li><li>Safety Radar</li><li>Recall checker</li><li>Safety marks</li><li>Verdict, set by code</li></ol>
    </div>${HAND}` },
  { id: "chat", pose: "happy", tab: "chat", target: "#chat .chatwin", title: "Or just ask Eddy", text: "The real chat: pick a product or paste any link or screenshot, then ask in your own words. It remembers the conversation and shows its sources.",
    art: `<div class="tm-talk solo"><div class="tm-phone wa chat"><span class="tm-wahead">${SHIELD}Eddy · SafeShelf</span><span class="tm-msg me">Is this charger safe in a child's room?</span><span class="tm-msg bot"><b class="amber">Be careful</b>Buyers report it overheating.</span><span class="tm-msg bot">Sources: 3 buyer reviews · BIS registry</span></div></div>` },
  { id: "talk", pose: "happy", tab: "ask-out-loud", target: "#ask-out-loud", alt: { tab: "whatsapp", target: "#whatsapp" }, title: "Reach everyone", text: "Point the camera at the label and ask out loud, forward a link on WhatsApp, or share it from the Android app. Answers come back by voice, in 26 languages.",
    art: `<div class="tm-talk">
      <div class="tm-phone"><span class="tm-mic"><i></i></span><b>“Is this safe?”</b><small>Listening… हिन्दी · 日本語 · English</small></div>
      <div class="tm-phone wa"><span class="tm-wahead">SafeShelf</span><span class="tm-msg me">flipkart.com/kelvo-cx65…</span><span class="tm-msg bot"><b>⛔ Don't buy</b>Not the real product.</span><span class="tm-msg bot voice"><i></i>0:12</span></div>
    </div>` },
  { id: "after", pose: "thumbs", target: "#after", title: "After you buy, it keeps watching", text: "Saved products are rechecked for new recalls. Eddy also keeps return and warranty dates, answers from the manual and shares the list with family.",
    art: `<div class="tm-talk solo"><div class="tm-phone wa chat"><span class="tm-wahead">${SHIELD}My Shelf</span><span class="tm-msg bot"><b>Recalled since you bought it</b>NEWDERY power bank, saved 9 Oct.</span><span class="tm-msg bot"><b class="amber">Return window: 3 days left</b>Kelvo CX-65 charger</span><span class="tm-msg bot">Manual, p. 14: don't charge it overnight.</span></div></div>` },
  { id: "wrong", pose: "surprised", target: "#wrong", title: "If something goes wrong", text: "Safe steps first, never \"test it\". Then a drafted refund or complaint, a hazard report a person reviews, and where to dispose of it safely.",
    art: `<div class="tm-talk solo"><div class="tm-phone wa chat"><span class="tm-wahead">${SHIELD}Eddy · SafeShelf</span><span class="tm-msg me">My power bank is hot and swelling</span><span class="tm-msg bot"><b>Unplug it if safe, move it to a hard surface</b>Fire or smoke: call 112.</span><span class="tm-msg bot">Refund request drafted · case attached</span></div></div>` },
  { id: "anywhere", pose: "flying", target: "#business", alt: { target: "#developers" }, title: "Marketplaces, regulators and AI agents", text: "The same engine scans whole catalogs, hands regulators an evidence pack, searches every recall notice, and answers AI agents over 10 MCP tools.",
    art: `<div class="tm-prods">${[["#0271e4", "Chrome extension"], ["#f0a020", "Web page"], ["#1d9b52", "WhatsApp"], ["#7b5cd6", "Catalog scan"], ["#001123", "API · MCP"]]
      .map(([c, l]) => `<span style="--c:${c}"><i></i>${l}</span>`).join("")}</div>` },
  { id: "answers", pose: "thinking", tab: "answers", target: "#answers", title: "Why trust it", text: "Gemini reads reviews and labels, searches, talks and translates. Plain code makes the final call from the evidence, so it cannot invent a recall.",
    art: `<div class="tm-answers">
      <div class="tm-checks"><span>Official recalls</span><span>Buyer reviews</span><span>Safety marks</span><span>Is it real?</span></div>
      <ul class="tm-ans"><li class="red"><b>Don't buy</b>recalled or fake</li><li class="amber"><b>Be careful</b>reports under review</li><li class="green"><b>No problems found</b>in what was checked</li><li class="grey"><b>Can't tell yet</b>never a guess</li></ul>
    </div>` },
  { id: "proof", pose: "surprised", tab: "accuracy", target: "#accuracy", alt: { tab: "attack", target: "#attack" }, title: "Tested, and attacked on purpose", text: "Only 2 false alarms in 40 safe products, against 6 for Gemini alone. We also tried to fool it; see what it decided.",
    art: `<div class="tm-proof2">
      <div class="tm-bars"><small>False alarms out of 40</small><div><span>SafeShelf</span><i class="me" style="--w:18%"></i><b>2</b></div><div><span>Gemini alone</span><i style="--w:55%"></i><b>6</b></div><div><span>Keyword rules</span><i style="--w:100%"></i><b>11</b></div></div>
      <ul class="tm-attacks"><li>Fake regulator page</li><li>Look-alike model number</li><li>Hidden text aimed at AI</li></ul>
    </div>` },
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
    if (p.tab) { const t = $id(`tab-${p.tab}`); if (t && !t.hidden && !t.closest("[hidden]")) return { ...p, prep: slide.prep, el }; continue; }
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
      <div class="tg-foot">
        <img class="tg-mini" alt="" src="${POSE("hi")}">
        <button type="button" class="tg-back">Back</button>
        <span class="tg-dots" role="tablist" aria-label="Tour slides"></span>
        <button type="button" class="tg-next"></button>
      </div>
      <p class="tg-skip">Seen this before? <button type="button">Skip the tour</button></p>
      <span class="tg-arrow" aria-hidden="true"></span>
    </div>`;
  const spot = document.createElement("div");
  spot.className = "tg-spot";
  wrap.prepend(spot);
  document.body.append(wrap);

  const q = (sel) => wrap.querySelector(sel);
  const card = q(".tg-card");
  const art = q(".tg-art");
  const stage = q(".tg-stage");
  let slides = [];
  let at = 0;
  let lastFocus = null;
  let pinned = null; // the part of the page the current coachmark points at

  // the pictures are drawn at 520 × 270 and scaled to fit the card
  const fit = () => { stage.style.transform = `scale(${Math.min(1, art.clientWidth / 520)})`; art.style.height = `${270 * Math.min(1, art.clientWidth / 520)}px`; };

  function show(i) {
    at = Math.max(0, Math.min(i, slides.length - 1));
    const s = slides[at];
    q(".tg-eddy").src = q(".tg-mini").src = POSE(s.pose);
    q("#tg-title").textContent = s.title;
    q("#tg-text").textContent = s.text;
    stage.innerHTML = s.art;
    stage.dataset.slide = s.id;
    q(".tg-back").textContent = at === 0 ? "Skip" : "Back";
    q(".tg-next").textContent = at === 0 ? "Take the tour" : at === slides.length - 1 ? "Done" : "Next";
    q(".tg-skip").hidden = at === 0 || at === slides.length - 1;
    q(".tg-dots").replaceChildren(...slides.map((sl, j) => {
      const d = document.createElement("button");
      d.type = "button";
      d.setAttribute("role", "tab");
      d.setAttribute("aria-label", `${j + 1} of ${slides.length}: ${sl.title}`);
      d.setAttribute("aria-selected", String(j === at));
      d.onclick = () => show(j);
      return d;
    }));
    pin(s); // before fit(): a centred step's picture is only measurable once the card has left coachmark mode
    card.classList.remove("in");
    void card.offsetWidth; // restart the entrance and the picture's motion
    card.classList.add("in");
    fit();
    const form = stage.querySelector(".tm-try");
    art.setAttribute("aria-hidden", String(!form)); // only the last slide's picture is something to use
    if (form) form.onsubmit = (e) => { e.preventDefault(); tryProduct(form.elements[0].value.trim()); };
  }

  // the sticky top bar and jump bar cover the top of the page; parts are scrolled to just below them
  const topBar = () => [document.querySelector("body > header.top"), document.querySelector(".jump")]
    .reduce((h, el) => h + (el && !el.closest("[hidden]") ? el.offsetHeight : 0), 0);

  // a step that points at the page: open its tab, scroll it into view and put the card beside it
  function pin(slide) {
    const p = slide.target && placeOf(slide);
    wrap.classList.toggle("pin", !!p);
    pinned = null;
    if (!p) { card.style.left = card.style.top = ""; return; }
    if (p.tab) openTab(p.tab);
    p.prep?.();
    pinned = document.querySelector(p.target);
    const r = pinned.getBoundingClientRect();
    const off = topBar() + 16, room = innerHeight - off;
    const y = r.height < room * .5 ? r.top - off - (room - r.height - card.offsetHeight) / 2 : r.top - off;
    scrollTo({ top: Math.max(0, scrollY + y), behavior: "instant" }); // straight there, so the card never trails the page
    place();
  }

  // the spotlight around the part, and the card on whichever side has room, its arrow pointing at the part
  function place() {
    if (!pinned || wrap.hidden) return;
    const vw = document.documentElement.clientWidth, vh = innerHeight, m = 12, gap = 18, pad = 8;
    const r = pinned.getBoundingClientRect();
    const top = topBar();
    const b = { l: Math.max(4, r.left - pad), r: Math.min(vw - 4, r.right + pad), t: Math.max(top + 4, r.top - pad), b: Math.min(vh - 4, r.bottom + pad) };
    const cw = card.offsetWidth, ch = card.offsetHeight;
    let side = vw - b.r >= cw + gap + m ? "right" : b.l >= cw + gap + m ? "left" : vh - b.b >= ch + gap + m ? "below" : b.t - top >= ch + gap + m ? "above" : null;
    if (!side) { // a big part: light up the top of it and put the card underneath
      b.b = Math.max(b.t + 90, vh - ch - gap - m);
      side = vh - b.b >= ch + gap + m ? "below" : "over";
    }
    Object.assign(spot.style, { left: `${b.l}px`, top: `${b.t}px`, width: `${b.r - b.l}px`, height: `${Math.max(0, b.b - b.t)}px` });
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(v, hi));
    const mx = (b.l + b.r) / 2, my = (b.t + b.b) / 2;
    let x, y, a;
    if (side === "right" || side === "left") {
      x = side === "right" ? b.r + gap : b.l - gap - cw;
      y = clamp(my - ch / 2, top + m, vh - ch - m);
      a = clamp(my - y, 26, ch - 26);
    } else if (side === "over") {
      x = (vw - cw) / 2; y = vh - ch - m; a = 0;
    } else {
      x = clamp(mx - cw / 2, m, vw - cw - m);
      y = side === "below" ? b.b + gap : b.t - gap - ch;
      a = clamp(mx - x, 26, cw - 26);
    }
    card.dataset.side = side;
    card.style.left = `${Math.round(x)}px`;
    card.style.top = `${Math.round(y)}px`;
    card.style.setProperty("--a", `${Math.round(a)}px`);
  }
  let frame = 0;
  const follow = () => { if (pinned && !frame) frame = requestAnimationFrame(() => { frame = 0; place(); }); };
  window.addEventListener("scroll", follow, { passive: true });

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
    wrap.classList.remove("pin");
    pinned = null;
    launch.hidden = false;
    document.documentElement.classList.remove("tg-on");
    if (refocus) lastFocus?.focus?.({ preventScroll: true });
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
  q(".tg-skip button").addEventListener("click", () => close());
  wrap.addEventListener("click", (e) => { if (e.target === wrap && !pinned) close(); }); // coachmarks close only on purpose
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
  window.addEventListener("resize", () => { if (!wrap.hidden) { fit(); place(); } });

  // first visit on this browser: open by itself once the page has drawn its views
  if (!store.get() && !new URLSearchParams(location.search).has("notour")) setTimeout(open, 1200);
  return { open };
}
