// Eddy, the page guide: an assistant-style walkthrough of every feature on the judges' page. Eddy (the mascot, cut
// from the brand sheet into site/assets/guide/) flies to each part of the page, "thinks", then types out what it does,
// in a pose that fits. Steps open the right Try it tab first and can offer a button that does the thing for the person
// (opens the test pages, fills in a sample listing…). The "Ask Eddy" box answers questions about the page by finding
// the step they're about and jumping there; this part is plain word matching, not AI. A question that names a product
// goes to the live check (Paste a listing), which is the real AI and counts against the person's limit.
// Eddy opens once by himself after sign-in (remembered on this browser; ?notour turns that off) and any time from his
// button at the bottom right. Steps hidden for the chosen view (roles.js) are skipped. Plain module, no build step;
// all text is set as text.

const KEY = "safeshelf-tour-seen";
const POSE = (name) => `site/assets/guide/eddy-${name}.webp`;
const POSES = ["hi", "pointing", "curious", "thinking", "excited", "thumbs", "happy", "wink", "surprised", "flying", "waving"];
const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const wait = (ms) => new Promise((r) => setTimeout(r, calm() ? 0 : ms));
const $id = (id) => document.getElementById(id);
const openTab = (id) => { const t = $id(`tab-${id}`); if (t && t.getAttribute("aria-selected") !== "true") t.click(); };
const setField = (form, name, value) => { const f = form?.elements[name]; if (f) { f.value = value; f.dispatchEvent(new Event("input", { bubbles: true })); } };
// the shop-page panel shows two choices first (app.js), then the test browser or the real one
const shopMode = () => $id("shop-page")?.dataset.mode;
const toTestPages = () => { if (shopMode() === "choose") $id("test-start")?.click(); };
const toChoices = () => { if (shopMode() === "test" && !$id("real-row")?.hidden) $id("mode-back")?.click(); };

