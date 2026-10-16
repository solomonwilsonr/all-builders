// Kasauti landing page behaviour. No scroll-driven motion: everything here answers a click or a keystroke,
// and without it every section is still readable.
(() => {
  const root = document.documentElement;
  const store = {
    get: (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch (_) {} },
  };

  // Light and dark: follow the system until the visitor picks one
  const isDark = () => root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  document.getElementById("theme").addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    root.dataset.theme = next;
    store.set("kasauti-theme", next);
  });

  // Phones and tablets cannot add a browser extension: show them their own buttons and words
  const phoneQuery = matchMedia("(hover: none) and (pointer: coarse), (max-width: 640px)");
  const setPhone = () => root.classList.toggle("is-phone", phoneQuery.matches);
  setPhone();
  phoneQuery.addEventListener("change", setPhone);

  // On a phone, "Add to Chrome" copies this page's link so it can be opened on a computer
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
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

  // The notice at the top can be closed
  const notice = document.getElementById("announce");
  if (store.get("kasauti-notice") === "closed") notice.hidden = true;
  notice.querySelector(".announce-x").addEventListener("click", () => { notice.hidden = true; store.set("kasauti-notice", "closed"); });

  // Mark one chip in a row as chosen
  const choose = (chip) => chip.parentElement.querySelectorAll(".chip").forEach((c) => {
    const on = c === chip; c.classList.toggle("on", on); c.setAttribute("aria-selected", String(on));
  });

  // Chat: English or Hindi
  document.querySelectorAll(".chat .chip").forEach((chip) => chip.addEventListener("click", () => {
    choose(chip);
    document.querySelectorAll("[data-thread]").forEach((t) => { t.hidden = t.dataset.thread !== chip.dataset.lang; });
  }));

  // Steps: a product page or a search page, one card at a time
  const steps = document.querySelector(".steps");
  const decks = [...steps.querySelectorAll(".deck")];
  const dots = steps.querySelector(".dots");
  const [prev, next] = steps.querySelectorAll(".arrow");
  const deck = () => decks.find((d) => !d.hidden);
  const at = () => { const d = deck(); return Math.round(d.scrollLeft / (d.firstElementChild.offsetWidth + 14)); };
  const sync = () => {
    const d = deck(), n = d.children.length, i = Math.min(at(), n - 1);
    if (dots.children.length !== n) dots.replaceChildren(...Array.from({ length: n }, () => document.createElement("i")));
    [...dots.children].forEach((dot, k) => dot.classList.toggle("on", k === i));
    prev.disabled = i <= 0;
    next.disabled = d.scrollLeft + d.clientWidth >= d.scrollWidth - 4;
  };
  const go = (dir) => { const d = deck(); d.scrollBy({ left: dir * (d.firstElementChild.offsetWidth + 14), behavior: "smooth" }); };
  prev.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));
  decks.forEach((d) => d.addEventListener("scroll", () => requestAnimationFrame(sync), { passive: true }));
  steps.querySelectorAll(".chip").forEach((chip) => chip.addEventListener("click", () => {
    choose(chip);
    decks.forEach((d) => { d.hidden = d.dataset.set !== chip.dataset.set; if (!d.hidden) d.scrollLeft = 0; });
    sync();
  }));
  addEventListener("resize", sync);
  sync();

  // The live verdict: the same rules the engine uses, run on the listing as it is typed
  const input = document.getElementById("listing");
  const card = document.querySelector(".verdict");
  const word = card.querySelector(".verdict-word");
  const ring = card.querySelector(".ring");
  const lines = card.querySelector(".verdict-lines");
  const GENUINE = 1399;
  const AUTHORISED = ["examplebrand official store", "appario retail"];
  const LOOK = {
    green: ["Looks fine so far", "--v-green", "green"],
    amber: ["Be careful", "--v-amber", "amber"],
    red: ["Danger: likely not genuine", "--v-red", "red"],
    unknown: ["Not enough evidence yet", "--v-grey", "grey"],
  };
  const SAMPLES = {
    genuine: "65W Super Fast Charger, CX-65 Original\nPrice ₹1,349\nSold by Appario Retail\nShop opened 2,140 days ago\nPhotos: the brand's own",
    blank: "65W Super Fast Charger, CX-65 Original\nSold by QuickKart Deals\nPhotos: same as the brand's listing",
  };
  const judge = () => {
    const t = input.value;
    const price = Number((t.match(/₹\s?([\d,]+)/) || [])[1]?.replace(/,/g, ""));
    const seller = (t.match(/sold by\s+(.+)/i) || [])[1]?.trim() || "";
    const days = Number((t.match(/opened\s+([\d,]+)\s+day/i) || [])[1]?.replace(/,/g, ""));
    const copied = /photos:\s*same as/i.test(t);
    const authorised = AUTHORISED.includes(seller.toLowerCase());
    const out = [];
    let flags = 0;
    if (!price) out.push("No price found, so the price could not be checked.");
    else if (price / GENUINE < 0.5) { flags++; out.push(`Price is ${Math.round((100 * price) / GENUINE)}% of the genuine ₹1,399.`); }
    else out.push("Price is close to the genuine product's.");
    if (copied && !authorised) { flags++; out.push("Photos are copied from the brand's listing, and this seller is not an authorised one."); }
    else if (authorised) out.push(`${seller} is an authorised seller.`);
    if (Number.isFinite(days) && days < 90) { flags++; out.push(`The shop opened only ${days} days ago.`); }
    else if (Number.isFinite(days)) out.push("The shop has been open for years.");
    const level = !price ? "unknown" : flags >= 2 ? "red" : flags === 1 ? "amber" : "green";
    const [w, token, ringClass] = LOOK[level];
    word.textContent = w;
    card.style.setProperty("--v", `var(${token})`);
    ring.className = `ring big ${ringClass}`;
    ring.querySelector(".ar").style.setProperty("--arc", level === "unknown" ? 40 : 138);
    lines.replaceChildren(...out.map((s) => Object.assign(document.createElement("li"), { textContent: s })));
  };
  input.addEventListener("input", judge);
  document.querySelectorAll("[data-fill]").forEach((b) => b.addEventListener("click", () => { input.value = SAMPLES[b.dataset.fill]; judge(); }));
  judge();
})();
