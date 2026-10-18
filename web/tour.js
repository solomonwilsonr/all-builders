// Eddy's "Get started" checklist for the judges' page, led by the real Chrome with the SafeShelf extension.
// - A launcher at the bottom right (Eddy's face · Get started · n% complete) opens a checklist panel: an ink header with
//   Eddy in a progress ring, then one row per thing to try, each with Start (or Done).
// - Start folds the panel, opens the step's tab, scrolls to the real control, rings it and points at it with an ink
//   coach card: a picture, one line on what happens, and one button that does the step's first move.
// - "Check a product inside it" is a tour of the real browser itself, six stops (Chrome, a test product, the page's
//   right answer, the shield, the answer, Ask and Save). The cloud Chrome is a 1280 × 800 screen drawn into #rframe at
//   the same aspect ratio, so each stop is a box on that screen, mapped onto the frame and ringed there. It starts by
//   itself the first time the browser goes live (browser/view.html posts safeshelf-browser:ready).
// - Steps tick themselves off by watching the page for the real thing, so app.js doesn't need to know about the guide.
//   Progress is kept in this browser only. It opens by itself once on a wide screen (?notour turns that off).

const KEY = "safeshelf-guide";
const POSE = (name) => `site/assets/guide/eddy-${name}.webp`;
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (s) => document.querySelector(s);
const $id = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const svg = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const I = {
  x: svg('<path d="M6 6l12 12M18 6L6 18"/>'),
  down: svg('<path d="M6 9l6 6 6-6"/>'),
  play: svg('<path d="M8 5v14l11-7z"/>'),
  spark: svg('<path d="M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6z"/>'),
  browser: svg('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M6.5 6.5h.01M9.5 6.5h.01"/>'),
  shield: svg('<path d="M12 3l7 3v5c0 4.5-3 8.2-7 10-4-1.8-7-5.5-7-10V6z"/><path d="m9 12 2 2 4-4"/>'),
  pages: svg('<rect x="7" y="3" width="13" height="15" rx="2"/><path d="M4 7v12a2 2 0 0 0 2 2h10"/>'),
  link: svg('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'),
  chat: svg('<path d="M20 12a8 8 0 0 1-11.6 7.1L4 20l1-4.2A8 8 0 1 1 20 12z"/>'),
  chart: svg('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
};

// the tour shows the real tool, not its preview card (app.js)
const openTab = (id) => { const t = $id(`tab-${id}`); if (t && t.getAttribute("aria-selected") !== "true") t.click(); const p = $id(id); if (p?.dataset.view) p.dataset.view = "live"; };
const shopMode = () => $id("shop-page")?.dataset.mode; // choose | test | real (app.js)
const setField = (form, name, value) => { const f = form?.elements[name]; if (f) { f.value = value; f.dispatchEvent(new Event("input", { bubbles: true })); } };
// a step is offered only while its part of the page is in the chosen view (roles.js hides the rest)
const shown = (sel) => { const el = $(sel); return !!el && !el.hidden && !el.closest("[hidden]"); };
// the real-browser choice exists only once the cloud browser is deployed (setUpRemote unhides it)
const hasReal = () => !!$id("real-row") && !$id("real-row").hidden && shown("#tab-shop-page");

// Stops inside the real browser. box = [x, y, w, h] on the cloud Chrome's 1280 × 800 screen: Chrome's tab strip and
// toolbar take the top 86 px, and the SafeShelf rail sits on the page's right edge, centred (extension/content.js).
const INSIDE = [
  { t: "This is a real Chrome", pose: "hi", box: [0, 0, 1280, 86],
    d: "A real Chromium in the cloud with the SafeShelf extension installed and signed in as you. Click inside it to use it: mouse, keyboard and scrolling all work. It closes by itself after 5 minutes." },
  { t: "Open a test product", pose: "pointing", box: [24, 560, 1232, 232],
    d: "It starts on a real Amazon.in listing, a toddler table recalled abroad; the test shops are in the second tab. Scroll down inside the browser and click any of the eight products, or let Eddy open the recalled power bank for you.",
    action: { label: "Open the HAIARA power bank", run: () => $("#lineup .lu-act")?.click(), when: () => !!$("#lineup .lu-act") } },
  { t: "Know the right answer first", pose: "thinking", box: [918, 262, 328, 452],
    d: "Every test page has a “How to test this page” card: what the page tests and what a correct check says. For the HAIARA power bank: Don’t buy, recalled in Japan." },
  { t: "Press the shield", pose: "excited", box: [1214, 486, 66, 76],
    d: "The SafeShelf rail sits on the page’s right edge: Ask, Save, Shelf and, at the bottom, the shield, Check with SafeShelf. Press it. If it asks about AI credits, press Continue." },
  { t: "Read the answer and its proof", pose: "surprised", box: [738, 196, 490, 470],
    d: "In a few seconds the verdict opens beside the listing: Don’t buy, Be careful, No problems found or Can’t tell yet, with the official notice, reviews or registry entry behind it. Open the evidence to see every source." },
  { t: "Ask, save, or paste your own", pose: "thumbs", box: [1218, 328, 62, 232],
    d: "Ask chats about this product; Save puts it on My Shelf, rechecked for new recalls. Paste any Amazon or Flipkart link in the address bar to check a real listing." },
];

let live = false; // the real browser is connected

const STEPS = [
  { k: "real", t: "Start the real browser", d: "Chrome with the SafeShelf extension, live.", icon: I.browser, pose: "pointing", avail: hasReal,
    tip: "A real Chrome in the cloud with the SafeShelf extension, signed in as you. It opens on a real Amazon.in listing recalled abroad, and our eight test products, where the right answer is known; Amazon and Flipkart work too.",
    prep: () => { openTab("shop-page"); if (shopMode() === "test") $id("mode-back")?.click(); }, target: () => (live ? $id("rwin") : $id("remote-start")),
    action: { label: "Start a real browser", time: "~15 s", run: () => { if (!live) $id("remote-start")?.click(); } } },
  { k: "inside", t: "Check a product inside it", d: "Six stops: the product, the shield, the proof.", icon: I.shield, pose: "excited", avail: hasReal,
    locked: () => (live ? null : "Unlocks once the real browser is live"), tour: INSIDE },
  { k: "shop", t: "Try the instant test pages", d: "The same eight products, no waiting.", icon: I.pages, pose: "pointing", avail: () => shown("#tab-shop-page"),
    tip: "Eight shop pages where the right answer is known, drawn on this page with the extension’s own panel. Press the blue shield and the answer opens beside the listing.",
    prep: () => { openTab("shop-page"); if (shopMode() === "choose") $id("test-start")?.click(); }, target: () => $id("ext-toggle"),
    action: { label: "Press the shield", run: () => $id("ext-toggle")?.click() } },
  { k: "paste", t: "Paste any listing", d: "Eight agents check it live while you watch.", icon: I.link, pose: "excited", avail: () => shown("#tab-check-own"),
    tip: "Copy a title from any shop. Eight agents read it and look for recalls and fakes, and plain code sets the verdict from what they find.",
    prep: () => openTab("check-own"), target: () => $id("own"),
    action: { label: "Fill in an example", run: () => { const f = $id("own"); setField(f, "title", "Anker PowerCore 10000 A1263"); f?.querySelector("button[type=submit]")?.focus({ preventScroll: true }); } } },
  { k: "chat", t: "Ask Eddy anything", d: "“Is this charger safe in a child’s room?”", icon: I.chat, pose: "happy", avail: () => shown("#tab-chat"),
    tip: "The real chat on the live API. Ask in your own words, paste a link or drop a screenshot; sources sit under every answer.",
    prep: () => openTab("chat"), target: () => $("#chat .chatwin") },
  { k: "trust", t: "See why to trust it", d: "Tested, and attacked on purpose.", icon: I.chart, pose: "thinking", avail: () => shown("#tab-accuracy"),
    tip: "Only 2 false alarms in 40 safe products, against 6 for Gemini alone. Gemini gathers the evidence; code makes the call, so it can’t invent a recall.",
    prep: () => openTab("accuracy"), target: () => $id("accuracy"), action: { label: "Got it", ticks: true } },
];

const store = {
  get() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (_) { return { done: [], open: false, hidden: false }; } }, // no storage: never opens by itself
  set(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (_) { /* private window */ } },
};