// Every feature, in page order. chapter: shown as a topic chip; tab: the Try it tab the step opens; prep: puts the
// panel in the right state; keys: words a question about it would contain; show: a button that does it for you.
const STEPS = [
  { id: "hello", target: ".jhero", pose: "hi", title: "Hi, I'm Eddy!",
    say: "I'm your safety wingman. SafeShelf answers two questions about any product listing: is it safe, and is it real? I'll walk you through every feature on this page, and I can work it for you. Follow along with Next, pick a topic, or ask me anything below.",
    keys: ["hello", "hi eddy", "what is safeshelf", "who are you eddy", "start over", "about", "help"] },
  { id: "facts", target: ".facts", pose: "pointing", title: "Real data behind every answer",
    say: "These numbers are real: 8,689 official recalls from the US and 7 Asia-Pacific regulators, 29,379 buyer reviews read for fire, burn and shock, and answers in 26 languages. Only 2 false alarms in 40 safe products.",
    keys: ["data", "recalls", "reviews", "regulator", "source", "numbers", "how many", "countries", "cpsc", "accc", "bis", "india", "japan"] },
  { id: "views", chapter: "Your view", target: "#for", pose: "curious", title: "Pick who you are",
    say: "One engine, four people. Choose Shopper, Marketplace, Regulator or Developer and the page keeps only the parts for you, with a one-minute story of the same recalled power bank told your way.",
    keys: ["view", "who are you", "shopper", "marketplace", "seller", "regulator", "researcher", "persona", "role"] },
  { id: "answers", chapter: "How it answers", target: "#answers", pose: "thinking", title: "Four answers, never a guess",
    say: "Every listing gets one of four answers: Don't buy, Be careful, No problems found, or Can't tell yet. Plain code picks the colour from the evidence; Gemini only explains it in your language, so the AI can't change a verdict.",
    keys: ["answer", "verdict", "colour", "color", "red", "amber", "green", "grey", "gemini", "decide", "rules", "hallucinat"] },
  { id: "tabs", chapter: "Try it", target: ".trytabs", pose: "pointing", title: "Four ways to try it live",
    say: "Here's where you use the real product: on a shop page, by pasting a listing, by asking out loud, or on WhatsApp. They all call the same live API on Cloud Run.",
    keys: ["try", "demo", "ways", "tabs", "live"] },
  { id: "choose", tab: "shop-page", prep: toChoices, target: "#real-row", pose: "excited", title: "A real browser, or test pages",
    say: "Start a real Chrome with the SafeShelf extension on the real Amazon or Flipkart (5 minutes, shared), or open seven test shop pages where we already know the right answer, including a safe one that must stay quiet.",
    keys: ["real browser", "chrome", "test pages", "amazon", "flipkart", "remote"],
    show: { label: "Open the test pages", run: toTestPages } },
  { id: "samples", tab: "shop-page", prep: toTestPages, target: "#samples", pose: "pointing", title: "Seven shop pages, one per tab",
    say: "I've opened the test browser. Each tab is a listing with a known right answer: a recalled power bank, a fake charger at a fifth of the price, a borrowed safety mark, and a safe product. Click any tab to load it.",
    keys: ["sample", "test page", "fake charger", "power bank", "browser tab"] },
  { id: "omnibox", tab: "shop-page", prep: toTestPages, target: "#omnibox", pose: "curious", title: "Paste any product link",
    say: "Got a real link? Paste it in the address bar and press Enter. SafeShelf reads the page and checks it live, which can take up to two minutes.",
    keys: ["link", "url", "address bar", "paste link", "omnibox"],
    show: { label: "Put the cursor there", run: () => $id("omni-url")?.focus() } },
  { id: "check", tab: "shop-page", prep: toTestPages, target: "#ext-toggle", pose: "thumbs", title: "Press the shield to check",
    say: "This is the Chrome extension's button. Press it on any shop page and the SafeShelf panel opens with the answer, the evidence, and what to do next. You can ask follow-up questions and listen to the answer too.",
    keys: ["check button", "extension", "shield", "panel", "chrome extension", "press check"] },
  { id: "own", chapter: "Paste a listing", tab: "check-own", target: "#own", pose: "pointing", title: "Check any listing from any shop",
    say: "Copy a product's title from any shop; the price, seller and label text make the check sharper. Each live check uses one of your checks: a guest gets 1, an account 5 a day.",
    keys: ["paste", "listing", "title", "form", "own product", "quota", "limit", "how many checks", "free", "cost"],
    show: { label: "Fill in a sample for me", run: () => {
      const f = $id("own");
      setField(f, "title", "HAIARA W5PRO 10000mAh power bank");
      setField(f, "price", "2980");
      setField(f, "currency", "JPY");
      setField(f, "page_text", "Model W5PRO. Sold on amazon.co.jp.");
      f?.querySelector("button[type=submit]")?.focus({ preventScroll: true });
    } } },
  { id: "agents", tab: "check-own", target: ".own-help", pose: "thinking", title: "Eight agents, one answer",
    say: "When you press Check, you watch eight agents light up: the page reader, Is it real?, Safety Radar for reviews, the recall checker, safety marks and the twin finder. Then code sets the verdict and Gemini writes it in plain words.",
    keys: ["agent", "pipeline", "steps", "how it works", "safety radar", "twin", "recall checker", "safety mark", "certificate"] },
  { id: "ask", chapter: "Ask out loud", tab: "ask-out-loud", target: "#ask-out-loud", pose: "happy", title: "Just ask out loud",
    say: "For people who'd rather not read small print. Press Start talking, point your camera at the label and ask \"Is this safe?\". Or take one photo and hear the answer read aloud, in 26 languages.",
    keys: ["voice", "talk", "speak", "camera", "photo", "label", "out loud", "language", "hindi", "accessib", "blind", "elderly", "read aloud"] },
  { id: "wa", chapter: "WhatsApp", tab: "whatsapp", target: "#whatsapp", pose: "wink", title: "SafeShelf on WhatsApp",
    say: "Forward a shop link or a photo of the label and get the answer as a text and a voice note, in English, Hindi or 24 other languages. This chat runs on the live API; the real WhatsApp number is coming soon.",
    keys: ["whatsapp", "chat", "message", "voice note", "forward"] },
  { id: "accuracy", chapter: "Is it accurate?", target: "#accuracy", pose: "thumbs", title: "Is it accurate?",
    say: "We tested on 25 real recalls and 40 products that were never recalled. SafeShelf raised 2 false alarms; Gemini alone raised 6, and keyword rules 11.",
    keys: ["accurate", "accuracy", "false alarm", "benchmark", "results", "compare", "how good", "trust"] },
  { id: "attack", chapter: "Can it be fooled?", target: "#attack", pose: "surprised", title: "Can it be fooled?",
    say: "We attacked our own code: fake regulator pages, look-alike model numbers, hidden instructions aimed at AI. Here you can see each attack and what SafeShelf decided.",
    keys: ["fool", "attack", "red team", "hack", "prompt injection", "hidden", "security", "trick"] },
  { id: "products", chapter: "Where to use it", target: "#products", pose: "flying", title: "One engine, five ways in",
    say: "The Chrome extension, this web page, WhatsApp, catalog scans for marketplaces (49 of 50 planted problems found in 500 listings), and an API with 10 read-only MCP tools so AI shopping agents can ask the same questions.",
    keys: ["where", "products", "api", "mcp", "developer", "agent", "catalog", "scan", "rest", "integrate", "get safeshelf", "download", "install"] },
  { id: "done", target: "#products .cta", pose: "waving", title: "That's the whole tour!",
    say: "You've seen everything. Tap me at the bottom right any time to ask a question or jump back to a topic. Want to try a real product now?",
    keys: ["done", "finish", "thanks", "thank you", "bye"],
    show: { label: "Check a product live", run: () => go("own") } },
];

