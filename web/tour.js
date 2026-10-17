// "Page tour": a short guided walkthrough of the judges' page. Each step lights up one part of the page and shows a card
// with a small moving picture, a title and two lines, dots for progress, and Skip / Next. It opens once by itself after
// sign-in (remembered on this browser) and again from the Tour button at the bottom right. Steps whose part of the page
// is hidden for the chosen view (roles.js) are skipped. Plain module, no build step; the pictures are fixed markup.

const KEY = "safeshelf-tour-seen";
const SHIELD = `<svg viewBox="0 0 32 32"><path d="M4 8a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v8c0 7-5.5 12-12 14C9.5 28 4 23 4 16z" fill="#0271E4"/><path d="m10.5 16 4 4 7-8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const CURSOR = `<svg class="tg-cursor" viewBox="0 0 16 20" aria-hidden="true"><path d="M1 1v15l4-4 3 7 3-1.3-3-6.7h6z" fill="#001123" stroke="#fff" stroke-width="1.2" stroke-linejoin="round"/></svg>`;

const STEPS = [
  {
    target: "#for", title: "Pick who you are",
    points: ["One engine, four people: shopper, marketplace, regulator or developer.", "The page reorders itself around the view you pick."],
    art: `<div class="tg-chips"><span>Shopper</span><span class="on">Marketplace</span><span>Regulator</span><span>Developer</span></div>${CURSOR}`,
  },
  {
    target: "#answers", title: "Four answers, never a guess",
    points: ["Every listing is asked two things: is it safe, and is it real?", "Plain code picks the colour from the evidence; Gemini only explains it."],
    art: `<ul class="tg-ans"><li class="red"><b>Don't buy</b></li><li class="amber"><b>Be careful</b></li><li class="green"><b>No problems found</b></li><li class="grey"><b>Can't tell yet</b></li></ul>`,
  },
  {
    target: ".trytabs", title: "Four ways to try it live",
    points: ["On a shop page, paste a listing, ask out loud, or on WhatsApp.", "Each one calls the same live API on Cloud Run."],
    art: `<div class="tg-tabs"><i class="on"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/></svg></i><i><svg viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg></i><i><svg viewBox="0 0 24 24"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/></svg></i><i><svg viewBox="0 0 24 24"><path d="M4 20l1.3-3.9A8 8 0 1 1 8 19z"/></svg></i></div>${CURSOR}`,
  },
  {
    target: "#shop-page .win", title: "Press Check on any shop page",
    points: ["Pick a tab, or paste a real product link in the address bar.", "The SafeShelf panel opens on the page with its answer and proof."],
    art: `<div class="tg-win"><div class="tg-bar"><span class="tg-lights"><i></i><i></i><i></i></span><span class="tg-url">amazon.co.jp/dp/W5PRO</span><span class="tg-ext">${SHIELD}</span></div><div class="tg-verdict"><b>Don't buy</b><small>Recalled in Japan · exact model</small></div></div>${CURSOR}`,
  },
  {
    target: "#accuracy", title: "Is it accurate?",
    points: ["Tested on 25 real recalls and 40 products that were never recalled.", "Fewer false alarms than Gemini alone or keyword rules."],
    art: `<div class="tg-bars"><div><span>SafeShelf</span><i style="--w:18%" class="me"></i><b>2</b></div><div><span>Gemini alone</span><i style="--w:55%"></i><b>6</b></div><div><span>Keyword rules</span><i style="--w:100%"></i><b>11</b></div><small>false alarms out of 40</small></div>`,
  },
  {
    target: "#attack", title: "Can it be fooled?",
    points: ["We attacked our own code with fake regulator pages and look-alike models.", "See each attack and what SafeShelf decided."],
    art: `<div class="tg-attack"><span class="tg-shield">${SHIELD}</span><ul><li>Fake regulator page</li><li>Look-alike model</li><li>Hidden AI instructions</li></ul></div>`,
  },
  {
    target: "#products", title: "Where to use it",
    points: ["A Chrome extension, this web page, WhatsApp, catalog scans and an API.", "AI shopping agents ask the same questions over MCP."],
    art: `<div class="tg-prods"><i style="--c:#0271e4"></i><i style="--c:#f0a020"></i><i style="--c:#1d9b52"></i><i style="--c:#7b5cd6"></i><i style="--c:#001123"></i></div>`,
  },
];

const store = {
  get: () => { try { return localStorage.getItem(KEY); } catch (_) { return "1"; } }, // no storage: never open by itself
  set: () => { try { localStorage.setItem(KEY, "1"); } catch (_) { /* private window */ } },
};

// A step counts only if its part of the page is on screen for this view (roles.js hides the rest).
const targetOf = (step) => {
  const t = document.querySelector(step.target);
  if (!t || t.closest("[hidden]")) return null;
  const r = t.getBoundingClientRect();
  return r.width && r.height ? t : null;
};

// how far down the sticky bars reach (the top bar, and the section links once they stick)
const barsBottom = () => Math.max(76, ...[...document.querySelectorAll("body > header.top, .jump")]
  .map((e) => [getComputedStyle(e), e.getBoundingClientRect()])
  .filter(([css, r]) => css.position === "sticky" && r.top <= (parseFloat(css.top) || 0) + 1)
  .map(([, r]) => r.bottom));

