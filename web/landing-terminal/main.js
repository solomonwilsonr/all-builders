// Kasauti for Builders. Nothing here is tied to scrolling: each part answers a click or a key.
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Pixel art for the hero cells, drawn from small character maps
  const PX = {
    shield: ["..XXXX..", ".XXXXXX.", "XXXXXXXX", "XXX..XXX", "XXX..XXX", ".XXXXXX.", "..XXXX..", "...XX..."],
    plug: [".X...X.", ".X...X.", "XXXXXXX", "XXXXXXX", "XX.X.XX", ".XXXXX.", "..XXX..", "...X...", "...X..."],
    ring: ["..XXXX..", ".X....X.", "X..XX..X", "X.X..X.X", "X.X..X.X", "X..XX..X", ".X....X.", "..XXXX.."],
  };
  document.querySelectorAll(".px").forEach((el) => {
    const map = PX[el.dataset.px], w = map[0].length, h = map.length;
    let rects = "";
    map.forEach((row, y) => [...row].forEach((ch, x) => { if (ch === "X") rects += `<rect x="${x}" y="${y}" width="1" height="1"/>`; }));
    el.innerHTML = `<svg viewBox="0 0 ${w} ${h}" style="fill:${el.dataset.c}">${rects}</svg>`;
  });
  document.querySelectorAll(".checker").forEach((c) => { c.innerHTML = "<i></i>".repeat(12); });

  // Light and dark: follow the system until the visitor picks one, and press T to switch
  const root = document.documentElement;
  const themeBtn = document.getElementById("theme");
  const toggleTheme = () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("kasauti-builders-theme", root.dataset.theme); } catch (_) {}
  };
  themeBtn.addEventListener("click", toggleTheme);
  themeBtn.dataset.key = "t";

  // Phones and tablets cannot add a browser extension: show them their own buttons and words
  const phoneQuery = matchMedia("(hover: none) and (pointer: coarse), (max-width: 640px)");
  const setPhone = () => root.classList.toggle("is-phone", phoneQuery.matches);
  setPhone();
  phoneQuery.addEventListener("change", setPhone);

  // On a phone, "Add to Chrome" copies this page's link so it can be opened on a computer
  const toast = document.getElementById("toast");
  let toastTimer;
  const say = (html, ms = 5000) => {
    toast.innerHTML = html;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, ms);
  };
  const pageUrl = () => document.body.dataset.shareUrl || location.href.split("#")[0];
  document.querySelectorAll(".get").forEach((a) => a.addEventListener("click", (e) => {
    if (!root.classList.contains("is-phone")) return;
    e.preventDefault();
    const url = pageUrl();
    const done = () => say("<b>Link copied.</b> Open it in Chrome on your computer to add Kasauti.");
    const shown = () => say(`Open this link in Chrome on your computer:<span class="url-text">${esc(url)}</span>`, 12000);
    try { navigator.clipboard.writeText(url).then(done, shown); } catch (_) { shown(); }
  }));

  // Copy the clone command
  document.querySelectorAll(".copy").forEach((b) => b.addEventListener("click", async () => {
    const note = b.querySelector(".copied");
    try { await navigator.clipboard.writeText(b.dataset.copy); note.textContent = "Copied"; }
    catch (_) { note.textContent = b.dataset.copy; }
    note.classList.add("show");
    setTimeout(() => note.classList.remove("show"), 1600);
  }));

  // Keyboard shortcuts shown on the buttons
  addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || /input|textarea|select/i.test(e.target.tagName)) return;
    const btn = document.querySelector(`[data-key="${e.key.toLowerCase()}"]`);
    if (!btn) return;
    btn.classList.add("flash");
    setTimeout(() => btn.classList.remove("flash"), 300);
    btn.click();
  });

  // 02: the inspector
  const CHECKS = {
    photos: {
      kv: [["Check", "copied_photos"], ["Result", "flag"], ["Matches official listing", "true"], ["Seller authorised", "false"]],
      body: { copied_photos: { result: "flag", matches_official_listing: true, seller_authorised: false } },
    },
    price: {
      kv: [["Check", "price"], ["Result", "flag"], ["Price", "₹299"], ["Lowest credible price", "₹1,399"]],
      body: { price: { result: "flag", price: 299, currency: "INR", lowest_credible_price: 1399, ratio: 0.21 } },
    },
    age: {
      kv: [["Check", "website_age"], ["Result", "flag"], ["Shop registered", "19 days ago"]],
      body: { website_age: { result: "flag", domain_registered_days_ago: 19 } },
    },
    spec: {
      kv: [["Check", "spec"], ["Result", "ok"], ["Conflicts", "none"]],
      body: { spec: { result: "ok", conflicts: [] } },
    },
    safety: {
      kv: [["Check", "safety of the genuine model"], ["Status", "under review"], ["Hazard reports", "9"], ["Recall", "none"]],
      body: { safety_of_genuine_model: "9 hazard reports under review, no recall", evidence_ids: ["EV-201", "EV-207"] },
    },
  };
  const paint = (obj) => esc(JSON.stringify(obj, null, 2))
    .replace(/"([^"]+)":/g, '<span class="k">"$1"</span>:')
    .replace(/: "([^"]*)"/g, ': <span class="s">"$1"</span>')
    .replace(/"(EV-[^"]+)"/g, '<span class="s">"$1"</span>')
    .replace(/: (-?\d+(\.\d+)?)/g, ': <span class="n">$1</span>')
    .replace(/: (true|false)/g, ': <span class="b">$1</span>');
  const kv = document.querySelector(".kv");
  const body = document.querySelector(".json code");
  const show = (id) => {
    const c = CHECKS[id];
    kv.replaceChildren(...c.kv.flatMap(([k, v]) => [Object.assign(document.createElement("dt"), { textContent: k }), Object.assign(document.createElement("dd"), { textContent: v })]));
    body.innerHTML = paint(c.body);
  };
  document.querySelectorAll(".row").forEach((r) => r.addEventListener("click", () => {
    document.querySelectorAll(".row").forEach((x) => { const on = x === r; x.classList.toggle("on", on); x.setAttribute("aria-selected", String(on)); });
    show(r.dataset.check);
  }));
  show("photos");

  // 04: the terminal types the chosen example
  const API = "https://safeshelf-api-368488022657.asia-south1.run.app";
  const SCRIPTS = {
    check: [
      ["p", "agent › "], ["", "is this charger real? amazon.in/dp/B0CX65SFC\n\n"],
      ["t", "● kasauti.check_listing"], ["c", '(url="amazon.in/dp/B0CX65SFC")\n'],
      ["c", "  ⎿ "], ["w", "copied_photos  flag"], ["c", "  seller not authorised\n"],
      ["c", "    "], ["w", "price          flag"], ["c", "  21% of ₹1,399\n"],
      ["c", "    "], ["w", "website_age    flag"], ["c", "  19 days\n"],
      ["c", "    "], ["ok", "spec           ok\n\n"],
      ["", "Be careful: photos copied from the official listing, price far\nbelow the genuine product, website only 19 days old.\n"],
    ],
    safety: [
      ["p", "agent › "], ["", "any safety problems with SS-P-10291?\n\n"],
      ["t", "● kasauti.product_safety"], ["c", '(product_id="SS-P-10291")\n'],
      ["c", "  ⎿ "], ["w", "status    under review"], ["c", "\n    reports   9 (USB-C port overheating)\n    recall    none\n    evidence  EV-201, EV-207\n\n"],
      ["", "No recall, but 9 hazard reports are under review. Keep it out\nof children's reach until the review is done.\n"],
    ],
    copies: [
      ["p", "agent › "], ["", "who else sells this same charger?\n\n"],
      ["t", "● kasauti.find_copies"], ["c", '(product_id="SS-P-10291")\n'],
      ["c", "  ⎿ "], ["ok", "verified  "], ["c", "CX-65 · Appario Retail · ₹1,349\n    "], ["w", "possible  "], ["c", "CX-65 · MegaDealz24 · ₹299 (photos copied)\n    "], ["w", "possible  "], ["c", "65W Fast · QuickKart · ₹259\n\n"],
      ["", "One verified seller. Two listings use the same photos at a\nfraction of the price.\n"],
    ],
    rest: [
      ["p", "$ "], ["", `curl -s -X POST ${API.replace("https://", "")}\\\n    /v1/listings/trust-check \\\n    -H 'content-type: application/json' \\\n    -d '{"url": "amazon.in/dp/B0CX65SFC"}'\n\n`],
      ["c", "{\n  "], ["t", '"matched_product_id"'], ["c", ': "SS-P-10291",\n  '], ["t", '"summary"'], ["c", ': "Be careful: photos copied from the official\n    listing, price far below the genuine product, website only\n    19 days old.",\n  '], ["t", '"label"'], ["c", ': "Evidence for the shopper - not a legal finding"\n}\n'],
    ],
  };
  const term = document.getElementById("term");
  let run = 0;
  const type = async (name) => {
    const me = ++run;
    term.innerHTML = "";
    for (const [cls, text] of SCRIPTS[name]) {
      const span = document.createElement("span");
      if (cls) span.className = cls;
      term.appendChild(span);
      if (reduce) { span.textContent = text; continue; }
      const step = cls === "c" || cls === "" ? 2 : 1;
      for (let i = 0; i < text.length; i += step) {
        if (me !== run) return;
        span.textContent = text.slice(0, i + step);
        await new Promise((r) => setTimeout(r, cls === "p" ? 40 : 9));
      }
    }
  };
  // the first example is already there when the page opens; typing happens on a click
  SCRIPTS.check.forEach(([cls, text]) => term.appendChild(Object.assign(document.createElement("span"), { className: cls, textContent: text })));
  document.querySelectorAll(".cmd").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".cmd").forEach((x) => { const on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-selected", String(on)); });
    type(b.dataset.cmd);
  }));

  // The moving dot stays still for anyone who asked for less motion
  if (reduce) document.querySelectorAll("animateMotion").forEach((a) => a.remove());
})();