const store = {
  get: () => { try { return localStorage.getItem(KEY); } catch (_) { return "1"; } }, // no storage: never open by itself
  set: () => { try { localStorage.setItem(KEY, "1"); } catch (_) { /* private window */ } },
};

// A step counts if its part of the page is in the chosen view (roles.js hides the rest). Steps in a Try it tab are
// checked again once the tab is open (shown()), since a closed tab hides everything in it.
function available(step) {
  const el = document.querySelector(step.target);
  if (!el) return false;
  if (step.tab) {
    const tab = $id(`tab-${step.tab}`);
    return !!tab && !tab.hidden && !$id("try")?.hidden && !(el.hidden && el.getAttribute("role") !== "tabpanel"); // #real-row stays hidden until a browser is set up
  }
  return !el.closest("[hidden]") && el.getBoundingClientRect().height > 0;
}
const shown = (el) => !!el && !el.closest("[hidden]") && el.getBoundingClientRect().height > 0;

// how far down the sticky bars reach (the top bar, and the section links once they stick)
const barsBottom = () => Math.max(76, ...[...document.querySelectorAll("body > header.top, .jump")]
  .map((e) => [getComputedStyle(e), e.getBoundingClientRect()])
  .filter(([css, r]) => css.position === "sticky" && r.top <= (parseFloat(css.top) || 0) + 1)
  .map(([, r]) => r.bottom));

// What a question is about: the step whose words it shares most (longer words count more).
function match(text) {
  const s = ` ${text.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ")} `;
  let best = null;
  let score = 0;
  for (const step of STEPS) {
    const n = step.keys.reduce((a, k) => a + (s.includes(k) ? k.length + 4 : 0), 0);
    if (n > score) { score = n; best = step; }
  }
  return score >= 7 ? best : null;
}
// "Is the Anker A1263 safe?", "boat airdopes 141": sounds like a product, not a question about the page
const productish = (text) => /\d/.test(text) || /\b(is|are)\b.+\b(safe|real|fake|genuine|recalled)\b/i.test(text);
const productName = (text) => text.replace(/[?!.]+$/, "").replace(/^(is|are)\s+(the|this|my|a|an|these)?\s*/i, "")
  .replace(/\s+(safe|real|fake|genuine|recalled)(\s+to\s+buy)?$/i, "").replace(/\s+(it|they)$/i, "").trim();

let go = () => {};