export function setUpTour() {
  const launch = document.createElement("button");
  launch.type = "button";
  launch.className = "tg-launch";
  launch.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.4 2.3c-.6.3-.9.8-.9 1.4v.3M12 17h.01"/></svg><span>Page tour</span>`;
  if (!store.get()) launch.classList.add("fresh");
  document.body.append(launch);

  const shade = document.createElement("div");
  shade.className = "tg-shade";
  shade.hidden = true;
  const ring = document.createElement("div");
  ring.className = "tg-ring";
  const card = document.createElement("div");
  card.className = "tg-card";
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-modal", "false");
  card.setAttribute("aria-labelledby", "tg-title");
  card.innerHTML = `<div class="tg-art" aria-hidden="true"></div>
    <div class="tg-body"><span class="tg-count"></span><h3 id="tg-title"></h3><ul class="tg-points"></ul></div>
    <div class="tg-foot"><span class="tg-dots" aria-hidden="true"></span><span class="tg-btns"><button type="button" class="tg-skip">Skip</button><button type="button" class="tg-back">Back</button><button type="button" class="tg-next primary">Next</button></span></div>`;
  shade.append(ring, card);
  document.body.append(shade);

  const $ = (sel) => card.querySelector(sel);
  let steps = [];
  let at = 0;
  let target = null;
  let frame = 0;
  let lastFocus = null;

  function place() {
    if (shade.hidden || !target) return;
    const r = target.getBoundingClientRect();
    const pad = 8;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    // the ring hugs the part of the page, clipped to the screen so a tall section still reads as "here"
    const top = Math.max(r.top - pad, barsBottom() + 6);
    const bottom = Math.min(r.bottom + pad, vh - 8);
    Object.assign(ring.style, { top: `${top}px`, left: `${Math.max(r.left - pad, 6)}px`, width: `${Math.min(r.width + 2 * pad, vw - 12)}px`, height: `${Math.max(bottom - top, 40)}px` });
    if (vw < 640) { card.style.cssText = ""; card.classList.add("docked"); return; }
    card.classList.remove("docked");
    const cw = card.offsetWidth;
    const ch = card.offsetHeight;
    const gap = 16;
    // beside the ring if there is room, else inside its bottom-right corner, always on screen
    let x = r.right + gap;
    let y = top;
    if (x + cw > vw - 16) x = r.left - cw - gap;
    if (x < 16) { x = Math.min(r.right, vw) - cw - 24; y = bottom - ch - 24; }
    x = Math.min(Math.max(x, 16), vw - cw - 16);
    y = Math.min(Math.max(y, barsBottom() + 14), vh - ch - 16);
    card.style.left = `${x}px`;
    card.style.top = `${y}px`;
  }
  const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(place); };

  function show(i) {
    at = i;
    const step = steps[i];
    target = targetOf(step);
    if (!target) { steps.splice(i, 1); return steps.length ? show(Math.min(i, steps.length - 1)) : close(); }
    const art = $(".tg-art");
    art.innerHTML = step.art;
    art.dataset.step = String(STEPS.indexOf(step));
    $(".tg-count").textContent = `${i + 1} of ${steps.length}`;
    $("#tg-title").textContent = step.title;
    $(".tg-points").replaceChildren(...step.points.map((p) => Object.assign(document.createElement("li"), { textContent: p })));
    $(".tg-dots").replaceChildren(...steps.map((_, j) => Object.assign(document.createElement("i"), { className: j === i ? "on" : "" })));
    $(".tg-back").hidden = i === 0;
    $(".tg-skip").hidden = i === steps.length - 1;
    $(".tg-next").textContent = i === steps.length - 1 ? "Done" : "Next";
    card.classList.remove("in");
    void card.offsetWidth; // restart the entrance and the picture's motion
    card.classList.add("in");
    // bring the part of the page under the sticky bar, then follow it while the page settles
    const r = target.getBoundingClientRect();
    const bars = Math.max(barsBottom(), document.querySelector(".jump")?.offsetHeight + 76 || 0) + 20;
    const tall = r.height > window.innerHeight - bars - 40 || window.innerWidth < 640; // phones: above the docked card
    const y = window.scrollY + r.top - (tall ? bars : Math.max(bars, (window.innerHeight - r.height) / 2));
    window.scrollTo({ top: Math.max(0, y), behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    schedule();
    $(".tg-next").focus({ preventScroll: true });
  }

  function open() {
    steps = STEPS.filter(targetOf);
    if (!steps.length) return;
    lastFocus = document.activeElement;
    store.set();
    launch.classList.remove("fresh");
    launch.hidden = true;
    shade.hidden = false;
    document.documentElement.classList.add("tg-on");
    show(0);
  }

  function close() {
    shade.hidden = true;
    launch.hidden = false;
    target = null;
    document.documentElement.classList.remove("tg-on");
    lastFocus?.focus?.({ preventScroll: true });
  }

  launch.addEventListener("click", open);
  $(".tg-skip").addEventListener("click", close);
  $(".tg-back").addEventListener("click", () => show(at - 1));
  $(".tg-next").addEventListener("click", () => (at < steps.length - 1 ? show(at + 1) : close()));
  shade.addEventListener("click", (e) => { if (e.target === shade) close(); });
  document.addEventListener("keydown", (e) => {
    if (shade.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight" && at < steps.length - 1) show(at + 1);
    else if (e.key === "ArrowLeft" && at > 0) show(at - 1);
  });
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);

  // first visit on this browser: open by itself once the page has drawn its views
  if (!store.get() && !new URLSearchParams(location.search).has("notour")) setTimeout(open, 1200);
  return { open };
}
