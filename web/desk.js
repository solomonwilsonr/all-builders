// The "Try a sample" desktop: a Mac-style menu bar with the real time, and the shop page inside the browser window,
// built from the sample's real listing (the same title, price, seller and page text the API is sent).
// Nothing here is made up beyond the page's look: no ratings, reviews or images that are not in the listing.

const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.includes("-") || k === "role") e.setAttribute(k, v);
    else e[k] = v;
  }
  e.append(...kids.filter((k) => k !== null && k !== undefined && k !== false));
  return e;
};

export function startClock() {
  const date = document.getElementById("mac-date");
  const time = document.getElementById("mac-time");
  if (!date || !time) return;
  const tick = () => {
    const now = new Date();
    date.textContent = now.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
    time.textContent = now.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  };
  tick();
  setInterval(tick, 15000);
}

const hostOf = (url) => { try { return new URL(url).hostname.replace(/^www\./, ""); } catch (_) { return ""; } };
const storeOf = (host) => (/amazon\./.test(host) ? "a" : /flipkart\./.test(host) ? "f" : "s");
const money = (price, currency) => {
  if (price === undefined || price === null || price === "") return "";
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: currency || "INR", maximumFractionDigits: 0 }).format(price); }
  catch (_) { return `${currency || ""} ${price}`; }
};

// A simple drawing of the kind of product named in the title (the listings carry no photos).
function productArt(title = "") {
  const t = title.toLowerCase();
  const kind = /kettle|ケトル/.test(t) ? "kettle" : /power ?bank|バッテリー|10000mah/.test(t) ? "bank" : "charger";
  const svg = {
    charger: '<rect x="34" y="20" width="92" height="104" rx="18" class="pa-body"/><rect x="58" y="124" width="10" height="20" rx="2" class="pa-pin"/><rect x="92" y="124" width="10" height="20" rx="2" class="pa-pin"/><rect x="62" y="44" width="36" height="10" rx="5" class="pa-port"/><rect x="62" y="62" width="36" height="10" rx="5" class="pa-port"/><circle cx="80" cy="100" r="5" class="pa-led"/>',
    bank: '<rect x="44" y="14" width="72" height="132" rx="16" class="pa-body"/><rect x="66" y="22" width="28" height="7" rx="3.5" class="pa-port"/><circle cx="68" cy="128" r="3.5" class="pa-led"/><circle cx="80" cy="128" r="3.5" class="pa-led"/><circle cx="92" cy="128" r="3.5" class="pa-led"/>',
    kettle: '<path d="M46 52h66l8 84H38z" class="pa-body"/><path d="M112 66c18 0 22 12 22 26s-6 24-18 26" fill="none" class="pa-handle"/><path d="M46 52 34 36h22" fill="none" class="pa-handle"/><rect x="40" y="136" width="80" height="10" rx="4" class="pa-pin"/>',
  }[kind];
  const wrap = el("div", { className: "pa", "aria-hidden": "true" });
  wrap.innerHTML = `<svg viewBox="0 0 160 160">${svg}</svg>`;
  return wrap;
}

// The text a listing hides from people but not from AI readers (the fake-shop test case).
const HIDDEN = /ignore (all |your )?previous instructions|verified safe|system prompt/i;

// bare: only the shop page, for the real extension to read (web/ext-frame.html). The sample's note and the expected
// answer stay outside it, so they never reach the check; the hidden AI text is really hidden, as on the real page.
export function renderPage(box, { listing = {}, preset = null, index = 0, total = 0, bare = false } = {}) {
  const host = hostOf(listing.url);
  const store = storeOf(host);
  box.className = `store store-${store}`;
  const lines = String(listing.page_text || "").split("\n").map((l) => l.trim()).filter(Boolean);
  const shown = lines.filter((l) => !HIDDEN.test(l));
  const hidden = lines.filter((l) => HIDDEN.test(l));

  const note = preset
    ? el("div", { className: "demo-note" },
        el("b", { textContent: `Sample ${index + 1} of ${total}` }),
        el("span", { textContent: preset.what }),
        el("span", { className: "exp", textContent: `Expected: ${preset.expect.label}` }))
    : el("div", { className: "demo-note" }, el("b", { textContent: "Your link" }),
        el("span", { textContent: "SafeShelf is checking this page live from its link." }));

  const head = el("header", { className: "s-head" },
    el("span", { className: "s-logo", textContent: host || "shop" }),
    el("span", { className: "s-search", textContent: "Search products" }),
    el("span", { className: "s-cart", textContent: "Cart" }));

  const info = el("div", { className: "s-info" },
    preset && !bare ? el("p", { className: "s-market", textContent: preset.market }) : null,
    el(bare ? "h1" : "h3", { className: "s-title", id: bare ? "title" : "", textContent: listing.title || listing.url || "Product page" }),
    listing.seller ? el("p", { className: "s-seller" }, "Sold by ", el("span", { id: bare ? "seller" : "", textContent: listing.seller })) : null,
    listing.price !== undefined ? el("p", { className: "s-price", id: bare ? "price" : "", textContent: money(listing.price, listing.currency) }) : null,
    el("div", { className: "s-btns" }, el("span", { className: "s-cartbtn", textContent: "Add to cart" }), el("span", { className: "s-buy", textContent: "Buy now" })),
    shown.length ? el("div", { className: "s-details" }, el("p", { className: "s-dt", textContent: "Product details" }),
      el("ul", {}, ...shown.map((l) => el("li", { textContent: l })))) : null,
    hidden.length && bare ? el("div", { className: "s-offscreen", "aria-hidden": "true", textContent: hidden.join(" ") }) : null,
    hidden.length && !bare ? el("div", { className: "s-hidden" },
      el("p", { className: "s-hidden-label", textContent: "Hidden on the real page (white text on white), but read by AI:" }),
      ...hidden.map((l) => el("p", { className: "s-hidden-text", textContent: l }))) : null);

  if (bare) { box.replaceChildren(head, el("div", { className: "s-main" }, productArt(listing.title), info)); return; }
  box.replaceChildren(note, head, el("div", { className: "s-main" }, productArt(listing.title), info),
    el("p", { className: "s-foot", textContent: preset
      ? "A demo page built from this test case's listing. Kelvo, SafeVolt, VoltNova, Zorvana and MegaDealz24 are fictional; the recalls and registries checked are real."
      : "Only the link was sent. The API reads the product area and filters out personal details." }));
  box.scrollTop = 0;
}

export function setAddress(url) {
  const input = document.getElementById("omni-url");
  if (input) input.value = url || "";
  const lock = document.getElementById("omni-host");
  if (lock) lock.textContent = hostOf(url);
}
