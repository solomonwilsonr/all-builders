// Reads a product page and shows a SafeShelf button (floating on product pages, one per card on results pages) that opens a card. Page text is sent as data only.
// A reloaded extension leaves an orphaned copy of this script in open tabs: clean it up, then start fresh.
try { window.__safeshelf?.cleanup(); } catch (_) { /* old context is already dead */ }
{
  const qs = (sel) => (sel ? document.querySelector(sel) : null);
  const text = (sel) => qs(sel)?.textContent.trim() || null;
  const num = (s) => {
    const m = (s || "").replace(/,/g, "").match(/(\d+(\.\d+)?)/);
    return m ? Number(m[1]) : undefined;
  };

  // schema.org Product data: the most stable source on most shops
  const jsonLd = () => {
    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const j = JSON.parse(s.textContent);
        const p = [].concat(j, j["@graph"] || []).find((i) => i && [].concat(i["@type"]).includes("Product"));
        if (p) return p;
      } catch (_) { /* not valid JSON, skip */ }
    }
    return null;
  };

  // One entry per shop. Selectors are best effort: shops change them, so each has fallbacks.
  const GENERIC = {
    isProduct: () => !document.body?.hasAttribute("data-safeshelf-skip"), // e.g. the chat test console (demo/chat.html)
    title: "h1",
    price: null,
    seller: null,
    images: "meta[property='og:image']",
    anchor: "h1",
    cards: null,
  };
  const SITES = [
    {
      match: (h) => /(^|\.)amazon\.(in|com|co\.jp|com\.au|sg)$/.test(h),
      isProduct: () => /\/(dp|gp\/product)\/[A-Z0-9]{10}/.test(location.pathname),
      title: "#productTitle",
      price: "#corePrice_feature_div .a-offscreen, #apex_desktop .a-offscreen, .a-price .a-offscreen",
      seller: "#sellerProfileTriggerId, #tabular-buybox [tabular-attribute-name='Sold by'] .tabular-buybox-text, #merchant-info",
      mainImage: "#landingImage, #imgTagWrapperId img",
      images: "#altImages img",
      // Only these product areas are sent as text. The header (which shows your name and delivery address) is never read.
      facts: "#bylineInfo, #acrPopover, #corePrice_feature_div, #productOverview_feature_div, #feature-bullets, #tabular-buybox, #buybox, #desktop_buybox, #productDescription",
      // Brand, model number, manufacturer, country of origin, specs: the data the engine matches on.
      details: "#prodDetails, #productDetails_feature_div, #productDetails_techSpec_section_1, #productDetails_techSpec_section_2, #productDetails_detailBullets_sections1, #technicalSpecifications_section_1, #detailBullets_feature_div",
      anchor: "#corePrice_feature_div, #apex_desktop, #title_feature_div",
      cards: { selector: "[data-component-type='s-search-result'][data-asin]:not([data-asin=''])", title: "h2", price: ".a-price .a-offscreen", link: "h2 a, a[href*='/dp/']", image: "img.s-image" },
      // The reviews shown on the page, for "Is it safe?" on products SafeShelf has no data for. Never the reviewer's name.
      reviews: { item: "[data-hook='review']", title: "[data-hook='review-title'] span:not(.a-letter-space):not(.a-icon-alt), [data-hook='reviewTitle']", body: "[data-hook='reviewRichContentContainer'], [data-hook='review-body'], [data-hook='reviewText']", rating: "[data-hook='review-star-rating'], [data-hook='cmps-review-star-rating']", date: "[data-hook='review-date']" }, // Amazon's 2025 and 2026 markup
    },
    {
      match: (h) => /(^|\.)flipkart\.com$/.test(h),
      isProduct: () => /\/p\/itm/.test(location.pathname) || location.search.includes("pid="),
      title: "h1",
      price: null, // class names are obfuscated and change often; use schema.org data, then the first rupee amount
      seller: "#sellerName span, #sellerName",
      images: "img[src*='rukminim']",
      anchor: "h1",
      cards: { selector: "div[data-id]", title: "a[title]", price: null, link: "a[href*='/p/']", image: "img[src*='rukminim']" },
    },
    {
      match: (h) => h === "localhost",
      isProduct: () => !!document.body.dataset.safeshelfListingId,
      title: "#title",
      price: "#price",
      seller: "#seller",
      images: "#gallery img",
      anchor: "#price",
      hiddenText: true, // demo pages carry a hidden prompt-injection test
      reviews: { item: "article.review", title: "strong", body: "p", rating: ".stars", date: "time" },
      cards: { selector: ".result[data-listing-id]", title: ".result-title", price: ".result-price", link: "a", image: "img" },
    },
  ];
  const site = SITES.find((s) => s.match(location.hostname)) || GENERIC;

  // Keeps personal details out of what is sent: delivery address, account name, emails, phone numbers.
  const PRIVATE_LINE = /^(deliver(ing)? to\b|hello,|hi,|your account|sign in|[A-Za-z .]+ [1-9]\d{5}$)/i;
  // Buttons and delivery noise that says nothing about the product.
  const NOISE_LINE = /^(add to cart|buy now|quantity:?\s*\d*|this will be a gift|add to wish list|add additional items|payment|secure transaction|details|price history|overnight|in stock|free delivery\b.*|link device to your amazon.*)$/i;
  // `seen` is shared between sections so a long line is sent once. Short lines are kept: they are labels paired with values.
  const scrub = (t, seen = new Set()) =>
    t.split("\n").map((l) => l.trim())
      .filter((l) => l && (l.length > 2 || /[A-Za-z]/.test(l)) && !PRIVATE_LINE.test(l) && !NOISE_LINE.test(l))
      .filter((l) => l.length < 25 || (!seen.has(l) && seen.add(l)))
      .join("\n")
      .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, "[email]")
      .replace(/(?<!\d)(\+?91[ -]?)?[6-9]\d{9}(?!\d)/g, "[phone]");

  // Drops tracking parameters. Amazon pages become https://host/dp/ASIN, Flipkart keeps its product id.
  const cleanUrl = () => {
    const u = new URL(location.href);
    // Local demo pages name the shop address they stand for, so the API checks that address, not localhost.
    const canonical = document.querySelector('link[rel="canonical"]')?.href;
    if (/^(localhost|127\.0\.0\.1)$/.test(u.hostname) && canonical) return canonical;
    const asin = u.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/);
    if (/amazon\./.test(u.hostname) && asin) return `${u.origin}/dp/${asin[1]}`;
    for (const k of [...u.searchParams.keys()]) {
      if (/^(utm_|ref|pd_rd|pf_rd|content-id|fbclid|gclid|_encoding|dib|crid|qid|sr$|sprefix|keywords|th$|psc)/i.test(k)) u.searchParams.delete(k);
    }
    u.hash = "";
    return u.toString();
  };

  // Text of the named sections. A section inside another selected section is skipped, so nothing is read twice.
  const textOf = (selectors) => {
    const els = selectors ? [...document.querySelectorAll(selectors)].filter((e) => e.innerText.trim()) : [];
    return els.filter((e) => !els.some((o) => o !== e && o.contains(e))).map((e) => e.innerText.trim()).join("\n");
  };
  // Text of the product area only: the named sections if the shop has them, otherwise the block around the title.
  const productText = () => {
    const named = textOf(site.facts);
    if (named) return named;
    let n = qs(site.title);
    while (n && n.parentElement && n.parentElement !== document.body && n.innerText.length < 1500) n = n.parentElement;
    return (n || document.body).innerText;
  };

  // "Sold by" label followed by the seller name, for buy boxes whose ids we do not know.
  const soldBy = () => {
    const label = [...document.querySelectorAll("span, div, a, td, th")].find((e) => !e.children.length && /^Sold by\s*:?$/i.test(e.textContent.trim()));
    for (let n = label, i = 0; n && i < 3; n = n.parentElement, i++) {
      const v = n.nextElementSibling?.textContent.trim();
      if (v && !/learn more/i.test(v)) return v;
    }
    return undefined;
  };
  const sellerName = () => {
    const bad = /learn more|^$/i;
    return [...document.querySelectorAll(site.seller || "x-none")].map((e) => e.textContent.trim()).find((t) => t && !bad.test(t)) || soldBy();
  };

  // Details tables (brand, model number, specs) found by their headings, since shops use different ids for them.
  const detailSections = (already) => {
    const heading = /^(product information|technical details|additional information|item details|product details|specifications)$/i;
    const found = [];
    for (const h of document.querySelectorAll("h1, h2, h3, h4, span.a-text-bold")) {
      if (!heading.test(h.textContent.trim())) continue;
      let n = h;
      while (n.parentElement && n.parentElement !== document.body && n.innerText.length < 200) n = n.parentElement;
      const t = n.innerText.trim().slice(0, 1500);
      if (t && !already.includes(t.slice(0, 60))) found.push(t);
      if (found.length === 2) break;
    }
    return found.join("\n");
  };

  // The shop's market (SafeShelf is JAPAC-first): its currency, from the shop's address. Prices may carry any of
  // the region's symbols.
  const MARKETS = [[/\.co\.jp$|\.jp$/, "JPY"], [/\.com\.au$|\.au$/, "AUD"], [/\.co\.nz$|\.nz$/, "NZD"], [/\.sg$/, "SGD"],
    [/\.my$/, "MYR"], [/\.co\.id$|\.id$/, "IDR"], [/\.co\.th$|\.th$/, "THB"], [/\.ph$/, "PHP"], [/\.vn$/, "VND"],
    [/\.in$|(^|\.)flipkart\.com$/, "INR"], [/(^|\.)amazon\.com$/, "USD"]];
  const shopCurrency = () => (MARKETS.find(([re]) => re.test(location.hostname)) || [null, "INR"])[1];
  const MONEY = /(?:₹|Rs\.?|¥|￥|A\$|NZ\$|S\$|US\$|\$|RM|Rp|฿|₱|₫)\s?([\d,]+(\.\d+)?)/;

  const readPage = () => {
    const ld = jsonLd();
    const offer = [].concat(ld?.offers || [])[0];
    const seen = new Set();
    const details = scrub([textOf(site.details), detailSections("")].filter(Boolean).join("\n"), seen); // model, brand, origin, specs
    const main = scrub(productText(), seen);
    const area = main;
    const rupee = area.match(MONEY);
    const asin = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/)?.[1];
    const mrp = qs(".a-price.a-text-price .a-offscreen")?.textContent.trim();
    const hidden = site.hiddenText
      ? " " + [...document.querySelectorAll("[aria-hidden='true'], [hidden]")].map((el) => el.textContent.trim()).filter(Boolean).join(" ")
      : "";
    // The main photo first (it can sit after the side thumbnails in the page), then the gallery. Only product photos: not icons or logos.
    const main_images = (sel) => [...document.querySelectorAll(sel)].map((i) => (i.src || i.content || "").replace(/\._[A-Za-z0-9_,%-]+_\.(jpg|png|webp)/, ".$1")); // thumbnail url -> full-size url
    const isPhoto = (u) => /^https?:/.test(u) && !/\/images\/G\/|icon|sprite|logo|pixel|\.gif(\?|$)/i.test(u);
    const images = [...new Set([...(site.mainImage ? main_images(site.mainImage) : []), ...main_images(site.images || "img")].filter(isPhoto))].slice(0, 8);
    return {
      url: cleanUrl(),
      title: text(site.title) || ld?.name || document.title,
      price: num(text(site.price)) ?? num(String(offer?.price ?? offer?.lowPrice ?? "")) ?? num(rupee?.[1]),
      currency: offer?.priceCurrency || shopCurrency(),
      seller: sellerName() || main.match(/^Sold by\s*\n(.+)$/m)?.[1],
      image_urls: images.length ? images : [].concat(ld?.image || []).slice(0, 8),
      // Technical details first: they identify the product. Marketing text last, so the cap cuts that, not the specs.
      page_text: [asin && `ASIN: ${asin}`, mrp && `M.R.P.: ${mrp}`, details.slice(0, 2500), area.slice(0, 1500) + hidden].filter(Boolean).join("\n").slice(0, 4200),
      reviews: readReviews(),
      listing_id: document.body.dataset.safeshelfListingId || null,
      product_id: document.body.dataset.safeshelfProductId || null,
    };
  };

  // Up to 30 reviews from the page: title, text, stars and date only. Emails and phone numbers are masked.
  // root: this page, or another page of the same shop read in the background (the critical-reviews page).
  const readReviews = (root = document) => {
    const r = site.reviews;
    if (!r) return [];
    const inside = (el, sel) => (sel ? el.querySelector(sel) : null);
    const mask = (t) => t.replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, "[email]").replace(/(?<!\d)(\+?91[ -]?)?[6-9]\d{9}(?!\d)/g, "[phone]");
    const words = (n) => (n ? (n.innerText || n.textContent || "").replace(/\s+/g, " ").trim() : "");
    return [...root.querySelectorAll(r.item)].slice(0, 30).map((el) => {
      const stars = inside(el, r.rating);
      const rating = Number((stars?.getAttribute("aria-label") || stars?.textContent || "").match(/([\d.]+) out of 5/)?.[1]) || null;
      const when = inside(el, r.date);
      const parsed = new Date(when?.getAttribute("datetime") || (when?.textContent || "").replace(/^.*\bon\s+/i, "").trim());
      return {
        title: mask(words(inside(el, r.title))).replace(/^[\d.]+ out of 5 stars\s*/, "").slice(0, 200) || null,
        text: mask(words(inside(el, r.body))).slice(0, 1500),
        rating,
        date: isNaN(parsed) ? null : parsed.toISOString().slice(0, 10),
      };
    }).filter((x) => x.text);
  };

  // Amazon shows only a few reviews on the product page, mostly positive. The product's critical (1-3 star) reviews
  // page is read here, in the shopper's own browser where they are signed in and Amazon does not block it, and its
  // reviews go first, since hazard reports live there. Remembered per product for the visit.
  const criticalCache = new Map();
  const criticalReviews = async () => {
    const asin = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/)?.[1];
    if (!asin || !/(^|\.)amazon\./.test(location.hostname)) return [];
    if (!criticalCache.has(asin)) {
      criticalCache.set(asin, (async () => {
        try {
          const res = await fetch(`/product-reviews/${asin}/?filterByStar=critical&sortBy=recent&reviewerType=all_reviews`, { credentials: "include" });
          if (!res.ok || /\/ap\/signin/.test(res.url)) return [];
          return readReviews(new DOMParser().parseFromString(await res.text(), "text/html"));
        } catch (_) { return []; }
      })());
    }
    return criticalCache.get(asin);
  };
  const withMoreReviews = async (page) => {
    const extra = await criticalReviews();
    if (!extra.length) return page;
    const seen = new Set();
    const reviews = [...extra, ...(page.reviews || [])].filter((x) => !seen.has(x.text) && seen.add(x.text)).slice(0, 30);
    return { ...page, reviews };
  };
  window.__safeshelfMoreReviews = withMoreReviews;

  // Data for one product card on a results page (no page load needed)
  const readCard = (card) => {
    const c = site.cards;
    const link = card.querySelector(c.link);
    const rupee = card.innerText.match(MONEY);
    const img = card.querySelector(c.image);
    return {
      url: link?.href || location.href,
      title: (card.querySelector(c.title)?.textContent || link?.title || img?.alt || "").trim().slice(0, 300),
      price: num(card.querySelector(c.price || "x-none")?.textContent) ?? num(rupee?.[1]),
      currency: shopCurrency(),
      image_urls: img?.src ? [img.src] : [],
      page_text: card.innerText.slice(0, 1000),
      listing_id: card.dataset.listingId || null,
      product_id: null,
    };
  };

  // Design tokens shared by every shadow root: soft pastel frames, white cards, navy ink, lime accent.
  const TOKENS = `
    :host { --ink:#13233a; --muted:#5a6a7c; --line:#e3e7ec; --soft:#f1f3f6; --card:#fdfcfa; --lime:#dff0a8; --lime-d:#c9e383; --link:#2f5fb3;
      --green:#0a6b2d; --green-bg:#e3f3e7; --amber:#8a5a00; --amber-bg:#fbefd6; --red:#b3261e; --red-bg:#fbe3e1; --unknown:#4a5560; --unknown-bg:#eceff3;
      --font:"Inter",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
      --sky:radial-gradient(120% 70% at 0% 0%, #b9d4ee 0%, transparent 60%), radial-gradient(120% 70% at 100% 100%, #f6c9b4 0%, transparent 60%), linear-gradient(180deg, #d6e4f2, #f3ddd2); }
  `;

  const PANEL_STYLE = `
    .tabs { display:flex; flex-wrap:wrap; justify-content:center; gap:6px; margin:12px 0 10px; }
    .tab { font:inherit; font-size:13px; font-weight:600; padding:6px 12px; border:1px solid var(--line); border-radius:12px; background:#fff; color:var(--ink); cursor:pointer; transition:background-color .12s ease; }
    .tab:hover { background:var(--soft); }
    .tab[aria-selected="true"] { background:var(--lime); border-color:var(--lime-d); }
    .vrow { display:flex; gap:8px; margin:6px 0; } .vrow .i { flex:none; width:1.4em; text-align:center; }
    .vrow .s { color:var(--muted); font-size:13px; } .vrow a { font-size:13px; color:var(--link); }
    .vh { font-weight:700; font-size:17px; letter-spacing:-.02em; margin:14px 0 2px; } .vnote { color:var(--muted); font-size:13px; margin:4px 0; }
    .notlive { background:var(--soft); border-radius:14px; padding:10px 12px; color:var(--ink); font-size:14px; }
    textarea.rep { width:100%; box-sizing:border-box; min-height:80px; font:inherit; font-size:14px; padding:10px 12px; border:1px solid var(--line); border-radius:14px; color:var(--ink); background:var(--soft); }
  `;

  const CTX_STYLE = `
    .ctx { display:flex; gap:10px; border-radius:16px; padding:10px; margin:8px 0; background:#fff; border:1px solid var(--line); color:var(--ink); font:13px/1.4 var(--font); box-shadow:0 4px 16px rgba(19,35,58,.08); }
    .ctx > img { width:56px; height:56px; object-fit:contain; background:var(--soft); border-radius:12px; flex:none; }
    .ctx .body { min-width:0; flex:1; }
    .ctx .t { font-weight:600; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
    .ctx .m { color:var(--muted); } .ctx s { color:var(--muted); }
    .ctx .chips { display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; justify-content:flex-start; }
    .ctx .chip { border-radius:8px; padding:1px 8px; font-size:12px; background:var(--soft); color:var(--ink); }
    .ctx .more { font:inherit; font-size:12px; padding:0; border:0; background:none; color:var(--link); cursor:pointer; text-decoration:underline; margin-top:6px; }
    .ctx pre { white-space:pre-wrap; word-break:break-word; max-height:180px; overflow:auto; margin:6px 0 0; font:12px/1.4 ui-monospace,monospace; background:var(--soft); border-radius:10px; padding:8px; }
    .ctx-h { font-size:12px; color:var(--muted); margin-top:10px; }
  `;

  const STYLE = `
    ${TOKENS}
    :host { all:initial; display:flex; font:15px/1.5 var(--font); color:var(--ink); letter-spacing:-.01em; }

    /* Side rail: frosted strip of soft square buttons */
    :host(.float) { position:fixed; right:0; top:50%; transform:translateY(-50%); z-index:2147483647; flex-direction:row; align-items:center; gap:12px; }
    :host(.float) .bar { flex-direction:column; gap:8px; padding:10px 8px 10px 10px; background:rgba(253,252,250,.86); backdrop-filter:blur(12px); border:1px solid #fff; border-right:0; border-radius:22px 0 0 22px; box-shadow:-6px 10px 30px rgba(19,35,58,.18); }
    :host(.float) .fab { position:relative; width:46px; height:46px; padding:0; border-radius:15px; display:grid; place-items:center; }
    .tip { position:absolute; right:calc(100% + 12px); top:50%; transform:translateY(-50%); background:var(--ink); color:#fff; padding:6px 12px; border-radius:10px; font-size:13px; font-weight:600; white-space:nowrap; opacity:0; pointer-events:none; transition:opacity .12s ease; }
    .fab:hover .tip, .fab:focus-visible .tip { opacity:1; }
    .fab { font:inherit; font-weight:700; padding:10px 18px; border:1px solid transparent; border-radius:14px; background:var(--soft); color:var(--ink); cursor:pointer; transition:transform .12s ease, background-color .12s ease; }
    .fab:hover { background:#e6ebf1; }
    .fab:active { transform:scale(.96); }
    .fab[aria-expanded="true"] { background:var(--lime); border-color:var(--lime-d); }
    .fab:focus-visible { outline:3px solid var(--link); outline-offset:2px; }
    .fab:disabled { opacity:.6; cursor:default; }
    .fab.unknown { background:var(--unknown-bg); color:var(--unknown); }
    .fab.green { background:var(--green-bg); color:var(--green); } .fab.amber { background:var(--amber-bg); color:var(--amber); } .fab.red { background:var(--red-bg); color:var(--red); }
    .fab.green[aria-expanded="true"], .fab.amber[aria-expanded="true"], .fab.red[aria-expanded="true"], .fab.unknown[aria-expanded="true"] { box-shadow:0 0 0 3px var(--lime-d); }
    :host(.inline) { display:block; position:absolute; bottom:12px; right:12px; z-index:100; }
    :host(.inline) .fab { padding:3px 11px; font-size:12px; white-space:nowrap; border-radius:10px; border-color:#fff; box-shadow:0 2px 10px rgba(19,35,58,.18); }
    :host(.inline) .bar { gap:6px; }
    .bar { display:flex; gap:8px; align-items:center; }

    /* Panels: pastel frame (tinted by the verdict) around a white card */
    .box { box-sizing:border-box; width:min(400px,calc(100vw - 100px)); max-height:72vh; overflow:auto; scrollbar-width:thin; padding:10px; border-radius:28px; background:var(--frame); box-shadow:0 18px 50px rgba(19,35,58,.24);
      --frame:var(--sky); }
    .box.green { --frame:radial-gradient(120% 70% at 0% 0%, #bfe6c9 0%, transparent 60%), radial-gradient(120% 70% at 100% 100%, #e6efc4 0%, transparent 60%), linear-gradient(180deg, #d9eee0, #eef3df); }
    .box.amber { --frame:radial-gradient(120% 70% at 0% 0%, #f7deaa 0%, transparent 60%), radial-gradient(120% 70% at 100% 100%, #f6c9b4 0%, transparent 60%), linear-gradient(180deg, #f6e7cb, #f3ddd2); }
    .box.red { --frame:radial-gradient(120% 70% at 0% 0%, #f4bdb8 0%, transparent 60%), radial-gradient(120% 70% at 100% 100%, #f6d2b4 0%, transparent 60%), linear-gradient(180deg, #f6d9d5, #f3ddd2); }
    .box[hidden] { display:none; }
    :host(.pop) { position:fixed; top:0; left:0; z-index:2147483647; }
    :host(.pop) .box { position:fixed; }
    .card { background:var(--card); border-radius:22px; padding:16px; box-shadow:0 6px 24px rgba(19,35,58,.10); }
    .brand-row { display:flex; align-items:center; justify-content:center; gap:6px; font-size:14px; }
    .brand-row .mark { display:grid; place-items:center; width:22px; height:22px; border-radius:7px; background:var(--lime); color:var(--ink); font-size:13px; }
    .brand-row .brand { font-size:15px; font-weight:700; }
    .badge { font-size:11px; font-weight:600; padding:1px 7px; border-radius:6px; background:var(--soft); color:var(--muted); }
    .headline { margin:6px 0 0; text-align:center; font-size:24px; line-height:1.15; font-weight:700; letter-spacing:-.03em; color:var(--ink); }
    .headline.green { color:var(--green); } .headline.amber { color:var(--amber); } .headline.red { color:var(--red); } .headline.unknown { color:var(--unknown); }
    .loading { display:flex; align-items:center; gap:10px; margin:0; }
    .loading .mark { flex:none; display:grid; place-items:center; width:28px; height:28px; border-radius:9px; background:var(--lime); animation:pulse 1.2s ease-in-out infinite; }
    @keyframes pulse { 50% { transform:scale(.85); opacity:.6; } }
    .demo { background:var(--amber-bg); color:var(--amber); border-radius:12px; padding:6px 10px; font-size:13px; margin-bottom:10px; text-align:center; }

    /* Verdict sections */
    .sec { border-radius:16px; padding:10px 14px; margin-top:10px; background:var(--unknown-bg); }
    .sec.green { background:var(--green-bg); } .sec.amber { background:var(--amber-bg); } .sec.red { background:var(--red-bg); }
    .sec h3 { margin:0 0 2px; display:flex; justify-content:space-between; align-items:center; gap:8px; }
    .verdict { font-size:12px; font-weight:700; padding:2px 10px; border-radius:999px; background:#fff; }
    .sec.green .verdict { color:var(--green); } .sec.amber .verdict { color:var(--amber); } .sec.red .verdict { color:var(--red); } .sec.unknown .verdict { color:var(--unknown); }

    /* Chat */
    .box.chat { display:flex; flex-direction:column; gap:12px; }
    .box.chat[hidden] { display:none; }
    .chat > .tools { justify-content:center; gap:8px; }
    .chat > .tools button { font:inherit; font-size:13px; font-weight:600; padding:7px 14px; border:1px solid rgba(255,255,255,.9); border-radius:14px; background:rgba(255,255,255,.55); color:var(--ink); cursor:pointer; box-shadow:0 2px 8px rgba(19,35,58,.08); backdrop-filter:blur(6px); }
    .chat > .tools button:hover { background:var(--lime); border-color:var(--lime-d); }
    .chat .card { display:flex; flex-direction:column; gap:10px; }
    .chat .headline { margin:0; font-size:22px; }
    .chat .ctx-h { text-align:center; margin:0 0 6px; }
    .sky { border-radius:18px; padding:14px 12px; background:linear-gradient(180deg, #cfe3f7 0%, #e9f0e6 55%, #8fc3b8 85%, #2e4f5c 100%); }
    .sky .ctx { margin:0; border-color:#fff; box-shadow:0 4px 16px rgba(19,35,58,.14); }
    .log { display:flex; flex-direction:column; gap:8px; max-height:38vh; overflow:auto; }
    .msg { padding:10px 12px; border-radius:16px; max-width:92%; }
    .msg.user { align-self:flex-end; background:var(--ink); color:#fff; border-bottom-right-radius:6px; } .msg.bot { align-self:flex-start; background:var(--soft); border-bottom-left-radius:6px; }
    .chips { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
    .chips button { font:inherit; font-size:13px; padding:6px 12px; border:1px solid var(--line); border-radius:12px; background:#fff; color:var(--ink); cursor:pointer; }
    .chips button:hover { background:#f4f9e6; border-color:var(--lime-d); }
    .ask { display:flex; gap:4px; background:var(--soft); border-radius:16px; padding:4px; }
    .ask input { flex:1; min-width:0; font:inherit; font-size:14px; padding:8px 10px; border:0; border-radius:12px; color:var(--ink); background:transparent; }
    .ask select, .ask button { font:inherit; font-size:13px; padding:6px 12px; border:0; border-radius:12px; background:#fff; color:var(--ink); cursor:pointer; }
    .ask button { background:var(--ink); color:#fff; font-weight:600; }
    .ask button:disabled { opacity:.5; cursor:default; }
    .rchat { margin-top:16px; padding-top:12px; border-top:1px solid var(--line); display:flex; flex-direction:column; gap:8px; }
    .rchat .ctx-h { margin:0; text-align:center; }
    .hist { display:flex; flex-direction:column; gap:8px; max-height:48vh; overflow:auto; }
    .hist[hidden], .log[hidden], .chips[hidden], .ask[hidden] { display:none; }
    .hist-item { background:var(--soft); border-radius:14px; padding:10px 12px; }
    .hist-item .when { color:var(--muted); font-size:12px; }
    .hist-item p { margin:4px 0 0; }

    /* Evidence */
    .evidence { margin-top:6px; }
    details.steps { margin-top:6px; font-size:12px; color:var(--muted); } details.steps summary { cursor:pointer; font-weight:600; }
    details.steps ol { margin:4px 0 0; padding-left:18px; } .draft dt { font-weight:700; font-size:13px; margin-top:6px; } .draft dd { margin:0 0 2px; font-size:13px; }
    .ev-h { font-weight:700; font-size:13px; color:var(--ink); }
    .ev-item { background:#fff; border:1px solid var(--line); border-radius:12px; padding:6px 10px; margin:6px 0; }
    .ev-title { font-size:12px; color:var(--muted); }
    blockquote { margin:2px 0 4px; font-size:13px; }

    ${CTX_STYLE}
    ${PANEL_STYLE}
    a { color:var(--link); font-size:13px; }
    .tools { display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-top:8px; }
    h3 { font-size:15px; margin:12px 0 2px; } ul { margin:0; padding-left:20px; } p { margin:8px 0 0; }
    .muted { color:var(--muted); font-size:13px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin-top:14px; }
    button.small { font:inherit; font-size:13px; font-weight:600; padding:7px 14px; border:1px solid var(--line); border-radius:12px; background:#fff; color:var(--ink); cursor:pointer; }
    button.small:hover { background:var(--soft); }
    .row button.small:first-child { background:var(--ink); border-color:var(--ink); color:#fff; }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline:3px solid var(--link); outline-offset:2px; }
    @media (prefers-reduced-motion: reduce) { .fab, .tab { transition:none; } .fab:active { transform:none; } .loading .mark { animation:none; } }
  `;

  const el = (tag, props = {}, ...kids) => {
    const n = Object.assign(document.createElement(tag), props);
    n.append(...kids);
    return n;
  };

  // Small confirmation message in its own layer on <body>, so no shop CSS can hide or clip it.
  let toastHost = null;
  let toastTimer = null;
  const toast = (message, actionLabel, onAction) => {
    toastHost?.remove();
    clearTimeout(toastTimer);
    toastHost = el("div");
    const root = toastHost.attachShadow({ mode: "open" });
    const close = () => { toastHost?.remove(); toastHost = null; };
    const action = actionLabel ? el("button", { type: "button", textContent: actionLabel, onclick: () => { onAction?.(); close(); } }) : "";
    const dismiss = el("button", { type: "button", textContent: "Dismiss", onclick: close });
    dismiss.setAttribute("aria-label", "Dismiss");
    root.append(
      el("style", { textContent: `
        ${TOKENS}
        :host { all:initial; position:fixed; left:50%; bottom:24px; transform:translateX(-50%); z-index:2147483647; }
        .t { display:flex; align-items:center; gap:12px; font:14px/1.4 var(--font); letter-spacing:-.01em; background:var(--ink); color:#fff; padding:10px 10px 10px 14px; border-radius:20px; box-shadow:0 14px 40px rgba(19,35,58,.35); max-width:min(480px,92vw); }
        .t::before { content:"✦"; display:grid; place-items:center; flex:none; width:24px; height:24px; border-radius:8px; background:var(--lime); color:var(--ink); font-size:13px; }
        button { font:inherit; font-size:13px; font-weight:600; padding:6px 12px; border:0; border-radius:12px; background:rgba(255,255,255,.14); color:#fff; cursor:pointer; white-space:nowrap; }
        button:first-of-type { background:var(--lime); color:var(--ink); }
        button:focus-visible { outline:3px solid var(--lime-d); outline-offset:2px; }
      ` }),
      el("div", { className: "t", role: "status" }, el("span", { textContent: message }), action, dismiss),
    );
    document.body.append(toastHost);
    toastTimer = setTimeout(close, 6000);
  };

  // Mini card of what is sent to the API: product photo, title, price, seller, and the exact fields on request.
  const contextCard = (page) => {
    const text = page.page_text || "";
    const asin = text.match(/^ASIN: (\S+)/m)?.[1];
    const mrp = text.match(/^M\.R\.P\.: (.+)$/m)?.[1];
    const n = (page.image_urls || []).length;
    // The exact fields that go to the API (the shop's own ids are removed before sending)
    const sent = { url: page.url, title: page.title, price: page.price, currency: page.currency, seller: page.seller, image_urls: page.image_urls, page_text: text };
    const pre = el("pre", { hidden: true, textContent: JSON.stringify(sent, null, 2) });
    const more = el("button", { type: "button", className: "more", textContent: "More details" });
    more.setAttribute("aria-expanded", "false");
    more.onclick = () => {
      pre.hidden = !pre.hidden;
      more.textContent = pre.hidden ? "More details" : "Hide details";
      more.setAttribute("aria-expanded", String(!pre.hidden));
    };
    const chip = (t) => el("span", { className: "chip", textContent: t });
    const photo = el("img", { src: (page.image_urls || [])[0] || "", alt: "" });
    photo.onerror = () => photo.remove();
    return el("div", { className: "ctx" },
      ...(n ? [photo] : []),
      el("div", { className: "body" },
        el("div", { className: "t", textContent: page.title || page.url }),
        el("div", { className: "m" }, page.price != null ? `${(() => { try { return new Intl.NumberFormat(undefined, { style: "currency", currency: page.currency || "INR", maximumFractionDigits: 0 }).format(page.price); } catch (_) { return page.price; } })()} ` : "", ...(mrp ? [el("s", { textContent: mrp })] : []), page.seller ? ` · ${page.seller}` : ""),
        el("div", { className: "chips" }, ...[page.seller && "seller", asin && `ASIN ${asin}`, `${n} photo link${n === 1 ? "" : "s"}`, `${text.length.toLocaleString()} characters of details`].filter(Boolean).map(chip)),
        more, pre,
      ));
  };

  // --- TEMP COST GUARD: shows an estimate in rupees and asks before a paid request. To remove: delete this block, the three `guard(` calls, and the cost rows in popup.html/popup.js. ---
  const COST = {
    // Gemini 3.6/3.8 Flash: about 2,000 input + 1,500 output tokens at $0.75 / $3.75 per 1M tokens, at an assumed Rs 88 per US$.
    chat: { text: "about ₹0.6 (up to ₹1.3 if a second model is tried). ₹0 on a free-tier key.", mid: 0.63 },
    // Copy search and identification run Gemini inside the engine; real token counts are not known yet.
    duplicates: { text: "about ₹1 to ₹5 (rough guess: Gemini compares the product with similar ones).", mid: 3 },
    identify: { text: "about ₹0.2 to ₹1 (rough guess: an embedding lookup).", mid: 0.5 },
    // The check uses Gemini on Vertex AI (embeddings + listing comparison); real token counts are not known yet.
    check: { text: "about ₹1 to ₹5 (rough guess: the check uses Gemini on Vertex AI to compare listings).", mid: 3 },
  };
  const approved = new Set(); // pages already approved: Check, Save and Ask share one cached check
  const confirmCost = (what, estimate, page) => new Promise((resolve) => {
    const host = el("div");
    const root = host.attachShadow({ mode: "open" });
    const finish = (ok) => { host.remove(); resolve(ok); };
    const go = el("button", { type: "button", textContent: "Continue", onclick: () => finish(true) });
    const no = el("button", { type: "button", textContent: "Cancel", onclick: () => finish(false) });
    const dialog = el("div", { className: "d", role: "alertdialog" }, el("div", { className: "in" },
      el("strong", { textContent: "This uses AI credits" }),
      el("p", { textContent: `${what}. Estimated cost: ${estimate}` }),
      ...(page ? [el("div", { className: "ctx-h", textContent: "What will be sent to SafeShelf:" }), contextCard(page)] : []),
      el("div", { className: "r" }, go, no)));
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-label", "Cost estimate");
    root.append(el("style", { textContent: `
      ${TOKENS}
      :host { all:initial; position:fixed; inset:0; z-index:2147483647; display:flex; align-items:center; justify-content:center; background:rgba(19,35,58,.28); backdrop-filter:blur(3px); }
      .d { font:15px/1.5 var(--font); letter-spacing:-.01em; color:var(--ink); max-width:min(420px,90vw); padding:10px; border-radius:28px; background:var(--sky); box-shadow:0 18px 50px rgba(19,35,58,.35); }
      .in { background:var(--card); border-radius:22px; padding:18px; }
      strong { display:block; text-align:center; font-size:20px; letter-spacing:-.03em; }
      ${CTX_STYLE}
      p { margin:6px 0 12px; text-align:center; color:var(--muted); font-size:14px; } .r { display:flex; gap:8px; justify-content:center; margin-top:12px; }
      button { font:inherit; font-size:14px; font-weight:600; padding:8px 18px; border:1px solid var(--line); border-radius:12px; background:#fff; color:var(--ink); cursor:pointer; }
      button:first-child { background:var(--ink); border-color:var(--ink); color:#fff; } button:focus-visible { outline:3px solid var(--link); outline-offset:2px; }
    ` }), dialog);
    dialog.addEventListener("keydown", (e) => { if (e.key === "Escape") finish(false); });
    document.body.append(host);
    go.focus();
  });
  // Resolves true when the request may go ahead. `key` remembers approval for a page; null asks every time.
  const guard = async (kind, key, what, page) => {
    try {
      if ((await chrome.storage.local.get("costGuard")).costGuard === false) return true;
      if (kind === "check" && (await chrome.runtime.sendMessage({ type: "safeshelf:cost-info" }))?.result?.mockApi) return true; // the local mock is free
      if (key && approved.has(key)) return true;
      if (!(await confirmCost(what, COST[kind].text, page))) return false;
      if (key) approved.add(key);
      const { spend = { total: 0, calls: 0 } } = await chrome.storage.local.get("spend");
      await chrome.storage.local.set({ spend: { total: spend.total + COST[kind].mid, calls: spend.calls + 1 } });
    } catch (_) { /* storage or messaging unavailable: do not block the shopper */ }
    return true;
  };
  // --- END TEMP COST GUARD ---

  // ---- Panels: one tab per SafeShelf API. Nothing is shown unless the API says the endpoint is live. ----
  // A list of rows from a view-model (see panels.js)
  const vmDom = (v) => el("div", {},
    el("div", { className: "vh", textContent: v.title }),
    ...(v.note ? [el("div", { className: "vnote", textContent: v.note })] : []),
    ...(v.empty ? [el("div", { className: "vnote", textContent: v.empty })] : []),
    ...v.rows.map((r) => r.heading ? el("div", { className: "vh", textContent: r.heading }) : el("div", { className: "vrow" }, el("span", { className: "i", textContent: r.icon }),
      el("div", {}, el("div", { textContent: r.text }), ...(r.sub ? [el("div", { className: "s", textContent: r.sub })] : []),
        ...(/^https?:/.test(r.link || "") ? [el("a", { href: r.link, target: "_blank", rel: "noopener", textContent: "Open source" })] : [])))),
  );
  const NOT_LIVE = "Not live on the SafeShelf API yet. Nothing is shown rather than example data. It will appear here once the API serves it.";
  // Calls one API operation through the background worker and puts the result (or why there is none) into `into`.
  const loadPanel = (into, op, args, key) => {
    into.replaceChildren(el("div", { className: "vnote", textContent: "Loading…" }));
    try {
      chrome.runtime.sendMessage({ type: "safeshelf:call", op, args }, (res) => {
        if (!res?.ok) return into.replaceChildren(el("div", { className: "notlive", textContent: `Could not load this: ${res?.error || chrome.runtime.lastError?.message}` }));
        if (!res.result.live) return into.replaceChildren(el("div", { className: "notlive", textContent: NOT_LIVE }));
        into.replaceChildren(vmDom(globalThis.SafeShelfPanels[key](res.result.data)));
      });
    } catch (_) { into.replaceChildren(el("div", { className: "notlive", textContent: "The extension was reloaded. Please refresh the page." })); }
  };
  // A button that runs a costly (AI) operation only after the cost dialog is accepted
  const costlyButton = (label, kind, what, run) => {
    const b = el("button", { type: "button", className: "small", textContent: label });
    b.onclick = async () => { if (await guard(kind, null, what)) run(); }; // TEMP cost guard
    return b;
  };

  // Past chats, kept in this browser only (newest first, at most 30).
  const history = {
    async get() { try { return (await chrome.storage.local.get("chatHistory")).chatHistory || []; } catch (_) { return []; } },
    async set(list) { try { await chrome.storage.local.set({ chatHistory: list }); } catch (_) { /* storage unavailable: skip */ } },
  };

  // Finds where a quote appears on the page (reviews, descriptions) so the shopper can jump to the source.
  const norm = (t) => t.replace(/\s+/g, " ").trim().toLowerCase();
  const findOnPage = (quote) => {
    const probe = norm(quote).slice(0, 60);
    if (!probe) return null;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const p = n.parentElement;
      if (!p || /^(SCRIPT|STYLE|NOSCRIPT)$/.test(p.tagName) || !p.getClientRects().length) continue;
      if (norm(n.nodeValue).includes(probe)) return p.closest("[data-review-id], [data-hook='review'], .review, article, li") || p;
    }
    return null;
  };
  const flash = (target) => {
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    const before = target.getAttribute("style");
    target.style.outline = "4px solid #f9ab00";
    target.style.background = "#fff3cd";
    setTimeout(() => (before === null ? target.removeAttribute("style") : target.setAttribute("style", before)), 4000);
  };

  const evidenceItem = (id, e) => {
    if (!e) return el("div", { className: "muted", textContent: `${id} (details not available)` });
    const show = el("button", { type: "button", className: "small", textContent: "Show on page" });
    show.onclick = () => {
      const target = findOnPage(e.quote);
      if (target) flash(target);
      else toast(`${id} is not on this page. It comes from: ${e.source}${e.date ? `, ${e.date}` : ""}.`);
    };
    return el("div", { className: "ev-item" },
      el("div", { className: "ev-title", textContent: `${id} · ${e.source}${e.date ? ` · ${e.date}` : ""}${e.rating ? ` · ${"★".repeat(e.rating)}` : ""}` }),
      el("blockquote", { textContent: `“${e.quote}”` }),
      el("div", { className: "tools" }, show, ...(/^https?:/.test(e.url || "") ? [el("a", { href: e.url, target: "_blank", rel: "noopener", textContent: "Open source" })] : [])),
    );
  };
  // Evidence under an answer: what each ID points to, and a button that scrolls to it on the page.
  const evidenceBlock = (ids) => {
    if (!ids.length) return el("div", { className: "muted", textContent: "No evidence cited." });
    const block = el("div", { className: "evidence" }, el("div", { className: "ev-h", textContent: "Evidence" }));
    try {
      chrome.runtime.sendMessage({ type: "safeshelf:evidence", ids }, (res) => {
        const byId = new Map((res?.ok ? res.result.items : []).map((e) => [e.evidence_id, e]));
        block.append(...ids.map((id) => evidenceItem(id, byId.get(id))));
      });
    } catch (_) { block.append(...ids.map((id) => evidenceItem(id, null))); }
    return block;
  };

  // What the agents did for an answer (tools read, hand-offs), from the API's own step list.
  const STEP_WORDS = { gemini: "", safety: "read the safety record", product: "read the product", relationships: "read the copies and twins",
    certifications: "read the safety marks", history: "read the history", alternatives: "read the safer options", evidence: "read the exact quotes" };
  const stepsBlock = (steps) => {
    const shown = (steps || []).filter((s) => s.tool !== "gemini" || /call|Wrote/.test(s.summary || ""));
    if (!shown.length) return "";
    const agent = (a) => ({ shelf_chat: "Shelf Chat", safer_alternative_finder: "Safer Alternative Finder", investigation_copilot: "Report copilot" }[a] || a);
    return el("details", { className: "steps" }, el("summary", { textContent: `How SafeShelf answered (${shown.length} steps)` }),
      el("ol", {}, ...shown.map((s) => el("li", { textContent: `${agent(s.agent)}: ${STEP_WORDS[s.tool] ? STEP_WORDS[s.tool] + " - " : ""}${s.summary}${s.seconds ? ` (${s.seconds} s)` : ""}` }))));
  };
  // Live agent session through the background worker: onEvent gets each step as it happens.
  const agentLive = (body, onEvent, timeout) => new Promise((resolve, reject) => {
    let port;
    try { port = chrome.runtime.connect({ name: "safeshelf-agent" }); } catch (_) { return reject(new Error("The extension was reloaded. Please refresh the page.")); }
    let finished = false;
    port.onMessage.addListener((m) => {
      if (m.type === "event") return onEvent?.(m.event);
      finished = true;
      port.disconnect();
      if (m.type === "done") resolve(m.result); else reject(new Error(m.error || "no answer"));
    });
    port.onDisconnect.addListener(() => { if (!finished) reject(new Error(chrome.runtime.lastError?.message || "The connection to SafeShelf closed")); });
    port.postMessage({ body, timeout });
  });
  const LIVE_WORDS = { safety: "Reading the safety record", product: "Reading the product", relationships: "Looking at copies and twins", certifications: "Checking safety marks",
    history: "Reading the history", alternatives: "Comparing safer options", evidence: "Reading the exact quotes", read_link: "Reading the page" };
  // A chat question, answered live: the pending bubble shows what the agent is doing, then done({ok, result}) as before.
  const askLive = (payload, pending, done) => {
    const { type, ...fields } = payload;
    const say = (t) => pending.replaceChildren(el("span", { className: "muted", textContent: t }));
    agentLive({ mode: "chat", ...fields }, (e) => {
      if (e.type === "step" && e.tool !== "gemini") say(`${LIVE_WORDS[e.tool] || e.summary}…`);
      if (e.type === "step" && e.tool === "gemini" && /call/.test(e.summary)) say(`${e.summary.replace("Decided to call", "Looking up:")}…`);
      if (e.type === "verdict") say(`${e.verdict.overall === "red" ? "⛔" : e.verdict.overall === "amber" ? "⚠️" : e.verdict.overall === "green" ? "✅" : "❔"} Verdict ready, writing the answer…`);
    }, /https?:\/\//.test(fields.message || "") ? 200000 : 150000)
      .then((a) => {
        const m = [...(a.messages || [])].reverse().find((x) => x.role === "assistant") || {};
        done({ ok: true, result: { text: m.text || "I don't know. There is not enough evidence to answer that.", evidence_ids: m.evidence_ids || [], steps: a.steps || [] } });
      })
      .catch((err) => done({ ok: false, error: err.message }));
  };
  const agentCall = (body, timeout) => new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendMessage({ type: "safeshelf:agent", body, timeout }, (res) => (res?.ok ? resolve(res.result) : reject(new Error(res?.error || chrome.runtime.lastError?.message || "no answer"))));
    } catch (_) { reject(new Error("The extension was reloaded. Please refresh the page.")); }
  });

  const level = (r) => {
    const both = [r.safe.level, r.real.level];
    return both.includes("red") ? "red" : both.includes("amber") ? "amber" : both.includes("unknown") ? "unknown" : "green";
  };

  const speak = (r) => {
    const say = (name, c) => `${name}. ${c.word}. ${c.lines.join(". ")}.`;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(`${say("Is it safe?", r.safe)} ${say("Is it real?", r.real)} ${r.summary}`));
  };

  const section = (title, c) =>
    el("div", { className: `sec ${c.level}` }, el("h3", {}, `${title} `, el("span", { className: "verdict", textContent: c.word })), el("ul", {}, ...c.lines.map((l) => el("li", { textContent: l }))));

  // Side-rail icons: plain stroked paths, one family, drawn in the button's text colour.
  const ICON_PATHS = {
    check: "M12 3l7 3v5c0 5-3.2 8.2-7 10-3.8-1.8-7-5-7-10V6z M9 12l2 2 4-4",
    save: "M7 3h10a1 1 0 011 1v17l-6-4-6 4V4a1 1 0 011-1z",
    ask: "M4 5h16v11H9l-5 4z",
  };
  const icon = (kind) => {
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    for (const [k, v] of Object.entries({ viewBox: "0 0 24 24", width: "24", height: "24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" })) svg.setAttribute(k, v);
    const p = document.createElementNS(ns, "path");
    p.setAttribute("d", ICON_PATHS[kind] || ICON_PATHS.check);
    svg.append(p);
    return svg;
  };

  // Centred "✦ SafeShelf [badge]" line at the top of every card.
  const brandRow = (badge) => el("div", { className: "brand-row" },
    el("span", { className: "mark", ariaHidden: "true", textContent: "✦" }), el("span", { className: "brand", textContent: "SafeShelf" }), el("span", { className: "badge", textContent: badge }));

  // One button + result card. Used once as a floating button (product page) and once per product card (results pages).
  // Nothing is sent to the API until the button is clicked.
  const createWidget = (getPage, mode) => {
    const host = el("div", { className: mode });
    const root = host.attachShadow({ mode: "open" });
    // Full wording on product pages, short wording on cards (less clutter); screen readers always get the full wording.
    const label = (btn, full, short) => {
      btn.setAttribute("aria-label", full);
      if (mode === "inline") { btn.textContent = short; return; }
      btn.replaceChildren(icon(btn.dataset.kind), el("span", { className: "tip", textContent: full }));
    };
    const fab = el("button", { type: "button", className: "fab" });
    fab.dataset.kind = "check";
    label(fab, "Check with SafeShelf", "Check");
    fab.setAttribute("aria-expanded", "false");
    const shelfBtn = el("button", { type: "button", className: "fab shelf" });
    shelfBtn.dataset.kind = "save";
    label(shelfBtn, "Save to My Shelf", "Save");
    // Shelf Chat: only on a single product page, never on result cards
    const chatBtn = mode === "float" ? el("button", { type: "button", className: "fab chat" }) : null;
    if (chatBtn) { chatBtn.dataset.kind = "ask"; label(chatBtn, "Ask SafeShelf", "Ask"); chatBtn.setAttribute("aria-expanded", "false"); }
    const chatBox = chatBtn ? el("section", { className: "box chat", hidden: true, ariaLabel: "Ask SafeShelf about this product" }) : null;
    shelfBtn.setAttribute("aria-live", "polite");
    const bar = el("div", { className: "bar" }, ...(chatBtn ? [chatBtn] : []), shelfBtn, fab); // separate buttons: chat, save, check
    const box = el("section", { className: "box", hidden: true, ariaLabel: "SafeShelf safety check" });
    box.setAttribute("aria-live", "polite");
    const show = (...nodes) => box.replaceChildren(el("div", { className: "card" }, ...nodes)); // everything in the box sits on one white card
    // On results pages the popup lives in its own layer on <body>, so no card's CSS can clip, move or cover it.
    const pop = mode === "inline" ? el("div", { className: "pop" }) : null;
    if (pop) {
      pop.attachShadow({ mode: "open" }).append(el("style", { textContent: STYLE }), box);
      root.append(el("style", { textContent: STYLE }), bar);
    } else {
      root.append(el("style", { textContent: STYLE }), box, ...(chatBox ? [chatBox] : []), bar);
    }
    let checked = false;
    let result = null;
    let saved = false;
    let setChatOpen = () => {};
    let resetChat = () => {};

    // Results-page popups are fixed overlays placed beside the button, so they never move page content.
    const place = () => {
      if (mode !== "inline" || box.hidden) return;
      const r = fab.getBoundingClientRect();
      const w = Math.min(400, innerWidth - 32);
      const below = innerHeight - r.bottom;
      box.style.width = `${w}px`;
      box.style.left = `${Math.max(16, Math.min(r.right - w, innerWidth - w - 16))}px`;
      if (below >= 260 || below >= r.top) {
        box.style.top = `${r.bottom + 6}px`; box.style.bottom = "auto"; box.style.maxHeight = `${Math.max(160, below - 20)}px`;
      } else {
        box.style.bottom = `${innerHeight - r.top + 6}px`; box.style.top = "auto"; box.style.maxHeight = `${Math.max(160, r.top - 20)}px`;
      }
    };
    const outside = (e) => { const p = e.composedPath(); if (!p.includes(host) && !p.includes(pop)) setOpen(false); };
    const setOpen = (open) => {
      box.hidden = !open;
      fab.setAttribute("aria-expanded", String(open));
      if (pop) {
        if (open) document.body.append(pop); else pop.remove();
        const act = open ? "addEventListener" : "removeEventListener";
        window[act]("scroll", place, true);
        window[act]("resize", place);
        document[act]("click", outside, true);
      }
      if (open) place(); else speechSynthesis.cancel();
    };

    // What a chat question is sent with: the check result and what the listing itself says.
    // The listing text goes last, so the API's length cap cuts it first. Works for unmatched products too.
    const chatContext = (r) => {
      const p = getPage();
      return { title: p.title, price: p.price, seller: p.seller, host: r.host, summary: r.summary,
        safe: { level: r.safe.level, lines: r.safe.lines }, real: { level: r.real.level, lines: r.real.lines }, evidence_ids: r.evidence_ids || [],
        matched_by: r.matched_by, checks: r.trust_checks, genuine_model_safety: r.genuine_model_safety,
        listing_text: (p.page_text || "").slice(0, 1500) };
    };

    // Chat about the check result just shown: it knows this result and remembers the conversation.
    const resultChat = (r) => {
      const thread = []; // {role: "user" | "bot", text}
      const sid = `SS-A-${Math.random().toString(36).slice(2, 10)}`;
      const log = el("div", { className: "log", role: "log" });
      log.setAttribute("aria-live", "polite");
      const input = el("input", { type: "text", placeholder: "Ask about this result…" });
      input.setAttribute("aria-label", "Your question about this result");
      const lang = el("select", {}, el("option", { value: "en", textContent: "English" }), el("option", { value: "hi", textContent: "हिन्दी" }));
      lang.setAttribute("aria-label", "Answer language");
      const send = el("button", { type: "submit", textContent: "Send" });
      const form = el("form", { className: "ask" }, input, lang, send);
      const chips = el("div", { className: "chips" });
      const add = (kind, text) => {
        const m = el("div", { className: `msg ${kind}` }, el("span", { textContent: text }));
        log.append(m);
        log.scrollTop = log.scrollHeight;
        return m;
      };
      const context = () => chatContext(r);
      const ask = async (q) => {
        if (!q.trim()) return;
        add("user", q);
        thread.push({ role: "user", text: q });
        input.value = "";
        send.disabled = true;
        const pending = add("bot", "Thinking…");
        const finish = (text, extra = []) => { pending.replaceChildren(el("span", { textContent: text }), ...extra); send.disabled = false; log.scrollTop = log.scrollHeight; };
        if (!(await guard("chat", null, "Ask about this result (your question, this result and the last few messages are sent)"))) { // TEMP cost guard
          thread.pop();
          return finish("Cancelled. Nothing was sent and nothing was charged.");
        }
        try {
          askLive({ type: "safeshelf:chat", product_id: r.product_id || "unmatched", message: q, language: lang.value, session_id: sid, context: context(), history: thread.slice(-7, -1) }, pending, (res) => {
            if (!res?.ok) { thread.pop(); return finish(`Could not get an answer: ${res?.error || chrome.runtime.lastError?.message}`); }
            const a = res.result;
            thread.push({ role: "bot", text: a.text });
            const speakA = el("button", { type: "button", className: "small", textContent: "Listen" });
            speakA.setAttribute("aria-label", "Read this answer aloud");
            speakA.onclick = () => { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(a.text); u.lang = lang.value === "hi" ? "hi-IN" : "en-IN"; speechSynthesis.speak(u); };
            finish(a.text, [evidenceBlock(a.evidence_ids), stepsBlock(a.steps), ...(a.source === "mock" ? [el("div", { className: "muted", textContent: "Demo answer: not a real finding." })] : []), speakA]);
          });
        } catch (_) { thread.pop(); finish("The extension was reloaded. Please refresh the page."); }
      };
      for (const q of ["Why this result?", "Is it safe to buy?", "Show me a safer one", "What should I check before buying?"]) {
        chips.append(el("button", { type: "button", textContent: q, onclick: () => ask(q) }));
      }
      form.onsubmit = (e) => { e.preventDefault(); ask(input.value); };
      return el("div", { className: "rchat" }, el("div", { className: "ctx-h", textContent: "Ask about this result" }), log, chips, form);
    };

    // Tabs under the result: one per SafeShelf API. Each loads when first opened, and only if the API serves it for real.
    const panelTabs = (r, overviewNodes) => {
      const similar = !r.product_id && r.similar_product_id; // a look-alike match: similar, not the same product
      const pid = r.product_id || r.similar_product_id; // what the tabs look up
      const noMatch = () => el("div", { className: "notlive", textContent: "SafeShelf found no product in its catalog that matches this listing, so there is nothing to look up for it." });
      const similarBanner = () => el("div", { className: "notlive", textContent: `Showing data for a similar product (${r.similar_product_id}), not this exact listing. It doesn't prove anything about this listing.` });
      const listing = () => { const { product_id, listing_id, ...rest } = getPage(); return rest; };
      const lookup = (op, key) => { const d = el("div"); if (pid) loadPanel(d, op, { product_id: pid }, key); else d.append(noMatch()); return d; };
      const build = {
        overview: () => el("div", {}, ...overviewNodes),
        marks: () => lookup("certifications", "certifications"),
        copies: () => {
          if (!pid) return noMatch();
          const found = el("div");
          return el("div", {}, lookup("relationships", "relationships"), el("div", { className: "tools" },
            costlyButton("Find copies with AI", "duplicates", "Search for copies of this product", () => loadPanel(found, "duplicates", { product_id: pid }, "duplicates"))), found);
        },
        history: () => lookup("history", "history"),
        safer: () => {
          if (!pid) return noMatch();
          const said = el("div");
          return el("div", {}, lookup("alternatives", "alternatives"), el("div", { className: "tools" },
            costlyButton("Ask the Safer Alternative agent", "chat", "Ask the Safer Alternative agent to recommend one", async () => {
              said.replaceChildren(el("div", { className: "vnote", textContent: "The Safer Alternative agent is comparing options…" }));
              try {
                const a = await agentCall({ mode: "alternatives", product_id: pid });
                const m = a.messages?.[0] || {};
                said.replaceChildren(el("p", { textContent: m.text || "No recommendation." }), evidenceBlock(m.evidence_ids || []), stepsBlock(a.steps));
              } catch (err) { said.replaceChildren(el("div", { className: "notlive", textContent: `Could not ask the agent: ${err.message}` })); }
            })), said);
        },
        details: () => {
          if (!pid) return noMatch();
          const how = el("div");
          return el("div", {}, lookup("product", "product"), el("div", { className: "tools" },
            costlyButton("How was it identified?", "identify", "Identify this listing again", () => loadPanel(how, "identify", { listing: listing() }, "identify"))), how);
        },
        report: () => {
          if (!r.product_id) return el("div", { className: "notlive", textContent: "A report needs an exact product match, so one can't be filed for this listing yet." });
          const d = el("div", {}, el("div", { className: "vnote", textContent: "Checking whether reporting is available…" }));
          try {
            chrome.runtime.sendMessage({ type: "safeshelf:status" }, (res) => {
              if (!res?.ok || !res.result.find((o) => o.op === "report")?.live) return d.replaceChildren(el("div", { className: "notlive", textContent: NOT_LIVE }));
              const ta = el("textarea", { className: "rep", placeholder: "What went wrong? Please don't include your name, phone or address." });
              ta.setAttribute("aria-label", "Describe the problem");
              const out = el("div");
              const send = el("button", { type: "button", className: "small", textContent: "Send report" });
              send.onclick = () => {
                if (ta.value.trim().length < 10) return out.replaceChildren(el("div", { className: "vnote", textContent: "Please write at least 10 characters." }));
                send.disabled = true;
                loadPanel(out, "report", { product_id: pid, description: ta.value.trim() }, "report");
              };
              d.replaceChildren(el("div", { className: "vnote", textContent: "Your report goes to SafeShelf. Personal details are masked, but please don't include any." }), ta, send, out, regulatorDraft(pid));
            });
          } catch (_) { d.replaceChildren(el("div", { className: "notlive", textContent: "The extension was reloaded. Please refresh the page." })); }
          return d;
        },
      };
      const names = [["overview", "Overview"], ["marks", "Marks"], ["copies", "Copies"], ["history", "History"], ["safer", "Safer options"], ["details", "Details"], ["report", "Report"]];
      const bar = el("div", { className: "tabs", role: "tablist" });
      const area = el("div", { role: "tabpanel" });
      const made = {};
      const buttons = names.map(([key, text]) => {
        const b = el("button", { type: "button", className: "tab", textContent: text, role: "tab" });
        b.onclick = () => {
          buttons.forEach((x) => x.setAttribute("aria-selected", String(x === b)));
          made[key] ||= el("div", {}, ...(similar && ["marks", "copies", "history", "safer", "details"].includes(key) ? [similarBanner()] : []), build[key]());
          area.replaceChildren(made[key]);
          place();
        };
        b.onkeydown = (e) => {
          const i = buttons.indexOf(b), n = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
          if (n !== null) { e.preventDefault(); buttons[(n + buttons.length) % buttons.length].focus(); }
        };
        return b;
      });
      bar.append(...buttons);
      buttons[0].click();
      return el("div", {}, bar, area);
    };

    // The report copilot pre-fills a regulator's incident report from stored evidence. Nothing is sent: the shopper
    // reviews it, copies it and files it on the regulator's own site.
    const regulatorDraft = (pid) => {
      const out = el("div");
      const btn = costlyButton("Draft a report for the regulator", "chat", "Draft a regulator report from SafeShelf's evidence", async () => {
        btn.disabled = true;
        out.replaceChildren(el("div", { className: "vnote", textContent: "The report copilot is building the evidence pack…" }));
        try {
          const a = await agentCall({ mode: "report_draft", product_id: pid });
          const rep = a.report || {};
          const f = rep.fields || {};
          const rows = [["Product", f.product_description], ["Brand / model", `${f.brand || ""} ${f.model || ""}`], ["Hazard", f.hazard_type], ["What buyers reported", f.incident_description],
            ["Number of reports", f.number_of_reports], ["First reported", f.first_reported], ["Injuries", f.injuries_reported], ["Where sold", f.where_sold], ["Open questions", (f.open_questions || []).join(" ")]];
          const text = `${rep.regulator?.name}\n${rows.map(([k, v]) => `${k}: ${v ?? ""}`).join("\n")}\nEvidence: ${(f.evidence_cited || []).join(", ")}`;
          const copy = el("button", { type: "button", className: "small", textContent: "Copy draft" });
          copy.onclick = () => navigator.clipboard?.writeText(text).then(() => { copy.textContent = "Copied"; });
          const open = el("a", { href: rep.regulator?.url || "#", target: "_blank", rel: "noopener", textContent: `Open ${rep.regulator?.name || "the regulator's site"}` });
          out.replaceChildren(el("div", { className: "notlive", textContent: "Draft only. SafeShelf has not sent anything: check every field, then file it yourself." }),
            el("dl", { className: "draft" }, ...rows.filter(([, v]) => v !== undefined && v !== "").flatMap(([k, v]) => [el("dt", { textContent: k }), el("dd", { textContent: String(v) })])),
            evidenceBlock(f.evidence_cited || []), el("div", { className: "row" }, copy, open));
        } catch (err) { out.replaceChildren(el("div", { className: "notlive", textContent: `Could not draft it: ${err.message}` })); }
        btn.disabled = false;
      });
      return el("div", {}, el("h3", { className: "vh", textContent: "Tell the regulator" }), el("div", { className: "tools" }, btn), out);
    };

    const render = (r) => {
      result = r;
      const lvl = level(r);
      fab.className = `fab ${lvl}`;
      const word = lvl === "red" ? "Danger" : lvl === "amber" ? "Be careful" : lvl === "unknown" ? "Not enough evidence" : "OK so far";
      label(fab, `SafeShelf: ${word}`, word);
      box.className = `box ${lvl}`;
      const speakBtn = el("button", { type: "button", className: "small", textContent: "Read it to me" });
      speakBtn.onclick = () => speak(r);
      const againBtn = el("button", { type: "button", className: "small", textContent: "Check again" });
      againBtn.onclick = () => run(true);
      const closeBtn = el("button", { type: "button", className: "small", textContent: "Close" });
      closeBtn.onclick = () => { setOpen(false); fab.focus(); };
      // Investigate (the Shopper Agent, investigate.js): only on a product page, never for a card on a results page.
      const investigateBtn = mode === "float" && window.__safeshelfInvestigate
        ? el("button", { type: "button", className: "small", textContent: "Investigate", title: "Let SafeShelf look through the photos, label, reviews and seller (read-only)" })
        : null;
      if (investigateBtn) investigateBtn.onclick = async () => { setOpen(false); window.__safeshelfInvestigate(await withMoreReviews(getPage())); };
      show(
        ...(r.source === "mock" ? [el("div", { className: "demo", textContent: "Demo data: these are example results, not real findings about this product." })] : []),
        brandRow(r.host),
        el("h2", { className: `headline ${lvl}`, textContent: word }),
        panelTabs(r, [
          el("p", { textContent: r.summary }),
          el("div", { className: "ctx-h", textContent: "What was sent for this check:" }),
          contextCard(getPage()),
          section("Is it safe?", r.safe),
          section("Is it real?", r.real),
          el("p", { className: "muted", textContent: `${r.label} · v${chrome.runtime.getManifest().version}` }),
          resultChat(r),
        ]),
        el("div", { className: "row" }, ...[investigateBtn, speakBtn, againBtn, closeBtn].filter(Boolean)),
      );
      place();
    };

    const run = async (fresh = false) => {
      if (!(await guard("check", getPage().url, "Check this product", getPage()))) { // TEMP cost guard
        checked = false;
        box.className = "box";
        show(el("p", { className: "muted", textContent: "Check cancelled. Nothing was sent and nothing was charged." }));
        return;
      }
      checked = true;
      box.className = "box";
      show(el("p", { className: "loading" }, el("span", { className: "mark", ariaHidden: "true", textContent: "✦" }), "SafeShelf is checking this product… the first check can take up to a minute."));
      try {
        const page = mode === "float" ? await withMoreReviews(getPage()) : getPage();
        chrome.runtime.sendMessage({ type: "safeshelf:check", page, fresh }, (res) => {
          if (res?.ok) render(res.result);
          else show(el("p", { textContent: `SafeShelf could not check this page: ${res?.error || chrome.runtime.lastError?.message}. Is the API running?` }));
        });
      } catch (_) { /* extension was reloaded; the new script takes over */ }
    };

    // Saving needs the product matched first. That lookup is silent: it never touches the Check button or the result card.
    const identify = async (done) => {
      if (!(await guard("check", getPage().url, "Identify this product (needed to save it or to chat)", getPage()))) return done(null, "Cancelled. Nothing was sent and nothing was charged."); // TEMP cost guard
      try {
        const page = mode === "float" ? await withMoreReviews(getPage()) : getPage();
        chrome.runtime.sendMessage({ type: "safeshelf:check", page }, (res) => {
          const why = res?.ok ? (res.result.product_id ? null : "SafeShelf does not know this product yet") : (res?.error || chrome.runtime.lastError?.message || "no answer");
          if (why) shelfBtn.title = why;
          done(res?.ok ? res.result : null, why);
        });
      } catch (_) { done(null, "The extension was reloaded. Refresh the page."); }
    };

    // Saves this page to My Shelf. Works with or without a check result, and with or without a matched product.
    const save = (r) => {
      try {
        const page = getPage();
        const pid = r?.product_id || page.product_id || null;
        const meta = { title: page.title, url: page.url, host: r?.host || location.hostname, level: r ? level(r) : null };
        chrome.runtime.sendMessage({ type: "safeshelf:save", product_id: pid, meta }, (res) => {
          if (res?.ok) {
            const item = res.result;
            saved = true;
            const note = item.synced ? "Saved to your SafeShelf account. We'll re-check recalls daily."
              : item.api_error ? `The API did not accept it (${item.api_error}), so it is saved on this browser only.`
              : "Saved on this browser.";
            toast(note, "View shelf", () => chrome.runtime.sendMessage({ type: "safeshelf:open-shelf" }));
            shelfBtn.disabled = false;
            label(shelfBtn, "Saved. View shelf", "Saved");
            shelfBtn.title = `${note} Click to view My Shelf.`;
          } else {
            label(shelfBtn, "Could not save. Retry", "Retry");
            shelfBtn.title = res?.error || chrome.runtime.lastError?.message || "";
            toast(`Could not save to My Shelf: ${shelfBtn.title || "unknown error"}`);
            shelfBtn.disabled = false;
          }
        });
      } catch (_) { shelfBtn.disabled = false; }
    };
    shelfBtn.onclick = () => {
      if (saved) { chrome.runtime.sendMessage({ type: "safeshelf:open-shelf" }); return; }
      shelfBtn.disabled = true;
      label(shelfBtn, "Saving…", "…");
      save(result); // no check needed: saving is free
    };

    const toggle = () => {
      if (!box.hidden) return setOpen(false);
      setChatOpen(false);
      setOpen(true);
      if (!checked) run();
    };
    const reset = () => {
      checked = false;
      result = null;
      saved = false;
      resetChat();
      shelfBtn.disabled = false;
      label(shelfBtn, "Save to My Shelf", "Save");
      shelfBtn.title = "";
      fab.className = "fab";
      label(fab, "Check with SafeShelf", "Check");
      setOpen(false);
    };
    if (chatBtn) {
      const log = el("div", { className: "log", role: "log" });
      log.setAttribute("aria-live", "polite");
      const input = el("input", { type: "text", placeholder: "Ask about this product…" });
      input.setAttribute("aria-label", "Your question");
      const lang = el("select", {}, el("option", { value: "en", textContent: "English" }), el("option", { value: "hi", textContent: "हिन्दी" }));
      lang.setAttribute("aria-label", "Answer language");
      const sendBtn = el("button", { type: "submit", textContent: "Send" });
      const form = el("form", { className: "ask" }, input, lang, sendBtn);
      const closeChat = el("button", { type: "button", className: "small", textContent: "Close" });
      closeChat.onclick = () => { setChatOpen(false); chatBtn.focus(); };
      const chips = el("div", { className: "chips" });
      const ctxHolder = el("div", { className: "sky" }); // page context the product was identified from, refreshed each time the chat opens
      const convo = []; // this conversation so far: {role: "user" | "bot", text, evidence}
      const historyBtn = el("button", { type: "button", className: "small", textContent: "History" });
      const clearBtn = el("button", { type: "button", className: "small", textContent: "Clear" });
      const histView = el("div", { className: "hist", hidden: true });
      const clearNote = el("p", { className: "muted", role: "status" });

      // Moves the current conversation into history, then empties the chat.
      const archive = async () => {
        if (convo.length) {
          const page = getPage();
          const list = await history.get();
          await history.set([{ id: Date.now(), title: page.title || page.url, url: page.url, at: new Date().toISOString(), messages: convo.slice() }, ...list].slice(0, 30));
          convo.length = 0;
        }
        log.replaceChildren();
      };
      const showHistory = async (show) => {
        histView.hidden = !show;
        log.hidden = chips.hidden = form.hidden = show;
        historyBtn.textContent = show ? "Back to chat" : "History";
        if (!show) return;
        const list = await history.get();
        const wipe = el("button", { type: "button", className: "small", textContent: "Delete all history" });
        wipe.onclick = async () => { await history.set([]); showHistory(true); };
        histView.replaceChildren(
          ...(list.length ? [] : [el("p", { className: "muted", textContent: "No past chats yet. When you press Clear, the chat is saved here." })]),
          ...list.map((h) => {
            const del = el("button", { type: "button", className: "small", textContent: "Delete" });
            del.setAttribute("aria-label", `Delete chat about ${h.title}`);
            del.onclick = async () => { await history.set((await history.get()).filter((x) => x.id !== h.id)); showHistory(true); };
            return el("div", { className: "hist-item" },
              el("strong", { textContent: h.title }),
              el("div", { className: "when", textContent: new Date(h.at).toLocaleString() }),
              ...h.messages.map((m) => el("p", { textContent: `${m.role === "user" ? "You" : "SafeShelf"}: ${m.text}${m.evidence?.length ? ` (${m.evidence.join(", ")})` : ""}` })),
              del,
            );
          }),
          ...(list.length ? [wipe] : []),
        );
      };
      historyBtn.onclick = () => showHistory(histView.hidden);
      clearBtn.onclick = async () => {
        const had = convo.length > 0;
        await archive();
        showHistory(false);
        clearNote.textContent = had ? "Chat cleared and saved to History." : "";
        input.focus();
      };

      const add = (kind, text, extra = []) => {
        const m = el("div", { className: `msg ${kind}` }, el("span", { textContent: text }), ...extra);
        log.append(m);
        log.scrollTop = log.scrollHeight;
        return m;
      };
      // The check result for this page (cached for 10 minutes, so this is free after Check). Needed even when
      // SafeShelf does not know the product: the chat then answers from the page and the check, with no safety claim.
      const getCheck = () => new Promise((done) => {
        if (result) done({ r: result }); else identify((r, why) => done({ r, why }));
      });
      const sid = `SS-A-${Math.random().toString(36).slice(2, 10)}`;
      const ask = async (question) => {
        if (!question.trim()) return;
        showHistory(false);
        clearNote.textContent = "";
        add("user", question);
        convo.push({ role: "user", text: question });
        input.value = "";
        sendBtn.disabled = true;
        const pending = add("bot", "Thinking…");
        if (!(await guard("chat", null, "Ask SafeShelf a question (your question, the check result and this page's product details are sent)"))) { // TEMP cost guard
          pending.replaceChildren(el("span", { textContent: "Cancelled. Nothing was sent and nothing was charged." }));
          convo.pop();
          sendBtn.disabled = false;
          return;
        }
        const { r, why } = await getCheck();
        const done = (text, extra = []) => { pending.replaceChildren(el("span", { textContent: text }), ...extra); sendBtn.disabled = false; log.scrollTop = log.scrollHeight; };
        if (!r) return done(`I could not check this page, so I can't answer yet (${why || "no answer"}${/running|answered|Failed to fetch/i.test(why || "") ? "; the SafeShelf API may be slow or down" : ""}).`);
        try {
          askLive({ type: "safeshelf:chat", product_id: r.product_id || "unmatched", message: question, language: lang.value,
            session_id: sid, context: chatContext(r), history: convo.slice(-7, -1).map((m) => ({ role: m.role, text: m.text })) }, pending, (res) => {
            if (!res?.ok) return done(`Could not get an answer: ${res?.error || chrome.runtime.lastError?.message}. Is the API running?`);
            const a = res.result;
            convo.push({ role: "bot", text: a.text, evidence: a.evidence_ids });
            const speakA = el("button", { type: "button", className: "small", textContent: "Listen" });
            speakA.setAttribute("aria-label", "Read this answer aloud");
            speakA.onclick = () => { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(a.text); u.lang = lang.value === "hi" ? "hi-IN" : "en-IN"; speechSynthesis.speak(u); };
            done(a.text, [
              evidenceBlock(a.evidence_ids),
              stepsBlock(a.steps),
              ...(a.source === "mock" ? [el("div", { className: "muted", textContent: "Demo answer: not a real finding." })] : []),
              speakA,
            ]);
          });
        } catch (_) { done("The extension was reloaded. Please refresh the page."); }
      };
      for (const q of ["Is this safe in a child's room?", "Is it genuine?", "Is there a safer option?", "Draft a refund request"]) {
        chips.append(el("button", { type: "button", textContent: q, onclick: () => ask(q) }));
      }
      form.onsubmit = (e) => { e.preventDefault(); ask(input.value); };
      chatBox.append(
        el("div", { className: "tools" }, historyBtn, clearBtn, closeChat),
        el("div", { className: "card" },
          brandRow("AI"),
          el("h2", { className: "headline", textContent: "Ask anything about this product" }),
          ctxHolder, log, histView, chips, form, clearNote,
        ),
      );
      chatBox.addEventListener("keydown", (e) => { if (e.key === "Escape") { setChatOpen(false); chatBtn.focus(); } });

      setChatOpen = (open) => {
        chatBox.hidden = !open;
        chatBtn.setAttribute("aria-expanded", String(open));
        if (open) { setOpen(false); ctxHolder.replaceChildren(el("div", { className: "ctx-h", textContent: "Page context used to identify this product:" }), contextCard(getPage())); input.focus(); } else speechSynthesis.cancel();
      };
      resetChat = () => { archive(); showHistory(false); clearNote.textContent = ""; setChatOpen(false); }; // a new product starts a fresh chat; the old one goes to History
      chatBtn.onclick = () => setChatOpen(chatBox.hidden);
    }
    fab.onclick = toggle;
    box.addEventListener("keydown", (e) => { if (e.key === "Escape") { setOpen(false); fab.focus(); } });
    return { host, toggle, reset, remove() { host.remove(); pop?.remove(); } };
  };

  // Shops navigate without full page loads: floating button on product pages, one button per card on results pages.
  let enabled = false; // stays off until the saved on/off choice has been read
  const floating = createWidget(readPage, "float");
  const inline = new Set();
  let lastUrl = location.href;

  const tick = () => {
    if (!enabled) { // turned off from the toolbar menu: remove everything we added
      speechSynthesis.cancel();
      toastHost?.remove();
      floating.host.remove();
      inline.forEach((w) => w.remove());
      inline.clear();
      document.querySelectorAll("[data-safeshelf-card]").forEach((c) => delete c.dataset.safeshelfCard);
      return;
    }
    if (site.isProduct()) {
      inline.forEach((w) => w.remove());
      inline.clear();
      if (!floating.host.isConnected) document.body.append(floating.host);
      if (location.href !== lastUrl) { lastUrl = location.href; floating.reset(); }
      return;
    }
    lastUrl = location.href;
    floating.host.remove();
    floating.reset();
    if (!site.cards) return;
    for (const card of document.querySelectorAll(site.cards.selector)) {
      if (card.dataset.safeshelfCard) continue;
      card.dataset.safeshelfCard = "1";
      if (getComputedStyle(card).position === "static") card.style.position = "relative"; // anchor for the corner button; no layout change
      const w = createWidget(() => readCard(card), "inline");
      inline.add(w);
      card.append(w.host);
    }
  };
  const timer = setInterval(tick, 1000);

  const onMessage = (msg, _s, reply) => {
    if (msg === "safeshelf:toggle") { tick(); if (floating.host.isConnected) floating.toggle(); }
  };
  chrome.runtime.onMessage.addListener(onMessage);
  window.__safeshelf = {
    cleanup() {
      clearInterval(timer);
      toastHost?.remove();
      floating.host.remove();
      inline.forEach((w) => w.remove());
      document.querySelectorAll("[data-safeshelf-card]").forEach((c) => delete c.dataset.safeshelfCard);
      chrome.runtime.onMessage.removeListener(onMessage);
    },
  };

  const setEnabled = (value) => { enabled = value !== false; tick(); };
  chrome.storage.local.get("enabled", ({ enabled: v }) => setEnabled(v));
  const onStorage = (changes, area) => { if (area === "local" && changes.enabled) setEnabled(changes.enabled.newValue); };
  chrome.storage.onChanged.addListener(onStorage);
  const oldCleanup = window.__safeshelf.cleanup;
  window.__safeshelf.cleanup = () => { chrome.storage.onChanged.removeListener(onStorage); oldCleanup(); };
}