export function setUpTour() {
  for (const p of POSES) { const i = new Image(); i.src = POSE(p); } // so Eddy never blinks out mid-flight

  // Eddy's button, bottom right, with a "Need a hand?" bubble until he has been met
  const launch = document.createElement("button");
  launch.type = "button";
  launch.className = "tg-launch";
  launch.setAttribute("aria-label", "Ask Eddy, your guide to this page");
  launch.innerHTML = `<span class="tg-hint" aria-hidden="true">Hi! Need a hand?</span><img src="${POSE("hi")}" alt="" width="68" height="68">`;
  if (!store.get()) launch.classList.add("fresh");
  document.body.append(launch);

  const shade = document.createElement("div");
  shade.className = "tg-shade";
  shade.hidden = true;
  shade.innerHTML = `<div class="tg-ring"></div>
    <div class="tg-guide">
      <img class="tg-eddy" alt="" src="${POSE("hi")}">
      <div class="tg-card" role="dialog" aria-modal="false" aria-labelledby="tg-title">
        <div class="tg-head"><img src="${POSE("happy")}" alt=""><span class="tg-who"><b>Eddy</b><small><i></i>Your safety wingman</small></span><span class="tg-count"></span><button type="button" class="tg-x" aria-label="Close the guide">×</button></div>
        <div class="tg-log">
          <p class="tg-you" hidden></p>
          <h3 id="tg-title"></h3>
          <p class="tg-say" aria-hidden="true"></p><p class="sr tg-said" aria-live="polite"></p>
          <span class="tg-typing" hidden><i></i><i></i><i></i></span>
          <div class="tg-acts"></div>
        </div>
        <form class="tg-ask" autocomplete="off"><label class="sr" for="tg-q">Ask Eddy about this page, or name a product to check</label><input id="tg-q" type="text" maxlength="200" placeholder="Ask about a feature, or name a product…"><button type="submit" aria-label="Ask"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg></button></form>
        <div class="tg-foot"><span class="tg-bar" aria-hidden="true"><i></i></span><span class="tg-btns"><button type="button" class="tg-skip">Skip</button><button type="button" class="tg-back">Back</button><button type="button" class="tg-next">Next</button></span></div>
      </div>
    </div>`;
  document.body.append(shade);

  const q = (sel) => shade.querySelector(sel);
  const ring = q(".tg-ring");
  const guide = q(".tg-guide");
  const eddy = q(".tg-eddy");
  let steps = [];
  let at = 0;
  let target = null;
  let frame = 0;
  let talk = 0; // bumps on every new message, so an older one stops typing
  let lastFocus = null;

  const pose = (name) => { const src = POSE(name); if (!eddy.src.endsWith(src)) eddy.src = src; };

  function place() {
    if (shade.hidden || !target) return;
    const r = target.getBoundingClientRect();
    const pad = 8;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const bars = barsBottom();
    const top = Math.min(Math.max(r.top - pad, bars + 6), vh - 48);
    const bottom = Math.max(Math.min(r.bottom + pad, vh - 8), top + 40);
    Object.assign(ring.style, { top: `${top}px`, left: `${Math.max(r.left - pad, 6)}px`, width: `${Math.min(r.width + 2 * pad, vw - 12)}px`, height: `${bottom - top}px` });
    if (vw < 640) { guide.classList.add("docked"); guide.style.left = guide.style.top = ""; return; }
    guide.classList.remove("docked");
    const gw = guide.offsetWidth;
    const gh = guide.offsetHeight;
    const gap = 20;
    const eddyRoom = 70; // Eddy stands off the card's left edge
    // beside the ring if there is room, else tucked into its bottom-right corner, always on screen
    let x = r.right + gap + eddyRoom;
    let y = top;
    if (x + gw > vw - 16) x = r.left - gw - gap;
    if (x < 16 + eddyRoom) { x = Math.min(r.right, vw) - gw - 24; y = bottom - gh - 24; }
    x = Math.min(Math.max(x, 16 + eddyRoom), vw - gw - 16);
    y = Math.min(Math.max(y, bars + 14), vh - gh - 16);
    guide.style.left = `${x}px`;
    guide.style.top = `${y}px`;
  }
  const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(place); };

  // Eddy thinks for a moment, then types the message word by word (screen readers get it whole, once).
  async function speak(text, stance, acts = []) {
    const me = ++talk;
    const say = q(".tg-say");
    const typing = q(".tg-typing");
    const box = q(".tg-acts");
    say.textContent = "";
    q(".tg-said").textContent = "";
    box.replaceChildren();
    typing.hidden = false;
    pose("thinking");
    schedule();
    await wait(600);
    if (me !== talk) return;
    typing.hidden = true;
    pose(stance);
    eddy.classList.remove("land"); void eddy.offsetWidth; eddy.classList.add("land");
    const words = text.split(" ");
    for (let i = 0; i < words.length && !calm(); i++) {
      if (me !== talk) return;
      say.textContent = words.slice(0, i + 1).join(" ");
      if (i % 4 === 0) schedule();
      await wait(/[.,:;?]$/.test(words[i]) ? 90 : 26);
    }
    if (me !== talk) return;
    say.textContent = text;
    q(".tg-said").textContent = text;
    box.replaceChildren(...acts);
    schedule();
  }

  const chip = (label, onclick, cls = "") => Object.assign(document.createElement("button"), { type: "button", className: `tg-chip ${cls}`.trim(), textContent: label, onclick });
  const topics = () => steps.filter((s) => s.chapter).map((s) => chip(s.chapter, () => go(s.id)));

  async function show(i, asked = "", dir = 1) {
    const step = steps[i];
    if (!step) return close();
    if (step.tab) openTab(step.tab);
    step.prep?.();
    const el = document.querySelector(step.target);
    if (!shown(el)) { // not on screen in this state (say, no real browser configured): move on in the same direction
      const n = i + dir;
      return n >= 0 && n < steps.length ? show(n, asked, dir) : close();
    }
    at = i;
    target = el;
    q(".tg-count").textContent = `${i + 1} / ${steps.length}`;
    q(".tg-bar i").style.width = `${((i + 1) / steps.length) * 100}%`;
    q("#tg-title").textContent = step.title;
    const you = q(".tg-you");
    you.hidden = !asked;
    you.textContent = asked;
    q(".tg-back").hidden = i === 0;
    q(".tg-skip").hidden = i === steps.length - 1;
    q(".tg-next").textContent = i === steps.length - 1 ? "Done" : "Next";
    // fly there: Eddy takes off, the page brings the part out from under the sticky bars, then he lands and talks
    const me = ++talk;
    pose("flying");
    guide.classList.add("moving");
    q(".tg-say").textContent = "";
    q(".tg-acts").replaceChildren();
    await new Promise((r) => requestAnimationFrame(r));
    const r = el.getBoundingClientRect();
    const bars = Math.max(barsBottom(), (document.querySelector(".jump")?.offsetHeight || 0) + 76) + 20;
    const tall = r.height > window.innerHeight - bars - 40 || window.innerWidth < 640; // phones: above the docked card
    const y = window.scrollY + r.top - (tall ? bars : Math.max(bars, (window.innerHeight - r.height) / 2));
    window.scrollTo({ top: Math.max(0, y), behavior: calm() ? "auto" : "smooth" });
    schedule();
    await wait(480);
    if (me !== talk) return;
    guide.classList.remove("moving");
    const acts = [];
    if (step.show) acts.push(chip(step.show.label, () => { step.show.run(); setTimeout(schedule, 400); }, "do"));
    if (step.id === "hello") acts.push(...topics());
    speak(step.say, step.pose, acts);
  }

  go = (id, asked = "") => {
    if (shade.hidden) open(false);
    const i = steps.findIndex((s) => s.id === id);
    if (i >= 0) show(i, asked);
  };

  function answer(text) {
    const asked = text.trim();
    if (!asked) return;
    const said = `You asked: “${asked}”`;
    const step = match(asked);
    if (step && steps.includes(step) && !productish(asked)) return go(step.id, said);
    const you = q(".tg-you");
    you.hidden = false;
    you.textContent = said;
    if (productish(asked) && steps.some((s) => s.id === "own")) {
      const name = productName(asked) || asked;
      q("#tg-title").textContent = "Let's check it for real";
      return speak(`That sounds like a product. I won't guess, but the live check can tell you: eight agents and Gemini, with the evidence. I'll put "${name}" in the form. Add the price and seller if you have them, then press Check it live.`, "excited",
        [chip("Put it in the form", async () => {
          go("own", said);
          await wait(700);
          setField($id("own"), "title", name);
          $id("own")?.querySelector("button[type=submit]")?.focus({ preventScroll: true });
        }, "do")]);
    }
    if (step && steps.includes(step)) return go(step.id, said);
    q("#tg-title").textContent = "Hmm, I'm not sure about that one";
    speak("I know this page best. Here's what I can show you:", "curious", topics());
  }

  function open(fromStart = true) {
    steps = STEPS.filter(available);
    if (!steps.length) return;
    lastFocus = document.activeElement;
    store.set();
    launch.classList.remove("fresh");
    launch.hidden = true;
    shade.hidden = false;
    document.documentElement.classList.add("tg-on");
    if (fromStart) show(0);
    q(".tg-next").focus({ preventScroll: true });
  }

  function close() {
    talk++;
    shade.hidden = true;
    launch.hidden = false;
    target = null;
    document.documentElement.classList.remove("tg-on");
    lastFocus?.focus?.({ preventScroll: true });
  }

  launch.addEventListener("click", () => open());
  q(".tg-x").addEventListener("click", close);
  q(".tg-skip").addEventListener("click", close);
  q(".tg-back").addEventListener("click", () => show(at - 1, "", -1));
  q(".tg-next").addEventListener("click", () => (at < steps.length - 1 ? show(at + 1) : close()));
  q(".tg-ask").addEventListener("submit", (e) => { e.preventDefault(); const f = q("#tg-q"); answer(f.value); f.value = ""; });
  document.addEventListener("keydown", (e) => {
    if (shade.hidden) return;
    if (e.key === "Escape") return close();
    if (e.target.closest?.("input, textarea, select")) return; // typing a question
    if (e.key === "ArrowRight" && at < steps.length - 1) show(at + 1);
    else if (e.key === "ArrowLeft" && at > 0) show(at - 1, "", -1);
  });
  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);

  // first visit on this browser: open by itself once the page has drawn its views
  if (!store.get() && !new URLSearchParams(location.search).has("notour")) setTimeout(() => open(), 1200);
  return { open, go };
}