export function setUpTour() {
  for (const p of new Set(["hi", "thumbs", ...STEPS.map((s) => s.pose), ...INSIDE.map((s) => s.pose)])) { const i = new Image(); i.src = POSE(p); }

  let state = { done: [], open: null, hidden: false, ...(store.get() || {}) };
  const save = () => store.set(state);
  const steps = () => STEPS.filter((s) => s.avail());
  const isDone = (k) => state.done.includes(k);
  const progress = () => { const all = steps(); const n = all.filter((s) => isDone(s.k)).length; return { n, N: all.length, pct: all.length ? Math.round((100 * n) / all.length) : 0 }; };

  const root = document.createElement("aside");
  root.className = "tg";
  root.setAttribute("aria-label", "Get started with Eddy");
  document.body.append(root);
  const coach = document.createElement("div");
  coach.className = "tg-coach";
  coach.setAttribute("role", "dialog");
  coach.setAttribute("aria-modal", "false");
  coach.hidden = true;
  const spot = document.createElement("div"); // the ring around a stop inside the real browser
  spot.className = "tg-spot";
  spot.hidden = true;
  document.body.append(coach, spot);
  let coachStep = null, coachTarget = null, stop = -1; // stop: index into the step's tour, -1 for a one-card step

  function ring(size) {
    const r = size / 2 - 2, c = 2 * Math.PI * r, { pct } = progress();
    return `<svg class="tg-ring" viewBox="0 0 ${size} ${size}" aria-hidden="true"><circle cx="${size / 2}" cy="${size / 2}" r="${r}" class="bg"/>` +
      `<circle cx="${size / 2}" cy="${size / 2}" r="${r}" class="fg" style="stroke-dasharray:${(c * pct) / 100} ${c}${pct ? "" : ";opacity:0"}"/></svg>`;
  }

  function render(ticked) {
    if (state.hidden) { root.replaceChildren(); document.body.classList.remove("tg-open"); return; }
    const list = steps(), { n, N, pct } = progress(), all = N > 0 && n >= N;
    const next = list.find((s) => !isDone(s.k) && !s.locked?.());
    const pill = `<button class="tg-pill tg-launch${ticked ? " pop" : ""}" type="button" id="tg-pill" aria-expanded="${!!state.open}" aria-controls="tg-panel">` +
      `<img src="site/assets/eddy-face.webp" alt="" width="34" height="34"><span class="tg-pill-t">${all ? "All set" : "Get started"}</span>` +
      `<span class="tg-pill-sep" aria-hidden="true"></span><span class="tg-pill-p">${pct}% complete</span></button>`;
    const panel = !state.open ? "" :
      `<section class="tg-panel" id="tg-panel" aria-label="Get started checklist">` +
      `<div class="tg-head"><div class="tg-head-bar"><span>Get started · ${n} of ${N}</span><button class="tg-ib" type="button" id="tg-min" aria-label="Collapse the checklist">${I.down}</button></div>` +
      `<div class="tg-head-main"><div><h2>${all ? "You’ve seen it all" : "Try SafeShelf in a real Chrome"}</h2>` +
      `<p>${all ? "Thanks for trying everything. Eddy keeps watching after you buy." : "Start with the real browser and the extension. Each step points at the real button."}</p></div>` +
      `<div class="tg-dial">${ring(96)}<span class="tg-dial-c"><img src="${POSE(all ? "thumbs" : "hi")}" alt="" width="96" height="96"></span><span class="tg-dial-p">${pct}% done</span></div></div></div>` +
      `<ol class="tg-list">${list.map((s) => {
        const d = isDone(s.k), lk = !d && s.locked?.();
        return `<li class="${d ? "done" : ""}${s === next ? " next" : ""}${lk ? " locked" : ""}"><span class="tg-ic" aria-hidden="true">${s.icon}</span>` +
          `<div class="tg-tx"><b>${esc(s.t)}</b><small>${esc(lk || s.d)}</small></div>` +
          (d ? `<span class="tg-done">Done</span>` : `<button class="tg-start${s === next ? " primary" : ""}" type="button" data-start="${s.k}"${lk ? " disabled" : ""} aria-label="Start: ${esc(s.t)}">Start</button>`) + `</li>`;
      }).join("")}</ol>` +
      `<div class="tg-foot"><button type="button" id="tg-reset">Start over</button><button type="button" id="tg-hide">Hide checklist</button></div></section>`;
    root.innerHTML = panel + pill;
    document.body.classList.toggle("tg-open", !!state.open);
    root.querySelector("#tg-pill").addEventListener("click", () => setOpen(!state.open));
    if (!state.open) return;
    root.querySelector("#tg-min").addEventListener("click", () => { setOpen(false); root.querySelector("#tg-pill").focus(); });
    root.querySelector("#tg-hide").addEventListener("click", () => { closeCoach(); state.hidden = true; save(); render(); });
    root.querySelector("#tg-reset").addEventListener("click", () => { state.done = []; save(); render(); });
    root.querySelectorAll("[data-start]").forEach((b) => b.addEventListener("click", () => start(b.dataset.start)));
  }

  function setOpen(v) { if (v) closeCoach(); state.open = v; save(); render(); }

  function done(k) {
    if (isDone(k) || !STEPS.some((s) => s.k === k)) return;
    state.done.push(k);
    save();
    if (coachStep?.k === k && stop < 0) closeCoach();
    render(true);
  }

  // ---- coach card -----------------------------------------------------------------------------------------------
  function start(k) {
    const s = STEPS.find((x) => x.k === k);
    if (!s) return;
    if (k === "real" && live) { done("real"); return start("inside"); } // already running: straight to the tour inside
    s.prep?.();
    setOpen(false); // fold to the launcher so the card and the page stay clear
    if (s.tour) {
      openTab("shop-page");
      $id("rwin")?.scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "center" });
      return setTimeout(() => openStop(s, 0), calm() ? 0 : 380);
    }
    setTimeout(() => openCoach(s), s.prep ? 260 : 0);
  }

  const head = (kicker, title, pose) =>
    `<span class="tg-arrow" aria-hidden="true"></span>` +
    `<div class="tg-c-top">${pose ? `<img class="tg-c-eddy" src="${POSE(pose)}" alt="">` : ""}<div class="tg-c-h"><small>${esc(kicker)}</small><b id="tg-c-title">${esc(title)}</b></div>` +
    `<button class="tg-ib" type="button" id="tg-c-x" aria-label="Close">${I.x}</button></div>`;

  function show(html) {
    coach.innerHTML = html;
    coach.setAttribute("aria-labelledby", "tg-c-title");
    coach.hidden = false;
    coach.classList.remove("in"); void coach.offsetWidth; coach.classList.add("in");
    coach.querySelector("#tg-c-x").addEventListener("click", closeCoach);
    place();
    setTimeout(place, 450); // after smooth scrolling settles
  }

  // one card for a step: the picture, a line, one action
  function openCoach(s) {
    clearHi();
    coachStep = s; stop = -1;
    const el = s.target?.() || null;
    coachTarget = el ? () => el : null;
    if (el) {
      el.scrollIntoView({ behavior: calm() ? "auto" : "smooth", block: "center", inline: "nearest" });
      el.classList.add("tg-hi");
    }
    const a = s.action || { label: "Got it" };
    const list = steps(), at = list.indexOf(s);
    show(head(`Step ${at + 1} of ${list.length}`, s.t) +
      `<div class="tg-art" aria-hidden="true"><i class="s1">${I.spark}</i><i class="s2">${I.spark}</i><i class="s3">${I.spark}</i>` +
      `<span class="tg-art-ic">${s.icon}</span><img class="tg-art-eddy" src="${POSE(s.pose)}" alt=""></div>` +
      `<p class="tg-c-d">${esc(s.tip)}</p>` +
      `<button class="tg-go primary" type="button" id="tg-c-go">${I.play}<span>${esc(a.label)}</span>${a.time ? `<em>${esc(a.time)}</em>` : ""}</button>`);
    coach.querySelector("#tg-c-go").addEventListener("click", () => {
      closeCoach();
      if (a.ticks) done(s.k);
      a.run?.();
      if (s.k === "real" && !live) setTimeout(waitCard, 300);
    });
    coach.querySelector("#tg-c-go").focus({ preventScroll: true });
  }

  // while the cloud Chrome starts: a card on the browser window; the tour inside follows once it is live
  function waitCard() {
    if (live || !shown("#rwin")) return;
    clearHi();
    coachStep = STEPS[0]; stop = -1;
    coachTarget = () => $id("rwin");
    show(head("Real browser", "Starting a real Chrome…", "waving") +
      `<p class="tg-c-d">About 15 seconds. When it’s live, Eddy shows you around inside it: the product, the shield and the proof.</p>` +
      `<div class="tg-wait" aria-hidden="true"><i></i></div>`);
  }

  // a stop inside the real browser: ringed on the frame, with Back / Next
  function openStop(s, i) {
    clearHi();
    coachStep = s; stop = i;
    const st = s.tour[i], last = i === s.tour.length - 1;
    coachTarget = () => boxRect(st.box);
    const act = st.action && (!st.action.when || st.action.when()) ? st.action : null;
    show(head(`Browser tour · ${i + 1} of ${s.tour.length}`, st.t, st.pose) +
      `<div class="tg-bar" aria-hidden="true">${s.tour.map((_, j) => `<i class="${j <= i ? "on" : ""}"></i>`).join("")}</div>` +
      `<p class="tg-c-d">${esc(st.d)}</p>` +
      (act ? `<button class="tg-go line" type="button" id="tg-c-act">${I.play}<span>${esc(act.label)}</span></button>` : "") +
      `<div class="tg-nav"><button class="tg-back" type="button" id="tg-c-back"${i ? "" : " hidden"}>Back</button>` +
      `<button class="tg-go primary" type="button" id="tg-c-next">${last ? "Done" : "Next"}</button></div>`);
    coach.querySelector("#tg-c-act")?.addEventListener("click", () => { act.run(); openStop(s, i + 1); });
    coach.querySelector("#tg-c-back").addEventListener("click", () => openStop(s, i - 1));
    coach.querySelector("#tg-c-next").addEventListener("click", () => { if (last) { closeCoach(); done(s.k); } else openStop(s, i + 1); });
    coach.querySelector("#tg-c-next").focus({ preventScroll: true });
  }

  // a box on the cloud Chrome's 1280 × 800 screen, in page coordinates: #rframe draws that screen at the same ratio
  function boxRect([x, y, w, h]) {
    const f = $id("rframe");
    if (!f || !shown("#rwin")) return null;
    const r = f.getBoundingClientRect(), k = r.width / 1280;
    const left = r.left + x * k, top = r.top + y * k;
    return { left, top, width: w * k, height: h * k, right: left + w * k, bottom: top + h * k };
  }

  const clearHi = () => { document.querySelectorAll(".tg-hi").forEach((e) => e.classList.remove("tg-hi")); spot.hidden = true; };
  function closeCoach() { coach.hidden = true; coachStep = coachTarget = null; stop = -1; clearHi(); }

  // the sticky top bar covers the top of the page; the card never goes under it
  const topBar = () => { const t = $("body > header.top"); return t && !t.closest("[hidden]") ? t.getBoundingClientRect().bottom : 0; };

  // the card beside its target (right, left, below, above), its arrow pointing at it
  function place() {
    if (coach.hidden) return;
    const W = document.documentElement.clientWidth, H = innerHeight, cw = coach.offsetWidth, ch = coach.offsetHeight, gap = 16, top = Math.max(8, topBar() + 8);
    let t = coachTarget?.() || null;
    if (t instanceof Element) t = document.contains(t) && t.offsetParent !== null ? t.getBoundingClientRect() : null;
    if (stop >= 0 && t) Object.assign(spot.style, { left: `${t.left - 4}px`, top: `${t.top - 4}px`, width: `${t.width + 8}px`, height: `${t.height + 8}px` });
    spot.hidden = !(stop >= 0 && t);
    let x, y, side = "none";
    if (!t) { x = (W - cw) / 2; y = (H - ch) / 2; }
    else if (t.right + gap + cw < W - 8) { side = "left"; x = t.right + gap; y = t.top + t.height / 2 - ch / 2; }
    else if (t.left - gap - cw > 8) { side = "right"; x = t.left - gap - cw; y = t.top + t.height / 2 - ch / 2; }
    else if (t.bottom + gap + ch < H - 8) { side = "top"; y = t.bottom + gap; x = t.left + t.width / 2 - cw / 2; }
    else if (t.top - gap - ch > top) { side = "bottom"; y = t.top - gap - ch; x = t.left + t.width / 2 - cw / 2; }
    else { side = "none"; x = t.left + 16; y = t.bottom - ch - 16; } // a big target: sit inside its lower left corner
    x = Math.max(8, Math.min(W - cw - 8, x));
    y = Math.max(top, Math.min(H - ch - 8, y));
    Object.assign(coach.style, { left: `${Math.round(x)}px`, top: `${Math.round(y)}px` });
    coach.dataset.side = side;
    const arrow = coach.querySelector(".tg-arrow");
    if (t && arrow) arrow.style.cssText = side === "left" || side === "right"
      ? `top:${Math.max(22, Math.min(ch - 22, t.top + t.height / 2 - y))}px`
      : `left:${Math.max(22, Math.min(cw - 22, t.left + t.width / 2 - x))}px`;
  }
  let frame = 0;
  const follow = () => { if (!coach.hidden && !frame) frame = requestAnimationFrame(() => { frame = 0; place(); }); };
  addEventListener("scroll", follow, { passive: true, capture: true });
  addEventListener("resize", follow);
  document.addEventListener("keydown", (e) => {
    if (coach.hidden) return;
    if (e.key === "Escape") closeCoach();
    else if (stop >= 0 && !e.target.matches?.("input, textarea")) {
      if (e.key === "ArrowRight") coach.querySelector("#tg-c-next")?.click();
      else if (e.key === "ArrowLeft" && stop > 0) coach.querySelector("#tg-c-back")?.click();
    }
  });
  // a click on the lit control is the person doing the step: let it through, then put the card away. The tour inside
  // the browser stays up while they use the browser (clicks inside the frame never reach this page anyway).
  document.addEventListener("pointerdown", (e) => {
    if (coach.hidden || stop >= 0 || coach.contains(e.target) || root.contains(e.target)) return;
    closeCoach();
  }, true);

  // ---- steps tick themselves off ---------------------------------------------------------------------------------
  document.addEventListener("click", (e) => {
    const el = e.target.closest?.("button, a");
    if (!el) return;
    if (el.matches("#ext-toggle")) done("shop");
    else if (el.matches("#tab-accuracy, #tab-attack")) done("trust");
  }, true);
  document.addEventListener("submit", (e) => { if (e.target.id === "own") done("paste"); }, true);
  // the chat lives in an iframe: the page loses focus to it when someone clicks into it
  addEventListener("blur", () => setTimeout(() => { if (document.activeElement?.id === "chatframe") done("chat"); }));
  // the real browser (browser/view.html) says when it is live and when it has ended
  addEventListener("message", (e) => {
    if (!e.source || e.source !== $id("rframe")?.contentWindow) return;
    const type = e.data?.type;
    if (type === "safeshelf-browser:ready") {
      live = true;
      done("real");
      if (!isDone("inside") && !state.hidden) setTimeout(() => { if (live) start("inside"); }, 900);
      else if (coachStep?.k === "real") closeCoach();
    } else if (type === "safeshelf-browser:ended") {
      live = false;
      if (coachStep?.tour || coachStep?.k === "real") closeCoach();
      render();
    }
  });
  // the session can also end from this page (End session, the 5-minute timer): the frame goes back to about:blank
  new MutationObserver(() => { if (live && !shown("#rwin")) { live = false; if (coachStep?.tour) closeCoach(); render(); } })
    .observe($id("rwin") || document.body, { attributes: true, attributeFilter: ["hidden"] });

  // roles.js and app.js can hide parts later; keep the list to what's on the page
  const offered = () => steps().map((s) => s.k).join();
  let was = offered();
  new MutationObserver(() => { const now = offered(); if (now !== was) { was = now; render(); } })
    .observe(document.body, { subtree: true, attributes: true, attributeFilter: ["hidden"] });

  // first visit on a wide screen: open the checklist once the page has drawn its views
  if (state.open === null) {
    state.open = false;
    save();
    if (!matchMedia("(max-width: 900px)").matches && !new URLSearchParams(location.search).has("notour")) setTimeout(() => setOpen(true), 1200);
  }
  render();

  const open = () => { state.hidden = false; setOpen(true); };
  return { open, done };
}
