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
  const TEST_SHOPS = /^safeshelf-shops\.(web\.app|firebaseapp\.com)$/;
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
      reviews: { item: "[data-hook='review']", title: "[data-hook='review-title'] span:not(.a-letter-space):not(.a-icon-alt), [data-hook='reviewTitle']", body: "[data-hook='reviewRichContentContainer'], [data-hook='review-body'], [data-hook='reviewText']", rating: "[data-hook='review-star-rating'], [data-hook='cmps-review-star-rating']", date: "[data-hook='review-date']", verified: "[data-hook='avp-badge'], [data-hook='avp-badge-linkless']" }, // Amazon's 2025 and 2026 markup
      // The star summary above the reviews: every rating, not only the few reviews shown. For "Is it any good?".
      ratings: { average: "[data-hook='rating-out-of-text'], #acrPopover", count: "[data-hook='total-review-count'], #acrCustomerReviewText", bars: "#histogramTable [aria-label], #histogramTable li, #histogramTable tr" },
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
      // the local demo pages, and the SafeShelf test shops (shops/, hosted): the seven test products as real pages
      match: (h) => h === "localhost" || TEST_SHOPS.test(h),
      isProduct: () => !!document.body.dataset.safeshelfListingId,
      title: "#title",
      price: "#price",
      seller: "#seller",
      images: "#gallery img",
      anchor: "#price",
      hiddenText: true, // demo pages carry a hidden prompt-injection test
      reviews: { item: "article.review", title: "strong", body: "p", rating: ".stars", date: "time", verified: ".verified" },
      ratings: { average: "#ratings .avg", count: "#ratings .count", bars: "#ratings li" },
      cards: { selector: ".result[data-listing-id]", title: ".result-title", price: ".result-price", link: "a", image: "img" },
    },
  ];
  const site = SITES.find((s) => s.match(location.hostname)) || GENERIC;

  // Keeps personal details out of what is sent: delivery address, account name, emails, phone numbers.
  const PRIVATE_LINE = /^(deliver(ing)? to\b|hello,|hi,|your account|sign in|[A-Za-z .]+ [1-9]\d{5}$)/i;
  // Buttons and delivery noise that says nothing about the product.
  // Tab labels, Rufus suggestions, protection-plan offers and short questions: page furniture that says nothing about the product.
  const FURNITURE = /^(product information|features & specs|additional details|item details|measurements|feedback|from the brand|from the manufacturer|top|about this item|similar|questions|reviews|product description|rufus ai|looking for specific info\??|style|camera|battery|battery life|display|connectivity|video|navigation|user guide|see more|› see more product details|add a protection plan:?|gift options|available at checkout|visit the .{1,40} store|would you like to tell us about a lower price\??|click to play video|read more)$/i;
  const OFFER_LINE = /(?:protection|warranty|screen protect|accidental|liquid damage|extended)[^\n]*₹\s?[\d,]+/i;
  const QUESTION_LINE = /^[^.!]{4,70}\?$/;
  const NOISE_LINE = /^(add to cart|buy now|quantity:?\s*\d*|this will be a gift|add to wish list|add additional items|payment|secure transaction|details|price history|overnight|in stock|free delivery\b.*|link device to your amazon.*)$/i;
  // `seen` is shared between sections so a long line is sent once. Short lines are kept: they are labels paired with values.
  const scrub = (t, seen = new Set()) =>
    t.split("\n").map((l) => l.trim())
      .filter((l) => l && (l.length > 2 || /[A-Za-z]/.test(l)) && !PRIVATE_LINE.test(l) && !NOISE_LINE.test(l) && !FURNITURE.test(l) && !OFFER_LINE.test(l) && !QUESTION_LINE.test(l))
      .filter((l) => l.length < 25 || (!seen.has(l) && seen.add(l)))
      .join("\n")
      .replace(/[\w.+-]+@[\w-]+\.[\w.]+/g, "[email]")
      .replace(/(?<!\d)(\+?91[ -]?)?[6-9]\d{9}(?!\d)/g, "[phone]");

  // Drops tracking parameters. Amazon pages become https://host/dp/ASIN, Flipkart keeps its product id.
  const cleanUrl = () => {
    const u = new URL(location.href);
    // Demo pages and test shops name the shop address they stand for, so the API checks that address, not theirs.
    const canonical = document.querySelector('link[rel="canonical"]')?.href;
    if ((/^(localhost|127\.0\.0\.1)$/.test(u.hostname) || TEST_SHOPS.test(u.hostname)) && canonical) return canonical;
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
  // The shop's own "Model Number" row, even when it sits in a collapsed tab or a comparison table (innerText skips
  // hidden text; Amazon.com puts "Item details" in a closed tab). Official notices are matched on this number.
  const modelHint = () => {
    const m = (document.body?.textContent || "").match(/\b(?:Item\s+)?Model\s*(?:Number|No\.?)\s*[:\s\u200e\u200f]{1,6}([A-Za-z0-9][A-Za-z0-9\-/.]{2,24})/i);
    return m && /\d/.test(m[1]) ? `Model Number: ${m[1]}` : "";
  };

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
    // The M.R.P. in the main price box: Amazon marks it as the basis price. Not the struck-through price per 100 g
    // (apex-priceperunit-value, misread as the M.R.P. on 15 Oct) nor a sponsored product's M.R.P. further down.
    const mrp = (qs("#corePriceDisplay_desktop_feature_div .basisPrice .a-offscreen, #apex_desktop .basisPrice .a-offscreen, #corePrice_feature_div .basisPrice .a-offscreen")
      || [...document.querySelectorAll("#corePriceDisplay_desktop_feature_div .a-price.a-text-price:not(.apex-priceperunit-value) .a-offscreen")].find((e) => !e.closest(".pricePerUnit"))
      || (site.title === "#productTitle" ? null : qs(".a-price.a-text-price .a-offscreen")))?.textContent.trim();
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
      page_text: [asin && `ASIN: ${asin}`, modelHint(), mrp && `M.R.P.: ${mrp}`, details.slice(0, 1800), area.slice(0, 1000) + hidden].filter(Boolean).join("\n").slice(0, 3000),
      reviews: readReviews(),
      listing_id: document.body.dataset.safeshelfListingId || null,
      product_id: document.body.dataset.safeshelfProductId || null,
    };
  };

  // Up to 30 reviews from the page: title, text, stars and date only. Emails and phone numbers are masked.
  // root: this page, or another page of the same shop read in the background (the critical-reviews page).
  // A review is cut to its first REVIEW_CHARS: the complaint or the praise is up front, and long ones repeat themselves.
  const REVIEW_CHARS = 700;
  // The same review read twice differs in spacing and a trailing "Read more": letters and digits only, in any script.
  const reviewKey = (x) => (x.text || "").toLowerCase().replace(/read more$/, "").replace(/[^\p{L}\p{N}]+/gu, "").slice(0, 160);
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
        text: mask(words(inside(el, r.body))).replace(/\s*Read more\s*$/i, "").slice(0, REVIEW_CHARS),
        rating,
        date: isNaN(parsed) ? null : parsed.toISOString().slice(0, 10),
        ...(r.verified ? { verified_purchase: !!inside(el, r.verified) } : {}),
      };
    }).filter((x) => x.text);
  };

  // The star summary: "4.1 out of 5", "3,412 ratings" and the percent of ratings per star. null when the shop shows none.
  // Falls back to schema.org data (average and count only, no bars).
  const readRatingSummary = () => {
    const r = site.ratings;
    const words = (n) => (n ? `${n.getAttribute("title") || ""} ${n.getAttribute("aria-label") || ""} ${n.textContent || ""}` : "");
    const average = Number(words(r && qs(r.average)).match(/([\d.]+) out of 5/)?.[1]) || null;
    const count = Number(words(r && qs(r.count)).replace(/,/g, "").match(/(\d+)\s*(global\s+)?(ratings?|reviews?)/i)?.[1]) || null;
    const distribution = {};
    for (const bar of r?.bars ? document.querySelectorAll(r.bars) : []) {
      const t = words(bar).replace(/\s+/g, " ");
      const said = t.match(/(\d{1,3})\s*percent of (?:reviews|ratings) have ([1-5]) stars?/i); // "58 percent of reviews have 5 stars"
      const shown = t.match(/\b([1-5])\s*stars?\b[^\d%]{0,20}(\d{1,3})\s*%/i); // "5 star 58%"
      const [star, pct] = said ? [said[2], said[1]] : shown ? [shown[1], shown[2]] : [];
      if (star && !(star in distribution)) distribution[star] = Number(pct);
    }
    const agg = jsonLd()?.aggregateRating;
    const summary = { average: average ?? (Number(agg?.ratingValue) || null), count: count ?? (Number(agg?.ratingCount || agg?.reviewCount) || null),
      ...(Object.keys(distribution).length === 5 ? { distribution } : {}) };
    return summary.average || summary.count || summary.distribution ? summary : null;
  };

  // Amazon shows only a few reviews on the product page, mostly positive. The product's critical (1-3 star) reviews
  // page is read here, in the shopper's own browser where they are signed in and Amazon does not block it, and its
  // reviews go first, since hazard reports live there. Remembered per product and page for the visit.
  // The quick check reads page 1; a first look at a product SafeShelf has never seen reads pages 1-3 (up to 60).
  const criticalCache = new Map();
  // filter: "critical" (1-3 stars), or one star level ("one_star" ... "five_star", for "Is it any good?").
  // sort: "recent", or "helpful" (the reviews other buyers found most useful: they explain a problem best).
  // A page that could not be read is an empty list marked failed, so "no reviews" is never claimed from a failed fetch.
  const failedPage = () => Object.assign([], { failed: true });
  const criticalPage = (asin, n, filter = "critical", sort = "recent") => {
    const key = `${asin}|${filter}|${sort}|${n}`;
    if (!criticalCache.has(key)) {
      criticalCache.set(key, (async () => {
        try {
          const res = await fetch(`/product-reviews/${asin}/?filterByStar=${filter}&sortBy=${sort}&reviewerType=all_reviews&pageNumber=${n}`, { credentials: "include" });
          if (!res.ok || /\/ap\/signin/.test(res.url)) return failedPage();
          return readReviews(new DOMParser().parseFromString(await res.text(), "text/html"));
        } catch (_) { return failedPage(); }
      })());
    }
    return criticalCache.get(key);
  };
  const criticalReviews = async (pages = 1) => {
    const asin = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/)?.[1];
    if (!asin || !/(^|\.)amazon\./.test(location.hostname)) return [];
    const out = [];
    for (let n = 1; n <= pages; n++) {
      const got = await criticalPage(asin, n);
      out.push(...got);
      if (got.length < 10) break; // a short page is the last one
    }
    return out;
  };
  const withMoreReviews = async (page, pages = 1, limit = 30) => {
    const extra = await criticalReviews(pages);
    if (!extra.length) return page;
    const seen = new Set();
    const reviews = [...extra, ...(page.reviews || [])].filter((x) => !seen.has(reviewKey(x)) && seen.add(reviewKey(x))).slice(0, limit);
    return { ...page, reviews };
  };
  window.__safeshelfMoreReviews = withMoreReviews;

  // sellerAge: when the product was first listed, from the page's own "Date First Available" (no other page is opened).
  // The product-details tables first; then the whole page text (the row sits in different places on different listings,
  // and in collapsed sections). A date-shaped capture only, so nothing else is picked up.
  const DATE_FIRST = /Date First Available\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4}|\d{1,2}\/\d{1,2}\/\d{4})/i;
  const tidy = (t) => (t || "").replace(/[\u200e\u200f]/g, "").replace(/\s+/g, " ");
  const readFirstAvailable = () => {
    const rows = "#productDetails_detailBullets_sections1 tr, #productDetails_techSpec_section_1 tr, #productDetails_techSpec_section_2 tr, #productDetails_db_sections tr, #prodDetails tr, #detailBullets_feature_div li, #detailBulletsWrapper_feature_div li, [id^='productDetails'] tr";
    for (const row of document.querySelectorAll(rows)) {
      const found = tidy(row.textContent).match(DATE_FIRST);
      if (found) return found[1].trim();
    }
    return tidy(document.body?.textContent).match(DATE_FIRST)?.[1].trim() || null;
  };

  // "Is it any good?": one page (about 10 reviews) per star level, so every kind of buyer is heard, and the page's own
  // reviews, at most 60, plus the star summary that covers every rating. The server weights each star by its real
  // share of all ratings. 1-3 star pages are the most helpful first (they explain a problem best), 4-5 the newest.
  // Read after the card is shown, in the shopper's own browser.
  const STAR_PAGES = [["one_star", "helpful"], ["two_star", "helpful"], ["three_star", "helpful"], ["four_star", "recent"], ["five_star", "recent"]];
  // sellerAge: Amazon's brand card ("Top Brand · Portronics · 84% positive ratings from 10K+ customers · 10+ years on Amazon"):
  // a short slice of the page text around it. The server reads the numbers; this is the BRAND's tenure, not the seller's.
  const readBrandText = () => {
    const flat = tidy(document.body?.textContent);
    const at = flat.search(/positive ratings from/i);
    return at < 0 ? undefined : flat.slice(Math.max(0, at - 80), at + 260);
  };
  // sellerAge, for a page with no "Date First Available": what the product's reviews say about its age. The review pages are
  // the ones already read for resultVerdict (cached, so no extra requests). complete is true only when every star level's
  // first page held fewer than 10 reviews (there is no next page) and none failed: then the oldest review is the first one,
  // and "no reviews" is true. null off Amazon.
  const reviewCoverage = async () => {
    const asin = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/)?.[1];
    if (!asin || !/(^|\.)amazon\./.test(location.hostname)) return null;
    const pages = await Promise.all(STAR_PAGES.map(([star, sort]) => criticalPage(asin, 1, star, sort)));
    const seen = new Set();
    const all = [...pages.flat(), ...readReviews()].filter((x) => !seen.has(reviewKey(x)) && seen.add(reviewKey(x)));
    const dates = all.map((x) => x.date).filter(Boolean).sort();
    return { oldest: dates[0] || null, read: all.length, complete: !pages.some((p) => p.failed) && pages.every((p) => p.length < 10),
      ratings: readRatingSummary()?.count ?? null };
  };
  const reviewsForVerdict = async (page) => {
    const asin = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/)?.[1];
    const amazon = asin && /(^|\.)amazon\./.test(location.hostname);
    const extra = amazon ? (await Promise.all(STAR_PAGES.map(([star, sort]) => criticalPage(asin, 1, star, sort)))).flat() : [];
    const seen = new Set();
    const reviews = [...extra, ...(page.reviews || [])].filter((x) => !seen.has(reviewKey(x)) && seen.add(reviewKey(x))).slice(0, 60);
    return { url: page.url, title: page.title, page_text: page.page_text, currency: page.currency, reviews, rating_summary: readRatingSummary() };
  };

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

  // Design tokens shared by every shadow root, in the website's theme: white panels, ink #001123, blue #0271E4, mint #A2F1A9.
  // --lime / --lime-d are the accent (pale and strong); their names stay so Settings > Theme accents keep working.
  const TOKENS = `
    :host { --ink:#001123; --ink-2:#26323f; --muted:#5d6874; --line:#e4e7eb; --soft:#f5f6f7; --card:#ffffff; --lime:#e8f2fd; --lime-d:#0271e4; --link:#0271e4;
      --blue:#0271e4; --blue-2:#0a5fc0; --mint:#a2f1a9; --mint-ink:#12632a;
      --green:#1d7f3e; --green-bg:#e4f7e6; --amber:#a35f00; --amber-bg:#fff2dc; --red:#c93a2f; --red-bg:#fdebe9; --unknown:#4f5a66; --unknown-bg:#eceff2;
      --font:"Helvetica Neue",Helvetica,Arial,system-ui,-apple-system,"Segoe UI",sans-serif;
      --shield:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M4 8a6 6 0 0 1 6-6h12a6 6 0 0 1 6 6v8c0 7-5.5 12-12 14C9.5 28 4 23 4 16z' fill='%230271E4'/%3E%3Cpath d='m10.5 16 4 4 7-8' fill='none' stroke='%23fff' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
      --shadow:0 24px 60px rgba(0,17,35,.22), 0 0 0 1px rgba(0,17,35,.06);
      --icon-stroke:2; }
    /* Settings > Theme: accent, font and icon weight arrive as attributes on each host (see themed() below). Blue is the default. */
    :host([data-accent=lime]) { --lime:#e9f6c8; --lime-d:#7aa82a; } :host([data-accent=mint]) { --lime:#e1f8e4; --lime-d:#2f9a4a; } :host([data-accent=sky]) { --lime:#e3f1fc; --lime-d:#3a8fd8; }
    :host([data-accent=lilac]) { --lime:#efeafd; --lime-d:#7b5cd6; } :host([data-accent=peach]) { --lime:#fdeee4; --lime-d:#d8743a; } :host([data-accent=sand]) { --lime:#f6f0df; --lime-d:#a4874a; }
    :host([data-font=geist]) { --font:Geist,"Helvetica Neue",Helvetica,Arial,system-ui,sans-serif; }
    :host([data-font=system]) { --font:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
    :host([data-font=rounded]) { --font:ui-rounded,"SF Pro Rounded",Nunito,system-ui,sans-serif; }
    :host([data-font=serif]) { --font:"Iowan Old Style",Palatino,Georgia,serif; }
    :host([data-icons=light]) { --icon-stroke:1.5; } :host([data-icons=bold]) { --icon-stroke:2.6; }
    svg:not(.ring) :is(path, rect, circle, line, polyline) { stroke-width:var(--icon-stroke); }
  `;
  // Theme settings for the widget, read from storage below and kept up to date. Every shadow host is painted with them.
  const LOOK = { accent: ["blue","lime","mint","sky","lilac","peach","sand"], font: ["geist","system","rounded","serif"], icons: ["regular","light","bold"],
    widgetSide: ["right","left"], widgetSize: ["regular","compact"], widgetSurface: ["glass","solid"], widgetChat: ["popup","drawer"] };
  const look = Object.fromEntries(Object.entries(LOOK).map(([k, v]) => [k, v[0]]));
  const themedHosts = new Set();
  const paintLook = (h) => Object.assign(h.dataset, { accent: look.accent, font: look.font, icons: look.icons, side: look.widgetSide, size: look.widgetSize, surface: look.widgetSurface, chat: look.widgetChat });
  const themed = (h) => { themedHosts.add(h); paintLook(h); return h; };
  // Chat as a drawer docks at the browser edge: the page gets narrower by the drawer's width, like a browser side panel.
  let dockStyle = null;
  const dock = (side, px) => {
    if (!px) { dockStyle?.remove(); dockStyle = null; return; }
    if (!dockStyle) { dockStyle = document.createElement("style"); (document.head || document.documentElement).append(dockStyle); }
    dockStyle.textContent = `html { margin-${side}:${px}px !important; transition:margin .2s ease; }`;
  };
  // Where the rail sits along the edge, as a % of the window height; set by dragging its handle.
  let widgetY = 50;
  const clampY = (y) => Math.min(92, Math.max(8, Number(y) || 50));
  const placeY = (h, y = widgetY) => h.style?.setProperty?.("--ss-y", `${y}%`);
  // Keeps the whole rail on screen: its centre stays at least half its height (plus a margin) from the top and bottom.
  const fitY = (h, y) => {
    const vh = innerHeight || 800, half = ((h.getBoundingClientRect?.().height || 0) / 2 + 8) / vh * 100;
    return Math.min(100 - half, Math.max(half, clampY(y)));
  };
  const readLook = (data) => { for (const [k, v] of Object.entries(LOOK)) if (k in data) look[k] = v.includes(data[k]) ? data[k] : v[0]; themedHosts.forEach(paintLook); };

  const PANEL_STYLE = `
    .tabs { display:flex; flex-wrap:nowrap; gap:0; margin:14px -18px 12px; padding:0 10px; overflow-x:auto; scrollbar-width:none; border-bottom:1px solid var(--line); }
    .tabs::-webkit-scrollbar { display:none; } .tabs { -webkit-mask:linear-gradient(90deg,#000 85%,transparent); mask:linear-gradient(90deg,#000 85%,transparent); } .tabs:hover, .tabs:focus-within { -webkit-mask:none; mask:none; }
    .tab { flex:none; font:inherit; font-size:13px; font-weight:500; padding:10px 9px; border:0; border-radius:0; background:transparent; color:var(--muted); cursor:pointer; white-space:nowrap; box-shadow:inset 0 0 0 transparent; transition:color .12s ease, box-shadow .2s ease; }
    .tab:hover { color:var(--blue); }
    .tab[aria-selected="true"] { color:var(--ink); box-shadow:inset 0 -2px 0 var(--lime-d); }
    .vrow { display:flex; gap:8px; margin:6px 0; } .vrow .i { flex:none; width:1.4em; text-align:center; } .vrow .i svg { width:17px; height:17px; vertical-align:-3px; }
    .vrow .i[data-icon=ok] { color:var(--green); } .vrow .i[data-icon=stop] { color:var(--red); } .vrow .i[data-icon=warn] { color:var(--amber); } .vrow .i[data-icon=unknown], .vrow .i[data-icon=dot] { color:var(--muted); }
    .vrow .s { color:var(--muted); font-size:13px; } .vrow a { font-size:13px; color:var(--link); }
    .vh { font-weight:600; font-size:17px; letter-spacing:-.02em; margin:14px 0 2px; } .vnote { color:var(--muted); font-size:13px; margin:4px 0; }
    .notlive { background:var(--soft); border-radius:8px; padding:10px 12px; color:var(--ink); font-size:14px; }
    textarea.rep { width:100%; box-sizing:border-box; min-height:80px; font:inherit; font-size:14px; padding:10px 12px; border:1px solid var(--line); border-radius:4px; color:var(--ink); background:var(--soft); }
  `;

  const CTX_STYLE = `
    .ctx { display:flex; gap:10px; border-radius:10px; padding:10px; margin:8px 0; background:#fff; border:1px solid var(--line); color:var(--ink); font:13px/1.4 var(--font); }
    .ctx > img { width:56px; height:56px; object-fit:contain; background:var(--soft); border-radius:8px; flex:none; }
    .ctx .body { min-width:0; flex:1; }
    .ctx .t { font-weight:600; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
    .ctx .m { color:var(--muted); } .ctx s { color:var(--muted); }
    .ctx .chips { display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; justify-content:flex-start; }
    .ctx .chip { border-radius:99px; padding:1px 8px; font-size:12px; background:var(--soft); color:var(--ink); }
    .ctx .more { font:inherit; font-size:12px; padding:0; border:0; background:none; color:var(--link); cursor:pointer; text-decoration:underline; margin-top:6px; }
    .ctx pre { white-space:pre-wrap; word-break:break-word; max-height:180px; overflow:auto; margin:6px 0 0; font:12px/1.4 ui-monospace,monospace; background:var(--soft); border-radius:6px; padding:8px; }
    .ctx-h { font-size:12px; color:var(--muted); margin-top:10px; }
  `;

  const STYLE = `
    ${TOKENS}
    :host { all:initial; display:flex; font:15px/1.5 var(--font); color:var(--ink); letter-spacing:-.01em; }

    /* Side rail: frosted strip of soft square buttons */
    :host(.float) { position:fixed; right:0; top:50%; transform:translateY(-50%); z-index:2147483647; flex-direction:row; align-items:center; gap:12px; }
    :host(.float) .bar { flex-direction:column; gap:6px; padding:8px 7px 10px 8px; background:rgba(255,255,255,.92); backdrop-filter:blur(14px); border:1px solid var(--line); border-right:0; border-radius:14px 0 0 14px; box-shadow:-10px 14px 36px rgba(0,17,35,.16); }
    :host(.float) .fab { position:relative; width:44px; height:44px; padding:0; border-radius:10px; display:grid; place-items:center; }
    :host(.float[data-side=left]) { right:auto; left:0; flex-direction:row-reverse; }
    :host(.float[data-side=left]) .bar { border-left:0; border-right:1px solid var(--line); border-radius:0 14px 14px 0; padding:8px 8px 10px 7px; box-shadow:10px 14px 36px rgba(0,17,35,.16); }
    :host(.float[data-side=left]) .tip { right:auto; left:calc(100% + 12px); }
    :host(.float[data-size=compact]) .bar { gap:6px; padding-top:8px; padding-bottom:8px; }
    :host(.float[data-size=compact]) .fab { width:38px; height:38px; border-radius:8px; } :host(.float[data-size=compact]) .fab svg:not(.ring) { width:20px; height:20px; }
    :host(.float[data-surface=solid]) .bar { background:#fff; backdrop-filter:none; }
    :host(.float.shelf-only) .fab:not(.go-shelf), :host(.float.shelf-only) .box { display:none !important; } /* not a product page */
    :host(.float) { top:var(--ss-y,50%); }
    .grip { display:grid; place-items:center; width:44px; height:14px; margin:-4px 0 -2px; padding:0; border:0; border-radius:6px; background:none; cursor:grab; touch-action:none; }
    .grip::before { content:""; width:22px; height:4px; border-radius:2px; background:var(--muted); opacity:.45; transition:opacity .12s; }
    .grip:hover::before, .grip:focus-visible::before { opacity:.85; } .grip:focus-visible { outline:2px solid var(--link); outline-offset:2px; }
    :host(.float[data-size=compact]) .grip { width:38px; }
    :host(.float.dragging) { user-select:none; } :host(.float.dragging) .grip { cursor:grabbing; } :host(.float.dragging) .bar { box-shadow:0 14px 40px rgba(0,17,35,.28); }
    :host(.float.drawer-open) .grip { display:none; }
    /* Panels as a drawer (Settings > Theme), while the check or chat is open: one solid full-height panel flush with the window edge.
       The button rail becomes the panel's outer column, each icon with its short name under it. */
    :host(.float[data-chat=drawer].drawer-open) { top:0; bottom:0; transform:none; gap:0; align-items:stretch; }
    :host(.float[data-chat=drawer].drawer-open) .bar { justify-content:flex-start; gap:6px; padding:16px 8px; border:0; border-left:1px solid var(--line); border-radius:0; background:var(--card); backdrop-filter:none; box-shadow:none; }
    :host(.float[data-chat=drawer].drawer-open) .fab { width:60px; height:auto; padding:9px 0 7px; display:flex; flex-direction:column; align-items:center; gap:4px; border-radius:8px; background:transparent; }
    :host(.float[data-chat=drawer].drawer-open) .fab:hover { background:var(--soft); }
    :host(.float[data-chat=drawer].drawer-open) .fab::after { content:attr(data-short); font-size:11px; font-weight:500; color:var(--muted); }
    :host(.float[data-chat=drawer].drawer-open) .fab[aria-expanded="true"] { background:var(--lime); border-color:transparent; }
    :host(.float[data-chat=drawer].drawer-open) .fab[aria-expanded="true"]::after { color:var(--lime-d); }
    :host(.float[data-chat=drawer].drawer-open) .tip { display:none; }
    :host(.float[data-chat=drawer].drawer-open) .box:not([hidden]) { width:min(420px,calc(100vw - 90px)); max-height:none; padding:0; border-radius:0; border-top:0; background:var(--card); box-shadow:none; border-left:1px solid var(--line); animation:ss-drawer .22s ease-out; }
    @keyframes ss-drawer { from { transform:translateX(28px); opacity:0; } }
    :host(.float[data-chat=drawer].drawer-open) .box:not([hidden]) > .card { min-height:100%; border-radius:0; box-shadow:none; padding:20px; }
    :host(.float[data-chat=drawer].drawer-open) .box.chat > .card { flex:1; min-height:0; }
    :host(.float[data-chat=drawer].drawer-open) .chat .log { flex:1; max-height:none; }
    :host(.float[data-chat=drawer].drawer-open) .chat .ask { margin-top:auto; } /* the question box sits at the bottom of the drawer */
    :host(.float[data-chat=drawer][data-side=left].drawer-open) .bar { border-left:0; border-right:1px solid var(--line); }
    :host(.float[data-chat=drawer][data-side=left].drawer-open) .box:not([hidden]) { border-left:0; border-right:1px solid var(--line); animation-name:ss-drawer-left; }
    @keyframes ss-drawer-left { from { transform:translateX(-28px); opacity:0; } }
    .tip { position:absolute; right:calc(100% + 12px); top:50%; transform:translateY(-50%); background:var(--ink); color:#fff; padding:6px 11px; border-radius:6px; font-size:12.5px; font-weight:500; white-space:nowrap; opacity:0; pointer-events:none; transition:opacity .12s ease; }
    .fab:hover .tip, .fab:focus-visible .tip { opacity:1; }
    .fab { font:inherit; font-weight:600; padding:10px 18px; border:1px solid transparent; border-radius:10px; background:var(--soft); color:var(--ink-2); cursor:pointer; transition:transform .12s ease, background-color .12s ease, color .12s ease; }
    .fab:hover { background:var(--lime); color:var(--lime-d); }
    .fab:active { transform:scale(.96); }
    .fab[aria-expanded="true"] { background:var(--lime); border-color:var(--lime-d); }
    .fab:focus-visible { outline:2px solid var(--lime-d); outline-offset:2px; }
    .fab:disabled { opacity:.6; cursor:default; }
    .fab.just-saved { background:var(--green-bg); color:var(--green); } .fab.just-saved svg { animation:ss-pop .28s cubic-bezier(.3,.7,.4,1.4); }
    .fab.saved { background:var(--lime); border-color:var(--lime-d); color:var(--lime-d); } .fab.saved svg path { fill:currentColor; }
    @keyframes ss-pop { from { transform:scale(.5); opacity:0; } }
    .fab .ring { position:absolute; inset:-5px; width:calc(100% + 10px); height:calc(100% + 10px); pointer-events:none; overflow:visible; }
    .fab .ring rect { fill:none; stroke-width:2.5; } .fab .ring .track { stroke:var(--lime-d); opacity:.55; }
    .fab .ring .seg { stroke:var(--lime-d); stroke-linecap:round; stroke-dasharray:24 76; animation:ss-ring 1.1s linear infinite; }
    .fab.loading[aria-expanded="true"] { border-color:transparent; box-shadow:none; }
    @keyframes ss-ring { to { stroke-dashoffset:-100; } }
    .fab.unknown { background:var(--unknown-bg); color:var(--unknown); }
    .fab.green { background:var(--green-bg); color:var(--green); } .fab.amber { background:var(--amber-bg); color:var(--amber); } .fab.red { background:var(--red-bg); color:var(--red); }
    .fab.green[aria-expanded="true"] { box-shadow:0 0 0 2px #fff, 0 0 0 4px #3bbf63; } .fab.amber[aria-expanded="true"] { box-shadow:0 0 0 2px #fff, 0 0 0 4px #f0a020; } .fab.red[aria-expanded="true"] { box-shadow:0 0 0 2px #fff, 0 0 0 4px var(--red); } .fab.unknown[aria-expanded="true"] { box-shadow:0 0 0 2px #fff, 0 0 0 4px #9aa3ad; }
    :host(.inline) { display:block; position:absolute; bottom:12px; right:12px; z-index:100; }
    :host(.inline) .fab { padding:4px 11px; font-size:12px; white-space:nowrap; border-radius:4px; border-color:#fff; box-shadow:0 2px 10px rgba(0,17,35,.18); }
    :host(.inline) .bar { gap:6px; }
    .bar { display:flex; gap:8px; align-items:center; }

    /* Panels: pastel frame (tinted by the verdict) around a white card */
    .box { box-sizing:border-box; width:min(400px,calc(100vw - 100px)); max-height:76vh; overflow:auto; scrollbar-width:thin; padding:0; border-radius:14px; background:var(--card); border-top:4px solid var(--lime-d); box-shadow:var(--shadow); }
    .box.green { border-top-color:#3bbf63; } .box.amber { border-top-color:#f0a020; } .box.red { border-top-color:var(--red); } .box.unknown { border-top-color:#9aa3ad; }
    .box[hidden] { display:none; }
    :host(.pop) { position:fixed; top:0; left:0; z-index:2147483647; }
    :host(.pop) .box { position:fixed; }
    .card { background:var(--card); border-radius:10px; padding:16px 18px 18px; box-shadow:none; }
    .brand-row { display:flex; align-items:center; justify-content:center; gap:6px; font-size:14px; }
    .brand-row .mark { display:block; width:22px; height:22px; flex:none; font-size:0; color:transparent; background:var(--shield) center / contain no-repeat; }
    .brand-row .brand { font-size:15.5px; font-weight:600; letter-spacing:-.02em; }
    .badge { font-size:11px; font-weight:500; padding:2px 8px; border-radius:99px; background:var(--soft); color:var(--muted); }
    .headline { margin:6px 0 0; text-align:center; font-size:24px; line-height:1.15; font-weight:600; letter-spacing:-.03em; color:var(--ink); }
    .headline.green { color:var(--green); } .headline.amber { color:var(--amber); } .headline.red { color:var(--red); } .headline.unknown { color:var(--unknown); }
    @keyframes pulse { 50% { transform:scale(.85); opacity:.6; } }

    /* Card header: brand on the left, small icon buttons on the right */
    .head { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:-4px -6px 0 0; }
    .head .brand-row { justify-content:flex-start; min-width:0; }
    .head .badge { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:150px; }
    .icons { display:flex; gap:2px; }
    .ibtn { font:inherit; font-size:12px; font-weight:500; display:inline-flex; align-items:center; justify-content:center; gap:4px; min-width:32px; height:32px; padding:0 8px; border:0; border-radius:6px; background:transparent; color:var(--muted); cursor:pointer; }
    .ibtn:hover, .ibtn[aria-pressed="true"] { background:var(--soft); color:var(--ink); }
    .ibtn svg { width:16px; height:16px; flex:none; }

    /* The verdict at the top of the card */
    .hero { display:grid; grid-template-columns:auto minmax(0,1fr); align-items:center; gap:0 12px; margin-top:12px; padding:14px 16px; border-radius:10px; background:var(--unknown-bg); text-align:left; }
    .hero.green { background:var(--green-bg); } .hero.amber { background:var(--amber-bg); } .hero.red { background:var(--red-bg); }
    .hero .ic { display:grid; place-items:center; width:44px; height:44px; margin:0; border-radius:10px; background:#fff; color:var(--unknown); box-shadow:0 2px 8px rgba(0,17,35,.08); }
    .hero.green .ic { color:var(--green); } .hero.amber .ic { color:var(--amber); } .hero.red .ic { color:var(--red); }
    .hero .ic svg { width:24px; height:24px; }
    .hero .headline { margin:0; text-align:left; font-size:23px; }
    .hero .sum { grid-column:1 / -1; margin:10px 0 0; max-width:none; font-size:14px; line-height:1.5; color:var(--ink-2); }
    .hero .upd { grid-column:1 / -1; justify-self:start; }

    /* While the check runs */
    .wait { text-align:center; padding:8px 4px 4px; }
    .wait .mark { display:inline-block; width:40px; height:40px; font-size:0; color:transparent; background:var(--shield) center / contain no-repeat; animation:pulse 1.2s ease-in-out infinite; }
    .wait strong { display:block; font-size:18px; font-weight:600; letter-spacing:-.02em; margin-top:8px; }
    .wait .stage { color:var(--muted); font-size:13px; min-height:2.8em; margin:2px auto 4px; max-width:34ch; }
    .skel { height:10px; border-radius:99px; margin:10px auto 0; background:linear-gradient(90deg, var(--soft) 25%, var(--lime) 50%, var(--soft) 75%); background-size:200% 100%; animation:shimmer 1.4s linear infinite; }
    @keyframes shimmer { to { background-position:-200% 0; } }

    /* Cancelled or failed */
    .state { text-align:center; padding:10px 4px 2px; } .state strong { display:block; font-size:17px; } .state p { color:var(--muted); font-size:14px; margin:6px 0 14px; }

    /* Actions under the result */
    .actions { display:flex; flex-direction:column; gap:8px; margin-top:14px; }
    .actions .more { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
    button.primary { font:inherit; font-size:14px; font-weight:500; display:inline-flex; gap:8px; align-items:center; justify-content:center; min-height:44px; padding:10px 16px; border:0; border-radius:4px; background:var(--lime-d); color:#fff; cursor:pointer; transition:filter .12s ease; }
    button.primary:hover { filter:brightness(.92); }
    button.primary svg { width:18px; height:18px; }
    /* First look: a product SafeShelf has never seen */
    .first { margin-top:12px; border-radius:10px; padding:10px 14px; background:#fff; border:1px solid var(--line); }
    .first h3 { margin:0 0 2px; display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:15px; }
    .first .tag { font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px; background:var(--lime); color:var(--lime-d); }
    .first .lede { color:var(--muted); font-size:13px; margin:0 0 4px; }
    .first ol { list-style:none; margin:4px 0 0; padding:0; font-size:13px; }
    .first li { display:flex; gap:8px; align-items:baseline; padding:3px 0; color:var(--muted); }
    .first li::before { content:""; flex:none; width:9px; height:9px; border-radius:50%; border:2px solid currentColor; border-top-color:transparent; animation:spin .8s linear infinite; }
    .first li.done { color:var(--ink); } .first li.done::before { content:"✓"; width:auto; height:auto; border:0; animation:none; color:var(--green); font-weight:700; }
    .first li.skip::before { content:"–"; width:auto; height:auto; border:0; animation:none; }
    .first ul.found { margin:8px 0 0; padding-left:18px; font-size:13px; } .first ul.found li { display:list-item; padding:2px 0; color:var(--ink); } .first ul.found li::before { content:none; }
    .upd { display:inline-block; margin-top:8px; font-size:12px; font-weight:600; padding:2px 10px; border-radius:999px; background:#fff; color:var(--lime-d); }
    @keyframes spin { to { transform:rotate(360deg); } }
    details.read { margin-top:10px; font-size:13px; } details.read summary { cursor:pointer; color:var(--muted); font-weight:600; }
    .foot { color:var(--muted); font-size:12px; text-align:center; margin-top:10px; }
    .demo { background:var(--amber-bg); color:var(--amber); border-radius:6px; padding:6px 10px; font-size:13px; margin-bottom:10px; text-align:center; }

    /* Verdict sections */
    .sec { border-radius:10px; padding:12px 14px; margin-top:10px; background:var(--card); border:1px solid var(--line); border-left:4px solid #9aa3ad; }
    .sec.green { border-left-color:#3bbf63; } .sec.amber { border-left-color:#f0a020; } .sec.red { border-left-color:var(--red); }
    .sec h3 { margin:0 0 2px; display:flex; justify-content:space-between; align-items:center; gap:8px; }
    .sec h3 .t { display:flex; align-items:center; gap:6px; }
    .sec h3 .t svg { width:16px; height:16px; flex:none; }
    .verdict { font-size:12px; font-weight:600; padding:2px 10px; border-radius:999px; background:var(--unknown-bg); }
    .sec.green .verdict { color:var(--green); background:var(--green-bg); } .sec.amber .verdict { color:var(--amber); background:var(--amber-bg); } .sec.red .verdict { color:var(--red); background:var(--red-bg); } .sec.unknown .verdict { color:var(--unknown); }
    .sec.green .t svg { color:var(--green); } .sec.amber .t svg { color:var(--amber); } .sec.red .t svg { color:var(--red); } .sec.unknown .t svg { color:var(--unknown); }
    /* "Is it any good?": a small widget under the verdict. Quality only, so it never uses red (red is for recalls). */
    .rv { margin:10px 0 0; padding:9px 12px; border-radius:14px; background:var(--soft); font-size:13px; line-height:1.4; }
    .rv-top { display:flex; align-items:baseline; justify-content:space-between; gap:8px; }
    .rv-word { font-weight:700; font-size:14px; } .rv.good .rv-word { color:var(--green); } .rv.mixed .rv-word, .rv.poor .rv-word { color:var(--amber); }
    .rv-stars { color:var(--muted); white-space:nowrap; } .rv-note { display:block; color:var(--muted); font-size:12px; }
    .rv-row { display:flex; gap:6px; align-items:flex-start; margin-top:5px; } .rv-row svg { width:14px; height:14px; flex:none; margin-top:2px; }
    .rv-row.up svg { color:var(--green); } .rv-row.down svg { color:var(--amber); } .rv-sub { color:var(--muted); }
    .rv-c summary { cursor:pointer; list-style:none; } .rv-c summary::-webkit-details-marker { display:none; }
    .rv-c summary::after { content:"▸"; margin-left:auto; padding-left:8px; color:var(--link); font-size:11px; } .rv-c[open] summary::after { content:"▾"; }
    .rv-revs { list-style:none; margin:6px 0 2px 20px; padding:0; display:grid; gap:8px; max-height:220px; overflow:auto; }
    .rv-revs li { padding:6px 9px; border-radius:10px; background:var(--card); font-size:12px; line-height:1.4; } .rv-meta { color:var(--amber); font-size:11px; letter-spacing:.5px; }
    /* "Is it possible?": price chart and claims. Amber at worst, never red (red is for recalls). */
    .ip { margin:10px 0 0; padding:9px 12px; border-radius:14px; background:var(--soft); font-size:13px; line-height:1.4; }
    .ip-top { display:flex; align-items:baseline; justify-content:space-between; gap:8px; } .ip-word { font-weight:700; font-size:14px; }
    .ip-sec.ok .ip-word { color:var(--green); } .ip-sec.warn .ip-word { color:var(--amber); } .ip-sec + .ip-sec { margin-top:8px; padding-top:8px; border-top:1px solid var(--line); }
    .ip-demo { font-size:11px; font-weight:700; color:var(--amber); background:var(--amber-bg); border-radius:8px; padding:1px 7px; }
    .ip-line { color:var(--muted); margin-top:2px; }
    .ip-chart { position:relative; height:10px; margin:10px 2px 4px; border-radius:5px; background:var(--line); }
    .ip-band { position:absolute; top:0; bottom:0; border-radius:5px; background:var(--green-bg); box-shadow:inset 0 0 0 1px var(--green); }
    .ip-median { position:absolute; top:-2px; bottom:-2px; width:2px; background:var(--green); }
    .ip-dot { position:absolute; top:50%; width:14px; height:14px; margin:-7px 0 0 -7px; border-radius:50%; background:var(--amber); box-shadow:0 0 0 2px var(--card); }
    .ip-sec.ok .ip-dot { background:var(--green); } .ip-sec.none .ip-dot { background:var(--unknown); }
    .ip-wait { color:var(--muted); font-size:12px; } .ip-q { color:var(--muted); font-size:12px; } .ip-sec.warn .ip-word { font-size:15px; } .ip-sec .ip-line { color:var(--ink); }
    .ip-h { margin-top:6px; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); }
    .ip-value { margin-top:6px; font-size:12px; color:var(--muted); } .ip-value strong { color:var(--ink); } .ip-value.warn strong { color:var(--amber); } .ip-value.ok strong { color:var(--green); }
    .ip-cmp { margin:4px 0 0; padding:0; list-style:none; font-size:12px; color:var(--muted); } .ip-cmp a { color:var(--link); }
    .ip-claim { display:flex; gap:6px; align-items:flex-start; margin-top:5px; } .ip-claim svg { width:14px; height:14px; flex:none; margin-top:2px; }
    .ip-claim.check svg { color:var(--green); } .ip-claim.warn svg, .ip-claim.stop svg { color:var(--amber); } .ip-claim.help svg { color:var(--unknown); }
    .ip-why { color:var(--muted); font-size:12px; } .ip-why a { color:var(--link); }
    .ip-more { margin-top:4px; } .ip-more summary { cursor:pointer; color:var(--link); font-size:12px; } .ip-more ul { margin:4px 0 0; padding-left:18px; }
    .ip.loading .ip-line { animation:ss-rv-pulse 1.2s ease-in-out infinite alternate; }
    @media (prefers-reduced-motion: reduce) { .ip.loading .ip-line { animation:none; } }
    /* sellerAge: how long the seller has been around, from their rating history. Amber for new, never red. */
    .sa { margin:10px 0 0; padding:9px 12px; border-radius:14px; background:var(--soft); font-size:13px; line-height:1.4; }
    .sa-top { display:flex; align-items:baseline; justify-content:space-between; gap:8px; } .sa-word { font-weight:700; font-size:14px; }
    .sa.ok .sa-word { color:var(--green); } .sa.warn .sa-word { color:var(--amber); } .sa-band { color:var(--muted); white-space:nowrap; font-size:12px; }
    .sa-brand { margin-top:6px; padding-top:6px; border-top:1px solid var(--line); font-size:12px; color:var(--ink); }
    .sa-line { margin-top:2px; } .sa-sub { color:var(--muted); font-size:12px; margin-top:2px; }
    .sa-more { margin-top:4px; } .sa-more summary { cursor:pointer; color:var(--link); font-size:12px; } .sa-more ul { margin:4px 0 0; padding-left:18px; font-size:12px; }
    /* officialSeller: is the seller the brand, an authorised seller, or a third party. Information only: green or neutral, never a warning colour. */
    .os { margin:10px 0 0; padding:9px 12px; border-radius:14px; background:var(--soft); font-size:13px; line-height:1.4; }
    .os-pill { display:inline-block; padding:3px 12px; border-radius:999px; font-weight:700; font-size:14px; background:var(--card); color:var(--ink); border:1px solid var(--line); }
    .os-pill.yes { background:var(--green-bg); color:var(--green); border-color:var(--green); }
    .os-pill.no { background:var(--ink); color:var(--card); border-color:var(--ink); }
    .os-line { margin-top:6px; } .os-src { margin-top:6px; font-size:12px; color:var(--muted); } .os-src a { color:var(--link); }
    .os-more { margin-top:4px; } .os-more summary { cursor:pointer; color:var(--link); font-size:12px; } .os-more ul { margin:4px 0 0; padding-left:18px; font-size:12px; }
    .rv-flag { margin-top:6px; padding:5px 8px; border-radius:10px; background:var(--amber-bg); color:var(--amber); font-size:12px; }
    .rv-why { margin-top:4px; } .rv-why summary { cursor:pointer; color:var(--link); font-size:12px; }
    .rv-why ul { margin:4px 0 0; padding-left:18px; }
    .rv.loading .rv-stars { animation:ss-rv-pulse 1.2s ease-in-out infinite alternate; } @keyframes ss-rv-pulse { to { opacity:.4; } }
    @media (prefers-reduced-motion: reduce) { .rv.loading .rv-stars { animation:none; } }
    /* Plain answer: what to do, where we checked (plan v2.2 UX) */
    .todo { margin-top:10px; padding:12px 14px; border-radius:10px; background:var(--lime); border:0; }
    .todo strong { display:block; font-size:14px; margin-bottom:4px; }
    .todo p { margin:0 0 6px; font-size:14px; line-height:1.45; }
    .todo .btnlink { display:inline-block; margin-top:4px; font-weight:600; font-size:13px; }
    .places { margin-top:10px; padding:12px 14px; border-radius:10px; background:var(--soft); font-size:13.5px; }
    .places > strong { display:block; margin-bottom:4px; }
    .places ul { list-style:none; margin:0; padding:0; } .places li { display:flex; gap:6px; align-items:baseline; margin:5px 0; line-height:1.35; }
    .places .pm { width:1.1em; font-weight:800; flex:none; text-align:center; }
    .places li.ok .pm { color:var(--green); } .places li.warn .pm { color:var(--red); } .places li.maybe .pm { color:var(--amber); } .places li.skip .pm { color:var(--unknown); }
    .places .flag { flex:none; } .places .note { color:var(--unknown); font-size:12px; margin:6px 0 0; }
    details.more { margin-top:10px; } details.more > summary { cursor:pointer; font-weight:600; font-size:13px; color:var(--unknown); padding:6px 2px; }
    /* What was checked, by country (plan v2.2) */
    .coverage { margin-top:8px; padding:10px 14px; border-radius:10px; background:var(--soft); font-size:13px; }
    .coverage summary { cursor:pointer; font-weight:600; }
    .coverage ul { margin:6px 0; padding-left:0; list-style:none; } .coverage li { margin:3px 0; }
    .coverage .mark { display:inline-block; width:1.2em; font-weight:700; }
    .coverage .checked_live .mark, .coverage .checked_cache .mark { color:var(--red); }
    .coverage .source_unavailable .mark { color:var(--amber); }
    .coverage .no_matching_notice_found .mark { color:var(--green); }
    .coverage .not_supported .mark { color:var(--unknown); }
    .coverage .legend { color:var(--unknown); font-size:12px; margin:2px 0 8px; }
    .coverage .note { color:var(--unknown); font-size:12px; margin:2px 0 0 1.2em; }
    .coverage .sub { margin:8px 0 2px; font-weight:600; }
    .aftercare-block { margin-top:16px; padding-top:14px; border-top:1px solid var(--line); }
    .dividerlabel { margin:0 0 8px; font-size:11px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }

    /* Chat */
    .box.chat { display:flex; flex-direction:column; }
    .box.chat[hidden] { display:none; }
    .chat .card { display:flex; flex-direction:column; gap:10px; }
    .chat .headline { margin:0; font-size:20px; text-align:left; }
    .chat details.read { margin-top:0; }
    .prod { display:flex; gap:10px; align-items:center; padding:9px 11px; border-radius:10px; background:var(--soft); font-size:13px; }
    .prod img { width:40px; height:40px; object-fit:contain; border-radius:6px; background:#fff; flex:none; }
    .prod .body { min-width:0; flex:1; }
    .prod .t { font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .prod .m { color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .pill { flex:none; font-size:11px; font-weight:600; padding:2px 8px; border-radius:999px; background:var(--unknown-bg); color:var(--unknown); }
    .pill.green { background:var(--green-bg); color:var(--green); } .pill.amber { background:var(--amber-bg); color:var(--amber); } .pill.red { background:var(--red-bg); color:var(--red); }
    .log { display:flex; flex-direction:column; gap:8px; max-height:42vh; overflow:auto; }
    .log:empty { display:none; }
    .msg { padding:10px 12px; border-radius:16px; max-width:90%; font-size:14px; line-height:1.45; overflow-wrap:anywhere; }
    .msg.user { align-self:flex-end; background:var(--lime-d); color:#fff; border-bottom-right-radius:4px; }
    .msg.bot { align-self:flex-start; background:var(--soft); border-bottom-left-radius:4px; }
    .msg.err { background:var(--red-bg); }
    .txt p { margin:0 0 6px; } .txt p:last-child { margin:0; } .txt ul { margin:2px 0 6px; padding-left:18px; }
    .typing { display:inline-flex; gap:3px; margin-right:8px; vertical-align:middle; }
    .typing i { width:6px; height:6px; border-radius:50%; background:var(--muted); animation:blink 1.2s infinite both; }
    .typing i:nth-child(2) { animation-delay:.2s; } .typing i:nth-child(3) { animation-delay:.4s; }
    @keyframes blink { 0%, 80%, 100% { opacity:.25; } 40% { opacity:1; } }
    .acts { display:flex; flex-wrap:wrap; gap:2px; margin:6px 0 0 -8px; }
    details.src { margin-top:8px; font-size:13px; } details.src summary { cursor:pointer; font-weight:600; }
    .nosrc { margin-top:6px; color:var(--muted); font-size:12px; }
    .intro { display:flex; flex-direction:column; gap:8px; }
    .hello { color:var(--muted); font-size:13px; text-align:center; margin:0; }
    .chips { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; }
    .chips button { font:inherit; font-size:13px; padding:7px 13px; border:1px solid var(--line); border-radius:999px; background:#fff; color:var(--ink-2); cursor:pointer; transition:background-color .12s ease, border-color .12s ease, color .12s ease; }
    .chips button:hover { background:var(--lime); border-color:var(--lime-d); color:var(--lime-d); }
    .ask { display:flex; align-items:center; gap:4px; background:var(--soft); border-radius:10px; padding:4px; border:1.5px solid var(--line); }
    .ask:focus-within { border-color:var(--lime-d); }
    .ask input { flex:1; min-width:0; font:inherit; font-size:14px; padding:8px 10px; border:0; border-radius:12px; color:var(--ink); background:transparent; }
    .ask input:focus-visible { outline:none; }
    .ask select { font:inherit; font-size:12px; font-weight:500; padding:6px; max-width:8.5em; border:0; border-radius:6px; background:#fff; color:var(--ink); cursor:pointer; }
    .ask .send { display:grid; place-items:center; flex:none; width:36px; height:36px; padding:0; border:0; border-radius:8px; background:var(--lime-d); color:#fff; cursor:pointer; }
    .ask .send svg { width:18px; height:18px; }
    .ask .send:disabled { opacity:.45; cursor:default; }
    details.askd { margin-top:14px; padding-top:10px; border-top:1px solid var(--line); }
    details.askd summary { cursor:pointer; font-weight:700; text-align:center; }
    details.askd > div { display:flex; flex-direction:column; gap:8px; margin-top:10px; }
    .hist { display:flex; flex-direction:column; gap:8px; max-height:48vh; overflow:auto; }
    .hist[hidden], .log[hidden], .intro[hidden], .ask[hidden] { display:none; }
    .hist-item { background:var(--soft); border-radius:10px; padding:10px 12px; }
    .hist-item .when { color:var(--muted); font-size:12px; }
    .hist-item p { margin:4px 0 0; }

    /* Evidence */
    .evidence { margin-top:6px; }
    details.steps { margin-top:6px; font-size:12px; color:var(--muted); } details.steps summary { cursor:pointer; font-weight:600; }
    details.steps ol { margin:4px 0 0; padding-left:18px; } .draft dt { font-weight:700; font-size:13px; margin-top:6px; } .draft dd { margin:0 0 2px; font-size:13px; }
    .ev-h { font-weight:700; font-size:13px; color:var(--ink); }
    .ev-item { background:#fff; border:1px solid var(--line); border-left:3px solid var(--lime-d); border-radius:6px; padding:6px 10px; margin:6px 0; }
    .ev-title { font-size:12px; color:var(--muted); }
    blockquote { margin:2px 0 4px; font-size:13px; }

    ${CTX_STYLE}
    ${PANEL_STYLE}
    a { color:var(--link); font-size:13px; }
    .tools { display:flex; gap:6px; align-items:center; flex-wrap:wrap; margin-top:8px; }
    h3 { font-size:15px; margin:12px 0 2px; } ul { margin:0; padding-left:20px; } p { margin:8px 0 0; }
    .muted { color:var(--muted); font-size:13px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin-top:14px; }
    button.small { font:inherit; font-size:13px; font-weight:500; padding:7px 13px; border:1.5px solid var(--line); border-radius:4px; background:#fff; color:var(--ink-2); cursor:pointer; }
    button.small:hover { border-color:var(--lime-d); color:var(--lime-d); }
    .row button.small:first-child { background:var(--lime-d); border-color:var(--lime-d); color:#fff; }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible { outline:2px solid var(--lime-d); outline-offset:2px; }
    @media (prefers-reduced-motion: reduce) { .fab, .tab { transition:none; } .fab:active { transform:none; } .fab.just-saved svg { animation:none; } .fab .ring .seg { animation-duration:3s; } :host(.float) .box { animation:none !important; } .wait .mark, .skel, .typing i, .first li::before { animation:none; } }
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
    themed(toastHost);
    const root = toastHost.attachShadow({ mode: "open" });
    const close = () => { toastHost?.remove(); toastHost = null; };
    const action = actionLabel ? el("button", { type: "button", textContent: actionLabel, onclick: () => { onAction?.(); close(); } }) : "";
    const dismiss = el("button", { type: "button", textContent: "Dismiss", onclick: close });
    dismiss.setAttribute("aria-label", "Dismiss");
    root.append(
      el("style", { textContent: `
        ${TOKENS}
        :host { all:initial; position:fixed; left:50%; bottom:24px; transform:translateX(-50%); z-index:2147483647; }
        .t { display:flex; align-items:center; gap:12px; font:14px/1.4 var(--font); letter-spacing:-.01em; background:var(--ink); color:#fff; padding:10px 10px 10px 14px; border-radius:10px; box-shadow:0 14px 40px rgba(0,17,35,.35); max-width:min(480px,92vw); }
        .t::before { content:""; flex:none; width:22px; height:22px; background:var(--shield) center / contain no-repeat; }
        button { font:inherit; font-size:13px; font-weight:500; padding:7px 12px; border:0; border-radius:4px; background:rgba(255,255,255,.14); color:#fff; cursor:pointer; white-space:nowrap; }
        button:first-of-type { background:var(--blue); color:#fff; }
        button:focus-visible { outline:3px solid var(--lime-d); outline-offset:2px; }
      ` }),
      el("div", { className: "t", role: "status" }, el("span", { textContent: message }), action, dismiss),
    );
    document.body.append(toastHost);
    toastTimer = setTimeout(close, 6000);
  };

  // The listing's price in the shop's currency, e.g. ₹1,399 or ¥2,990.
  const money = (page) => {
    if (page.price == null) return "";
    try { return new Intl.NumberFormat(undefined, { style: "currency", currency: page.currency || "INR", maximumFractionDigits: 0 }).format(page.price); } catch (_) { return String(page.price); }
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
        el("div", { className: "m" }, page.price != null ? `${money(page)} ` : "", ...(mrp ? [el("s", { textContent: mrp })] : []), page.seller ? ` · ${page.seller}` : ""),
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
    check: { text: "about ₹1 to ₹5 (rough guess: the check uses Gemini on Vertex AI to compare listings). A product SafeShelf has never seen also gets a first look right after: about ₹3 to ₹8 more (Google Search and the recall sites).", mid: 3 },
    firstLook: { mid: 5 },
  };
  const approved = new Set(); // pages already approved: Check, Save and Ask share one cached check
  const confirmCost = (what, estimate, page) => new Promise((resolve) => {
    const host = themed(el("div"));
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
            :host { all:initial; position:fixed; inset:0; z-index:2147483647; display:flex; align-items:center; justify-content:center; background:rgba(0,17,35,.32); backdrop-filter:blur(3px); }
      .d { font:15px/1.5 var(--font); letter-spacing:-.01em; color:var(--ink); max-width:min(420px,90vw); padding:0; border-radius:14px; border-top:4px solid var(--lime-d); background:var(--card); box-shadow:var(--shadow); }
      .in { background:var(--card); border-radius:10px; padding:20px; }
      strong { display:block; text-align:center; font-size:20px; font-weight:600; letter-spacing:-.03em; }
      ${CTX_STYLE}
      p { margin:6px 0 12px; text-align:center; color:var(--muted); font-size:14px; } .r { display:flex; gap:8px; justify-content:center; margin-top:12px; }
      button { font:inherit; font-size:14px; font-weight:500; padding:9px 18px; border:1.5px solid var(--line); border-radius:4px; background:#fff; color:var(--ink); cursor:pointer; }
      button:first-child { background:var(--lime-d); border-color:var(--lime-d); color:#fff; } button:focus-visible { outline:2px solid var(--lime-d); outline-offset:2px; }
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
  // A row marker: the named line icon from panels.js, or the text itself (step numbers).
  const marker = (name) => { const icons = globalThis.SafeShelfPanels?.ICONS || {}; const n = el("span", { className: "i" }); if (icons[name]) { n.innerHTML = icons[name]; n.dataset.icon = name; } else n.textContent = name ?? ""; return n; };
  // A list of rows from a view-model (see panels.js)
  const vmDom = (v) => el("div", {},
    el("div", { className: "vh", textContent: v.title }),
    ...(v.note ? [el("div", { className: "vnote", textContent: v.note })] : []),
    ...(v.empty ? [el("div", { className: "vnote", textContent: v.empty })] : []),
    ...v.rows.map((r) => r.heading ? el("div", { className: "vh", textContent: r.heading }) : el("div", { className: "vrow" }, marker(r.icon),
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
  const evidenceBlock = (ids, heading = true) => {
    if (!ids.length) return el("div", { className: "muted", textContent: "No evidence cited." });
    const block = el("div", { className: "evidence" }, ...(heading ? [el("div", { className: "ev-h", textContent: "Evidence" })] : []));
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
    const say = (t) => pending.replaceChildren(typingDots(), el("span", { className: "muted", textContent: t }));
    agentLive({ mode: "chat", ...fields }, (e) => {
      if (e.type === "step" && e.tool !== "gemini") say(`${LIVE_WORDS[e.tool] || e.summary}…`);
      if (e.type === "step" && e.tool === "gemini" && /call/.test(e.summary)) say(`${e.summary.replace("Decided to call", "Looking up:")}…`);
      if (e.type === "verdict") say(`${e.verdict.overall === "red" ? "⛔" : e.verdict.overall === "amber" ? "⚠️" : e.verdict.overall === "green" ? "✅" : "❔"} Verdict ready, writing the answer…`);
    }, /https?:\/\//.test(fields.message || "") ? 200000 : 150000)
      .then((a) => {
        const m = [...(a.messages || [])].reverse().find((x) => x.role === "assistant") || {};
        done({ ok: true, result: { text: m.text || "I don't know. There is not enough evidence to answer that.", evidence_ids: m.evidence_ids || [], steps: a.steps || [], language: a.language } });
      })
      .catch((err) => done({ ok: false, error: err.message }));
  };
  const agentCall = (body, timeout) => new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendMessage({ type: "safeshelf:agent", body, timeout }, (res) => (res?.ok ? resolve(res.result) : reject(new Error(res?.error || chrome.runtime.lastError?.message || "no answer"))));
    } catch (_) { reject(new Error("The extension was reloaded. Please refresh the page.")); }
  });

  const level = (r) => {
    if (r.discovery?.overall) return r.discovery.overall; // the first look's colour, set by code on the server
    const both = [r.safe.level, r.real.level];
    return both.includes("red") ? "red" : both.includes("amber") ? "amber" : both.includes("unknown") ? "unknown" : "green";
  };

  const speak = (r) => {
    if (r.outcome?.plain && globalThis.SafeShelfAftercare) return SafeShelfAftercare.speakPlain(r.outcome.plain); // voice mode
    const say = (name, c) => `${name}. ${c.word}. ${c.lines.join(". ")}.`;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(`${say("Is it safe?", r.safe)} ${say("Is it real?", r.real)} ${r.summary}`));
  };

  const section = (title, c) =>
    el("div", { className: `sec ${c.level}` }, el("h3", {}, el("span", { className: "t" }, icon(VERDICT_ICON[c.level] || "help"), title), el("span", { className: "verdict", textContent: c.word })), el("ul", {}, ...c.lines.map((l) => el("li", { textContent: l }))));

  // Plan v2.2: what was checked, country by country (live, stored copy, couldn't be checked, not supported), and the
  // official records behind the answer. A country with no match is never shown as an all-clear.
  const STATE_WORDS = { checked_live: ["●", "notice found (live)"], checked_cache: ["●", "notice found (stored copy)"],
    no_matching_notice_found: ["○", "no matching notice"], source_unavailable: ["!", "couldn't be checked"], not_supported: ["–", "not checked"] };
  const coverageBlock = (o) => {
    if (!o || !o.coverage?.length) return null;
    const rows = o.coverage.slice(0, 8).map((c) => {
      const [mark, words] = STATE_WORDS[c.state] || ["–", c.state];
      const how = (c.sources || []).filter((x) => x.state !== "not_supported").map((x) => x.authority).join(", ");
      return el("li", { className: `cov ${c.state}` }, el("span", { className: "mark", ariaHidden: "true", textContent: mark }),
        el("strong", { textContent: `${c.name}${c.is_market ? " (your country)" : ""}: ` }), `${words}${how ? ` · ${how}` : ""}`,
        ...(c.notes?.length && c.is_market ? [el("div", { className: "note", textContent: c.notes[0] })] : []));
    });
    const links = (o.sources || []).filter((x) => /^https:/.test(x.url || "")).map((x) =>
      el("li", {}, el("a", { href: x.url, target: "_blank", rel: "noopener", textContent: `${x.authority} ${x.record_id}` }),
        ` ${x.local ? "(this country)" : "(another country)"}: ${(x.title || "").slice(0, 90)}`));
    const next = (o.what_would_change || []).slice(0, 2).map((w) => el("li", { textContent: `${w.fact} (${w.how})` }));
    return el("details", { className: "coverage" },
      el("summary", { textContent: `What was checked (${o.source_mode === "partial" ? "some sources couldn't be read" : o.source_mode || "live"})` }),
      el("p", { className: "legend", textContent: "● a recall notice was found there (worth reading) · ○ no matching notice · ! couldn't be checked · – not covered yet" }),
      el("ul", {}, ...rows),
      ...(links.length ? [el("p", { className: "sub", textContent: "Official records" }), el("ul", {}, ...links)] : []),
      ...(next.length ? [el("p", { className: "sub", textContent: "What would change this answer" }), el("ul", {}, ...next)] : []),
      el("p", { className: "note", textContent: "The result is set by code from these sources; no matching notice is not proof of safety." }));
  };

  // The answer in everyday words (engine/plain.py): a title, why, what to do, and where SafeShelf looked.
  const MARKS = { ok: "✓", warn: "!", maybe: "?", skip: "–" };
  const todoBox = (plain) => plain && el("div", { className: "todo" },
    el("strong", { textContent: "What you can do" }), el("p", { textContent: plain.todo }),
    ...(plain.link?.url ? [el("a", { className: "btnlink", href: plain.link.url, target: "_blank", rel: "noopener", textContent: plain.link.label })] : []));
  const placesBlock = (plain) => plain?.checked?.length ? el("div", { className: "places" },
    el("strong", { textContent: "Where we checked official recall lists" }),
    el("ul", {}, ...plain.checked.map((c) => el("li", { className: c.mark },
      el("span", { className: "pm", ariaHidden: "true", textContent: MARKS[c.mark] || "–" }),
      el("span", { className: "flag", ariaHidden: "true", textContent: c.flag }),
      el("span", {}, el("b", { textContent: `${c.name}${c.yours ? " (you)" : ""}: ` }), c.status, globalThis.SafeShelfAftercare?.badge(el, c.badge))))),
    el("p", { className: "note", textContent: plain.note })) : null;
  const detailsBox = (...nodes) => el("details", { className: "more" }, el("summary", { textContent: "Show details" }), ...nodes.filter(Boolean));

  // Side-rail icons: plain stroked paths, one family, drawn in the button's text colour.
  const ICON_PATHS = {
    check: "M12 3l7 3v5c0 5-3.2 8.2-7 10-3.8-1.8-7-5-7-10V6z M9 12l2 2 4-4",
    save: "M7 3h10a1 1 0 011 1v17l-6-4-6 4V4a1 1 0 011-1z",
    tick: "M5 12.5l4.5 4.5L19 7",
    shelf: "M4 4h16a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z M5 9v10a1 1 0 001 1h12a1 1 0 001-1V9 M10 13h4",
    ask: "M4 5h16v11H9l-5 4z",
    warn: "M12 3l9.5 17h-19z M12 10v4 M12 17h.01",
    stop: "M8 3h8l5 5v8l-5 5H8l-5-5V8z M9.5 9.5l5 5 M14.5 9.5l-5 5",
    help: "M12 21a9 9 0 100-18 9 9 0 000 18z M9.5 9.5a2.5 2.5 0 015 .5c0 1.5-2.5 2-2.5 3.5 M12 17h.01",
    close: "M6 6l12 12 M18 6L6 18",
    history: "M3 12a9 9 0 103-6.7L3 8 M3 3v5h5 M12 7v5l3 2",
    plus: "M12 5v14 M5 12h14",
    copy: "M9 9h11v11H9z M5 15H4V4h11v1",
    speaker: "M4 9v6h4l5 4V5L8 9z M16 9a4 4 0 010 6 M19 6a8 8 0 010 12",
    send: "M22 2L11 13 M22 2l-7 20-4-9-9-4z",
    search: "M11 18a7 7 0 100-14 7 7 0 000 14z M21 21l-5-5",
    refresh: "M20 11a8 8 0 10-2.3 5.7 M20 4v7h-7",
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

  const VERDICT_WORD = { red: "Don't buy", amber: "Be careful", unknown: "Can't tell yet", green: "No problems found" };
  const VERDICT_ICON = { red: "stop", amber: "warn", unknown: "help", green: "check" };

  // A small icon button. `text` shows a word next to the icon; the label is always there for screen readers and as a tooltip.
  const iconBtn = (kind, label, text) => {
    const b = el("button", { type: "button", className: "ibtn", title: label }, icon(kind), ...(text ? [text] : []));
    b.setAttribute("aria-label", label);
    return b;
  };
  // Card header: "✦ SafeShelf [badge]" on the left, small buttons (Close, History…) on the right.
  const cardHead = (badge, ...buttons) => el("div", { className: "head" }, brandRow(badge), el("div", { className: "icons" }, ...buttons));
  const typingDots = () => el("span", { className: "typing", ariaHidden: "true" }, el("i"), el("i"), el("i"));

  // Light formatting for an answer: paragraphs, "- " or "1." lists and **bold**. Built from text nodes, never as HTML.
  const rich = (text) => {
    const inline = (s) => s.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((p) => (/^\*\*.+\*\*$/.test(p) ? el("strong", { textContent: p.slice(2, -2) }) : p));
    const out = [];
    let list = null;
    for (const line of String(text || "").split("\n").map((l) => l.trim())) {
      const item = line.match(/^(?:[-•*]|\d+[.)])\s+(.*)$/);
      if (item) { if (!list) out.push(list = el("ul")); list.append(el("li", {}, ...inline(item[1]))); continue; }
      list = null;
      if (line) out.push(el("p", {}, ...inline(line)));
    }
    return el("div", { className: "txt" }, ...out);
  };

  // The product a chat is about: photo, title, price and, once checked, the verdict.
  const productStrip = (page, r) => {
    const photo = el("img", { src: (page.image_urls || [])[0] || "", alt: "" });
    photo.onerror = () => photo.remove();
    const lvl = r ? level(r) : null;
    return el("div", { className: "prod" }, ...((page.image_urls || []).length ? [photo] : []),
      el("div", { className: "body" }, el("div", { className: "t", textContent: page.title || page.url }), el("div", { className: "m", textContent: [money(page), page.seller].filter(Boolean).join(" · ") })),
      ...(lvl ? [el("span", { className: `pill ${lvl}`, textContent: VERDICT_WORD[lvl] })] : []));
  };

  // An answer's sources, folded away; their quotes are looked up the first time they are opened.
  const sourcesBlock = (ids) => {
    if (!ids.length) return el("div", { className: "nosrc", textContent: "No sources cited for this answer." });
    const d = el("details", { className: "src" }, el("summary", { textContent: `Sources (${ids.length})` }));
    d.addEventListener("toggle", () => { if (d.open && d.children.length === 1) d.append(evidenceBlock(ids, false)); });
    return d;
  };

  // Answer languages across JAPAC: [code the API takes, the name in its own script, speech locale]. Same codes as
  // LANGUAGES in engine/chat_core.py.
  const LANGS = {
    "": [["en", "English", "en-IN"]],
    "India and South Asia": [["hi", "हिन्दी", "hi-IN"], ["bn", "বাংলা", "bn-IN"], ["mr", "मराठी", "mr-IN"], ["te", "తెలుగు", "te-IN"],
      ["ta", "தமிழ்", "ta-IN"], ["gu", "ગુજરાતી", "gu-IN"], ["ur", "اردو", "ur-IN"], ["kn", "ಕನ್ನಡ", "kn-IN"], ["or", "ଓଡ଼ିଆ", "or-IN"],
      ["ml", "മലയാളം", "ml-IN"], ["pa", "ਪੰਜਾਬੀ", "pa-IN"], ["ne", "नेपाली", "ne-NP"], ["si", "සිංහල", "si-LK"]],
    "East Asia": [["ja", "日本語", "ja-JP"], ["ko", "한국어", "ko-KR"], ["zh-Hans", "简体中文", "zh-CN"], ["zh-Hant", "繁體中文", "zh-TW"]],
    "South-East Asia": [["id", "Bahasa Indonesia", "id-ID"], ["ms", "Bahasa Melayu", "ms-MY"], ["th", "ไทย", "th-TH"],
      ["vi", "Tiếng Việt", "vi-VN"], ["fil", "Filipino", "fil-PH"], ["my", "မြန်မာ", "my-MM"], ["km", "ខ្មែរ", "km-KH"], ["lo", "ລາວ", "lo-LA"]],
  };
  const LANG_LIST = Object.values(LANGS).flat();
  const speechLocale = (code) => (LANG_LIST.find(([c]) => c === code) || LANG_LIST[0])[2];
  // The shopper's last pick, else the browser's language when SafeShelf speaks it, else English.
  const startLang = async () => {
    try { const { chatLang } = await chrome.storage.local.get("chatLang"); if (LANG_LIST.some(([c]) => c === chatLang)) return chatLang; } catch (_) { /* storage unavailable */ }
    const nav = (globalThis.navigator?.language || "en").toLowerCase();
    const zh = /^zh-(tw|hk|mo|hant)/.test(nav) ? "zh-Hant" : "zh-Hans";
    return (LANG_LIST.find(([c]) => c !== "en" && (nav.startsWith("zh") ? c === zh : nav.split("-")[0] === c.split("-")[0])) || LANG_LIST[0])[0];
  };

  // A finished answer: the text, its sources, how SafeShelf answered, and Listen / Copy.
  const answerNodes = (a, lang) => {
    const listen = iconBtn("speaker", "Read this answer aloud", "Listen");
    listen.onclick = () => {
      speechSynthesis.cancel();
      const locale = speechLocale(a.language || lang);
      const base = locale.split("-")[0];
      const voice = speechSynthesis.getVoices().find((v) => v.lang.replace("_", "-").toLowerCase().split("-")[0] === base);
      // No voice for this language on this device: an English voice would read nonsense, so say so instead.
      if (!voice && base !== "en" && speechSynthesis.getVoices().length) { listen.lastChild.textContent = "No voice for this language on this device"; return; }
      const u = new SpeechSynthesisUtterance(a.text);
      u.lang = locale;
      if (voice) u.voice = voice;
      speechSynthesis.speak(u);
    };
    const copy = iconBtn("copy", "Copy this answer", "Copy");
    copy.onclick = () => navigator.clipboard?.writeText(a.text).then(() => { copy.lastChild.textContent = "Copied"; });
    return [rich(a.text), sourcesBlock(a.evidence_ids || []), stepsBlock(a.steps),
      ...(a.source === "mock" ? [el("div", { className: "muted", textContent: "Demo answer: not a real finding." })] : []),
      el("div", { className: "acts" }, listen, copy)];
  };

  // One chat thread: messages, suggestions and the question box. Used by the side chat on product pages and under the
  // result on results-page cards. getCheck() resolves to {r} (the check result to ask about) or {why} there is none.
  const chatUI = ({ suggestions, hello, placeholder, what, getCheck, context, onAsk = () => {} }) => {
    const convo = []; // this conversation so far: {role: "user" | "bot", text, evidence}
    const newSid = () => `SS-A-${Math.random().toString(36).slice(2, 10)}`;
    let sid = newSid();
    const log = el("div", { className: "log", role: "log" });
    log.setAttribute("aria-live", "polite");
    const input = el("input", { type: "text", placeholder, autocomplete: "off" });
    input.setAttribute("aria-label", "Your question");
    const option = ([code, name]) => { const o = el("option", { value: code, textContent: name }); o.lang = code; return o; };
    const lang = el("select", {}, ...Object.entries(LANGS).map(([region, list]) => (region ? el("optgroup", { label: region }, ...list.map(option)) : option(list[0]))));
    lang.setAttribute("aria-label", "Answer language");
    startLang().then((code) => { lang.value = code; });
    lang.onchange = () => { try { chrome.storage.local.set({ chatLang: lang.value }); } catch (_) { /* storage unavailable: this chat only */ } };
    const send = el("button", { type: "submit", className: "send" }, icon("send"));
    send.setAttribute("aria-label", "Send");
    const form = el("form", { className: "ask" }, input, lang, send);
    const intro = el("div", { className: "intro" }, ...(hello ? [el("p", { className: "hello", textContent: hello })] : []),
      el("div", { className: "chips" }, ...suggestions.map((q) => el("button", { type: "button", textContent: q, onclick: () => ask(q) }))));
    const add = (kind, ...kids) => {
      const m = el("div", { className: `msg ${kind}` }, ...kids);
      log.append(m);
      intro.hidden = true;
      log.scrollTop = log.scrollHeight;
      return m;
    };
    const ask = async (q) => {
      if (!q.trim() || send.disabled) return;
      onAsk();
      const mine = add("user", q);
      convo.push({ role: "user", text: q });
      input.value = "";
      send.disabled = true;
      const pending = add("bot", typingDots(), el("span", { className: "muted", textContent: "Thinking…" }));
      const done = (...kids) => { pending.replaceChildren(...kids); send.disabled = false; log.scrollTop = log.scrollHeight; };
      // A failed question is taken back, with a button to ask it again.
      const fail = (text) => {
        convo.pop();
        pending.classList.add("err");
        const again = iconBtn("refresh", "Ask this again", "Try again");
        again.onclick = () => { mine.remove(); pending.remove(); ask(q); };
        done(rich(text), el("div", { className: "acts" }, again));
      };
      if (!(await guard("chat", null, what))) { // TEMP cost guard
        convo.pop();
        return done(el("span", { className: "muted", textContent: "Cancelled. Nothing was sent and nothing was charged." }));
      }
      const { r, why } = await getCheck();
      if (!r) return fail(`I could not check this page, so I can't answer yet (${why || "no answer"}${/running|answered|Failed to fetch/i.test(why || "") ? "; the SafeShelf API may be slow or down" : ""}).`);
      askLive({ product_id: r.product_id || "unmatched", message: q, language: lang.value, session_id: sid, context: context(r),
        history: convo.slice(-7, -1).map((m) => ({ role: m.role, text: m.text })) }, pending, (res) => {
        if (!res?.ok) return fail(`Could not get an answer: ${res?.error || "no answer"}.`);
        convo.push({ role: "bot", text: res.result.text, evidence: res.result.evidence_ids });
        done(...answerNodes(res.result, lang.value));
      });
    };
    form.onsubmit = (e) => { e.preventDefault(); ask(input.value); };
    const reset = () => { convo.length = 0; sid = newSid(); log.replaceChildren(); intro.hidden = false; };
    return { log, intro, form, input, convo, reset };
  };

  const openShelf = async () => {
    try {
      const reply = await chrome.runtime.sendMessage({ type: "safeshelf:open-shelf" });
      if (!reply?.ok) throw new Error(reply?.error || "SafeShelf did not respond. Refresh this page and try again.");
    } catch (err) {
      const message = /context invalidated|receiving end does not exist|cannot read properties/i.test(err.message)
        ? "SafeShelf was reloaded. Refresh this product page, then open My Shelf again."
        : `Couldn't open My Shelf: ${err.message}`;
      toast(message);
    }
  };

  // One button + result card. Used once as a floating button (product page) and once per product card (results pages).
  // Nothing is sent to the API until the button is clicked.
  const createWidget = (getPage, mode) => {
    const host = themed(el("div", { className: mode }));
    const root = host.attachShadow({ mode: "open" });
    // Reloading the extension invalidates scripts already injected into shop tabs.
    // Block stale controls before they reach any extension API.
    const guardContext = (event) => {
      let active = false;
      try { active = Boolean(chrome.runtime.id); } catch (_) {}
      if (active) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      toast("SafeShelf was reloaded. Refresh this product page to reconnect.", "Refresh page", () => location.reload());
    };
    root.addEventListener("click", guardContext, true);
    root.addEventListener("submit", guardContext, true);
    root.addEventListener("pointerdown", guardContext, true);
    // Full wording on product pages, short wording on cards (less clutter); screen readers always get the full wording.
    const label = (btn, full, short) => {
      btn.setAttribute("aria-label", full);
      btn.dataset.short = short; // shown under the icon when chat is open as a drawer
      if (mode === "inline") { btn.textContent = short; return; }
      btn.replaceChildren(icon(btn.dataset.kind), el("span", { className: "tip", textContent: full }));
      if (btn.classList.contains("loading")) btn.append(ring());
    };
    // While a check runs, the check button's border becomes a moving ring.
    const ring = () => {
      const ns = "http://www.w3.org/2000/svg";
      const svg = document.createElementNS(ns, "svg");
      svg.setAttribute("class", "ring"); svg.setAttribute("viewBox", "0 0 56 56"); svg.setAttribute("aria-hidden", "true");
      for (const cls of ["track", "seg"]) {
        const r = document.createElementNS(ns, "rect");
        for (const [k, v] of Object.entries({ class: cls, x: "1.5", y: "1.5", width: "53", height: "53", rx: "19", pathLength: "100" })) r.setAttribute(k, v);
        svg.append(r);
      }
      return svg;
    };
    const setLoading = (on) => {
      if (mode !== "float") return;
      fab.classList.toggle("loading", on);
      fab.toggleAttribute("aria-busy", on);
      fab.querySelector(".ring")?.remove();
      if (on) fab.append(ring());
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
    // Open My Shelf: its own button, so the bookmark can add and remove. Product pages only.
    const goShelfBtn = mode === "float" ? el("button", { type: "button", className: "fab go-shelf" }) : null;
    if (goShelfBtn) { goShelfBtn.dataset.kind = "shelf"; label(goShelfBtn, "Open My Shelf", "Shelf"); goShelfBtn.onclick = openShelf; }
    // Drag handle (float rail only): move the rail along the edge, or across the middle to the other side. Arrow keys do the same.
    const grip = mode === "float" ? el("button", { type: "button", className: "grip", ariaLabel: "Move the SafeShelf buttons. Drag, or use the arrow keys." }) : null;
    if (grip) {
      placeY(host);
      const keep = (y, side) => {
        widgetY = fitY(host, y);
        placeY(host);
        try { chrome.storage.local.set({ widgetY, widgetSide: side }); } catch (_) {} // the extension was reloaded
      };
      grip.addEventListener("pointerdown", (e) => {
        if (host.classList.contains("drawer-open")) return;
        e.preventDefault();
        try { grip.setPointerCapture(e.pointerId); } catch (_) {} // keeps the drag going if the pointer leaves the handle
        host.classList.add("dragging");
        const move = (ev) => {
          placeY(host, fitY(host, (ev.clientY / innerHeight) * 100));
          host.dataset.side = ev.clientX < innerWidth / 2 ? "left" : "right"; // crossing the middle flips it as you drag
        };
        const drop = (ev) => {
          grip.removeEventListener("pointermove", move);
          grip.removeEventListener("pointerup", drop);
          grip.removeEventListener("pointercancel", drop);
          host.classList.remove("dragging");
          keep((ev.clientY / innerHeight) * 100, host.dataset.side);
        };
        grip.addEventListener("pointermove", move);
        grip.addEventListener("pointerup", drop);
        grip.addEventListener("pointercancel", drop);
      });
      grip.addEventListener("keydown", (e) => {
        const side = { ArrowLeft: "left", ArrowRight: "right" }[e.key] || host.dataset.side;
        const step = { ArrowUp: -4, ArrowDown: 4 }[e.key] || 0;
        if (!step && side === host.dataset.side) return;
        e.preventDefault();
        host.dataset.side = side;
        keep(widgetY + step, side);
      });
    }
    const bar = el("div", { className: "bar" }, ...(grip ? [grip] : []), ...(chatBtn ? [chatBtn] : []), shelfBtn, ...(goShelfBtn ? [goShelfBtn] : []), fab); // separate buttons: chat, save, my shelf, check
    const box = el("section", { className: "box", hidden: true, ariaLabel: "SafeShelf safety check" });
    box.setAttribute("aria-live", "polite");
    const show = (...nodes) => box.replaceChildren(el("div", { className: "card" }, ...nodes)); // everything in the box sits on one white card
    let stopTicker = () => {}; // stops the "Checking this product… 12 s" counter
    // On results pages the popup lives in its own layer on <body>, so no card's CSS can clip, move or cover it.
    const pop = mode === "inline" ? el("div", { className: "pop" }) : null;
    if (pop) {
      themed(pop).attachShadow({ mode: "open" }).append(el("style", { textContent: STYLE + (globalThis.SafeShelfAftercare?.STYLE || "") }), box);
      root.append(el("style", { textContent: STYLE + (globalThis.SafeShelfAftercare?.STYLE || "") }), bar);
    } else {
      root.append(el("style", { textContent: STYLE + (globalThis.SafeShelfAftercare?.STYLE || "") }), box, ...(chatBox ? [chatBox] : []), bar);
    }
    let checked = false;
    let result = null;
    let saved = false;
    let savedTimer = 0;
    // Saved: a tick for one second, then the bookmark stays filled. On result cards (text buttons) only the wording changes.
    const showSaved = (title, flash) => {
      saved = true;
      clearTimeout(savedTimer);
      shelfBtn.disabled = false;
      shelfBtn.title = title;
      const settle = () => { shelfBtn.dataset.kind = "save"; shelfBtn.classList.remove("just-saved"); shelfBtn.classList.add("saved"); label(shelfBtn, "Saved. Click to remove from My Shelf", "Saved"); };
      if (!flash) return settle();
      shelfBtn.dataset.kind = "tick";
      shelfBtn.classList.add("just-saved");
      label(shelfBtn, "Saved", "Saved");
      savedTimer = setTimeout(settle, 1000);
    };
    // A product already on My Shelf opens with the bookmark filled.
    const markIfSaved = async () => {
      if (mode !== "float") return;
      try { const { shelf = [] } = await chrome.storage.local.get("shelf"); if (!saved && shelf.some((i) => i.url === cleanUrl())) showSaved("On My Shelf. Click to remove it.", false); } catch (_) {}
    };
    markIfSaved();
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
    // Settings > Theme > Panels open in: as a drawer, an open check card or chat reshapes the widget and docks it at the window edge.
    const syncDrawer = () => {
      if (mode !== "float") return;
      const open = !box.hidden || (chatBox ? !chatBox.hidden : false);
      host.classList.toggle("drawer-open", open);
      if (open && look.widgetChat === "drawer") dock(look.widgetSide, Math.round(host.getBoundingClientRect().width)); // reading the size lays the drawer out first
      else dock();
    };
    const setOpen = (open) => {
      box.hidden = !open;
      fab.setAttribute("aria-expanded", String(open));
      syncDrawer();
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
        ...(r.discovery ? { first_look: r.discovery } : {}), // what the first look found online and on the recall sites
        listing_text: (p.page_text || "").slice(0, 1500) };
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

    const closeX = () => {
      const b = iconBtn("close", "Close");
      b.onclick = () => { setOpen(false); fab.focus(); };
      return b;
    };

    // Results-page cards have no side chat, so their chat sits folded under the result.
    const inlineChat = (r) => {
      const chat = chatUI({ suggestions: ["Why this result?", "Is it safe to buy?", "Show me a safer one", "What should I check before buying?"], placeholder: "Ask about this result…",
        what: "Ask about this result (your question, this result and the last few messages are sent)", getCheck: async () => ({ r }), context: chatContext });
      return el("details", { className: "askd" }, el("summary", { textContent: "Ask about this result" }), el("div", {}, chat.log, chat.intro, chat.form));
    };

    // The verdict at the top of the card. `note` says when a first look changed it.
    let heroEl = null;
    const hero = (lvl, summary, note, title) => el("div", { className: `hero ${lvl}` }, el("div", { className: "ic" }, icon(VERDICT_ICON[lvl])),
      el("h2", { className: `headline ${lvl}`, textContent: title || VERDICT_WORD[lvl] }), ...(summary ? [el("p", { className: "sum", textContent: summary })] : []),
      ...(note ? [el("span", { className: "upd", textContent: note })] : []));
    // The plain answer leads, unless the seller check is the bigger worry (then that leads, in its own words).
    const plainHero = (r, lvl, note) => {
      const plain = r.outcome?.plain;
      const rank = { red: 3, amber: 2, unknown: 1, green: 0 };
      if (!plain || rank[r.real.level] > rank[r.safe.level] && ["red", "amber"].includes(r.real.level)) return hero(lvl, r.summary, note);
      return hero(lvl, plain.why, note, plain.title);
    };

    // First look: a product SafeShelf has never seen is looked up right away (agent mode "discover"): up to 60
    // critical reviews, recall notices, the market's official recall sites, and the genuine product found online.
    // Each lookup ticks off as it finishes; if the colour changes, the card says so. The server saves the lookup by
    // model number, so the next shopper on this model gets it at once.
    let discoveryRun = 0; // a newer check or another product makes an older first look's answer stale
    const FIRST_LOOK = [["reviews", "Reading what buyers say"], ["real", "Checking the seller and price"],
      ["reference", "Finding the genuine product online"], ["sites", "Searching government recall lists"]];
    const firstLook = (r, fresh) => {
      const run = ++discoveryRun;
      const before = level(r);
      const items = Object.fromEntries(FIRST_LOOK.map(([k, t]) => [k, el("li", {}, el("span", { textContent: `${t}…` }))]));
      const tag = el("span", { className: "tag", textContent: "Working" });
      const lede = el("p", { className: "lede", textContent: "First time we've seen this product, so we're looking it up now. It takes about a minute – you can keep browsing." });
      const found = el("div");
      const section = el("div", { className: "first" }, el("h3", {}, "Taking a closer look", tag), lede, el("ol", {}, ...Object.values(items)), found);
      section.setAttribute("aria-live", "polite");
      const tick = (k, text, cls = "done") => { items[k].className = cls; items[k].replaceChildren(el("span", { textContent: text })); };
      // retrying: after a dropped connection or "Try again". Never forced fresh, so whatever the server already found
      // and saved for this model is reused instead of being paid for twice.
      const go = async (retrying) => {
        if (!retrying) try { const { spend = { total: 0, calls: 0 } } = await chrome.storage.local.get("spend"); await chrome.storage.local.set({ spend: { total: spend.total + COST.firstLook.mid, calls: spend.calls + 1 } }); } catch (_) { /* TEMP cost guard tally */ }
        const { product_id, listing_id, ...listing } = await withMoreReviews(getPage(), 3, 60);
        const n = (listing.reviews || []).length;
        try {
          const v = await agentLive({ mode: "discover", product_id: "unmatched", listing, fresh: fresh && !retrying }, (e) => {
            if (run !== discoveryRun || e.type !== "step" && e.type !== "start") return;
            if (e.type === "step" && e.agent === "safety_radar") {
              const read = Number(e.summary.match(/from (\d+) reviews?/)?.[1] ?? n); // the server also keeps reviews from earlier visits
              tick("reviews", `Read ${read} buyer review${read === 1 ? "" : "s"} and the recall notices SafeShelf holds`);
            }
            if (e.type === "step" && e.agent === "is_it_real") tick("real", e.summary.replace(/^Is it real\? /, "Shop and price: "));
            if (e.type === "step" && e.agent === "reference") tick("reference", e.summary);
            if (e.type === "start" && e.tool === "recall_sites") items.sites.firstChild.textContent = "Searching official recall sites (up to a minute)…";
            if (e.type === "step" && e.agent === "research_agent" && e.tool === "recall_sites") {
              const WORDS = { not_found: "no notice", found: "searched", blocked: "blocked the check", captcha: "asked for a captcha", error: "could not be searched" };
              tick("sites", e.summary.replace(/^Research Agent: /, "Recall sites: ").replace(/\b(not_found|found|blocked|captcha|error)\b/g, (w) => WORDS[w]));
            }
            if (e.type === "step" && e.agent === "discovery" && e.tool === "saved") {
              tick("reference", e.summary);
              if (/recall-site search/.test(e.summary)) tick("sites", "Recall sites: reused that search");
            }
          }, 280000);
          if (run !== discoveryRun) return;
          for (const [k, t] of FIRST_LOOK) if (items[k].className !== "done") tick(k, `${t}: not available this time`, "skip");
          const verdict = v.verdict || {};
          const lvl = ["red", "amber", "green", "unknown"].includes(verdict.overall) ? verdict.overall : "unknown";
          r.discovery = { overall: lvl, safe: verdict.safe, real: verdict.real, reasons: (verdict.reasons || []).map((x) => x.text),
            evidence_ids: verdict.evidence_ids || [], reference: v.reference || null, from_saved: !!v.discovery?.from_saved };
          tag.textContent = "Done";
          lede.textContent = v.discovery?.from_saved
            ? `This model was looked up ${v.discovery.saved_minutes_ago < 90 ? `${v.discovery.saved_minutes_ago} minutes` : `${Math.round(v.discovery.saved_minutes_ago / 60)} hours`} ago, so that lookup was reused with this page's own checks. What SafeShelf found:`
            : "What SafeShelf found:";
          const fp = verdict.plain;
          const technical = el("ul", { className: "found" }, ...(verdict.reasons || []).map((x) => el("li", { textContent: x.text })));
          found.replaceChildren(...(fp ? [todoBox(fp), placesBlock(fp), detailsBox(technical, sourcesBlock(verdict.evidence_ids || []))]
            : [technical, sourcesBlock(verdict.evidence_ids || [])]));
          const word = VERDICT_WORD[lvl];
          fab.className = `fab ${lvl}`;
          label(fab, `SafeShelf: ${word}`, word);
          box.className = `box ${lvl}`;
          const changed = lvl !== before;
          if (globalThis.SafeShelfAftercare) SafeShelfAftercare.guardBuy({ ...r, outcome: { ...(r.outcome || {}), plain: fp || r.outcome?.plain } }, lvl); // the first look's colour guards the buy button
          const summary = !changed ? r.summary : ["red", "amber"].includes(lvl) ? "The first look found warning signs: see First look below." : "The first look found no warning signs in what it checked.";
          const updated = fp ? hero(lvl, fp.why, changed ? `Updated after a closer look (was: ${VERDICT_WORD[before]})` : null, fp.title)
            : hero(lvl, summary, changed ? `Updated after the first look (was ${VERDICT_WORD[before]})` : null);
          heroEl?.replaceWith(updated);
          heroEl = updated;
          if (box.hidden) toast(`SafeShelf finished its first look at this product: ${word}.`, "Show", () => setOpen(true));
          place();
        } catch (err) {
          if (run !== discoveryRun) return;
          if (!retrying && /closed|disconnect/i.test(err.message)) { // the connection dropped: pick up once, by itself
            lede.textContent = "The connection dropped; picking up where SafeShelf left off…";
            return go(true);
          }
          for (const [k, t] of FIRST_LOOK) if (items[k].className !== "done") tick(k, `${t}: stopped`, "skip");
          tag.textContent = "Stopped";
          lede.textContent = `The first look could not finish (${err.message}). The result above is from this page only.`;
          const again = el("button", { type: "button", className: "small", textContent: "Try again" });
          again.onclick = () => {
            tag.textContent = "Working";
            lede.textContent = "Trying again; anything already found is reused…";
            found.replaceChildren();
            for (const [k, t] of FIRST_LOOK) if (items[k].className !== "done") { items[k].className = ""; items[k].replaceChildren(el("span", { textContent: `${t}…` })); }
            go(true);
          };
          found.replaceChildren(el("div", { className: "tools" }, again));
        }
      };
      go(false);
      return section;
    };

    // "Is it any good?": a small widget under the verdict. It fills in once the extra reviews are read, after the card is
    // shown, so the check itself is no slower. About quality only: it never changes the verdict above it.
    const reviewsWidget = () => {
      const top = (word, stars, note) => el("div", {}, el("div", { className: "rv-top" }, el("span", { className: "rv-word", textContent: word }),
        el("span", { className: "rv-stars", textContent: stars })), ...(note ? [el("span", { className: "rv-note", textContent: note })] : []));
      const w = el("div", { className: "rv loading", role: "group", ariaLabel: "What buyers say" }, top("What buyers say", "Reading reviews…"));
      const fill = (vm) => {
        const rows = [];
        if (vm.liked.length) rows.push(el("div", { className: "rv-row up" }, icon("check"), el("span", { textContent: vm.liked.join(" · ") })));
        // A complaint opens to the reviews counted for it (they come in the API answer itself). Review text is set as text only.
        const row = (c) => {
          const head = el("summary", { className: "rv-row down" }, icon("warn"), el("span", {}, el("span", { textContent: c.text }), el("span", { className: "rv-sub", textContent: ` · ${c.sub}` })));
          const counted = c.reviews.map((r) => el("li", {}, el("div", { className: "rv-meta", textContent: [r.stars, r.date].filter(Boolean).join(" · ") }),
            ...(r.title ? [el("strong", { textContent: r.title })] : []), el("div", { textContent: r.text })));
          const d = el("details", { className: "rv-c" }, head, counted.length ? el("ul", { className: "rv-revs" }, ...counted) : el("div", { className: "rv-note", textContent: "These reviews are not in this answer." }));
          d.addEventListener("toggle", place);
          return d;
        };
        rows.push(...vm.complaints.map(row)); // every complaint (at most ten), none hidden
        if (vm.warning) rows.push(el("div", { className: "rv-flag", textContent: vm.warning }));
        const why = el("details", { className: "rv-why" }, el("summary", { textContent: "Why this verdict" }), el("ul", {}, ...vm.reasons.map((t) => el("li", { textContent: t }))));
        why.addEventListener("toggle", place);
        w.className = `rv ${vm.tone}`;
        w.replaceChildren(top(vm.word, vm.stars, vm.note), ...rows, why);
        place();
      };
      const failed = (why) => { w.className = "rv"; w.replaceChildren(top("What buyers say", "Not available"), el("span", { className: "rv-note", textContent: why })); place(); };
      (async () => {
        try {
          if (!(await guard("check", getPage().url, "Check this product", getPage()))) return w.remove(); // TEMP cost guard: approved with the check
          const listing = await reviewsForVerdict(getPage());
          chrome.runtime.sendMessage({ type: "safeshelf:reviews", listing }, (res) => {
            if (!res?.ok) return failed(`Couldn't read the reviews this time (${res?.error || chrome.runtime.lastError?.message || "no answer"}).`);
            if (!res.result) return w.remove();
            fill(res.result);
          });
        } catch (_) { w.remove(); } // the extension was reloaded; the new script takes over
      })();
      return w;
    };

    // "Is it possible?": the technology first (can what the listing claims exist at all?). Only if it can, the price: is
    // this product possible at this price? Technology that cannot exist stops it there: the price is never looked up.
    // Price and physics only: it never changes the verdict above it.
    const possibleWidget = () => {
      const w = el("div", { className: "ip loading", role: "group", ariaLabel: "Is it possible?" },
        el("div", { className: "ip-q", textContent: "Is it possible?" }), el("div", { className: "ip-line", textContent: "Checking the technology…" }));
      const state = { claims: null, price: null, answer: null, demo: false, stage: "tech", priceError: null };
      const link = (u, t) => el("a", { href: u, target: "_blank", rel: "noopener", textContent: t });
      const claimLine = (x) => el("div", { className: `ip-claim ${x.mark}` }, icon(x.mark), el("span", {}, el("span", { textContent: x.text }), el("div", { className: "ip-why", textContent: x.why })));
      const chart = (p) => el("div", { className: `ip-sec ${p.tone}` },
        ...(p.chart ? [el("div", { className: "ip-chart", role: "img", ariaLabel: p.chart.label },
          el("div", { className: "ip-band", style: `left:${p.chart.band[0]}%;width:${Math.max(1, p.chart.band[1] - p.chart.band[0])}%` }),
          el("div", { className: "ip-median", style: `left:${p.chart.median}%` }),
          ...(p.chart.dot != null ? [el("div", { className: "ip-dot", style: `left:${p.chart.dot}%` })] : []))] : []),
        el("div", { className: "ip-line", textContent: p.line }));
      const draw = () => {
        const a = state.answer;
        const claims = state.claims?.claims || [];
        const problems = claims.filter((x) => x.result === "not_possible" || x.result === "doubtful");
        // Nothing wrong found and no price answer (the kind of product is not covered yet): one slim line, so it is
        // clear the check ran. No "can't tell" headline, no bare price, no "?" rows.
        if (state.stage === "done" && !problems.length && (!a || a.verdict === "cant_tell")) {
          const said = state.claims ? "Nothing impossible found in the technology the listing claims." : "The technology could not be checked this time.";
          const price = state.price || !state.claims ? "" : " The price check does not cover this kind of product yet.";
          w.className = "ip";
          w.replaceChildren(el("div", { className: "ip-q", textContent: "Is it possible?" }), el("div", { className: "ip-line", textContent: said + price }));
          return place();
        }
        const fine = claims.filter((x) => !problems.includes(x));
        const stopped = state.claims?.verdict === "not_possible"; // the technology cannot exist: no price was looked up
        const kids = [];
        if (state.demo) kids.push(el("span", { className: "ip-demo", textContent: "Demo data: example answer from the local API" }));
        const head = el("div", { className: `ip-sec ${a?.tone || "none"}` },
          el("div", { className: "ip-q", textContent: a?.question ? `Is ${a.question} possible?` : "Is it possible?" }));
        if (state.stage === "tech") head.append(el("div", { className: "ip-line", textContent: "Checking the technology…" }));
        else if (a) head.append(el("div", { className: "ip-top" }, el("span", { className: "ip-word", textContent: a.word })), el("div", { className: "ip-line", textContent: a.text }));
        else head.append(el("div", { className: "ip-line", textContent: state.stage === "price" ? "Checking the price…" : "Nothing to judge on this page." }));
        kids.push(head);
        if (state.stage === "price" && a) kids.push(el("div", { className: "ip-line ip-wait", textContent: "Checking the price…" }));
        // The technology result, then the price chart (never for technology that cannot exist)
        if (state.claims) {
          if (problems.length) kids.push(el("div", { className: "ip-sec warn" }, el("div", { className: "ip-h", textContent: "Technology" }), ...problems.map(claimLine)));
          else if (!stopped) kids.push(el("div", { className: "ip-sec ok" }, el("div", { className: "ip-h", textContent: "Technology" }),
            fine.length ? claimLine(fine[0]) : el("div", { className: "ip-line", textContent: "Nothing impossible found in what the listing claims." })));
        }
        if (stopped) kids.push(el("div", { className: "ip-line ip-wait", textContent: "The price was not checked: this technology cannot exist." }));
        else if (state.price?.chart) kids.push(el("div", { className: "ip-h", textContent: "Price" }), chart(state.price));
        else if (state.priceError) kids.push(el("div", { className: "ip-line ip-wait", textContent: `The price could not be checked this time (${state.priceError}).` }));
        const reasons = [...(state.price?.reasons || []), ...(state.claims?.reasons || [])];
        const inside = [];
        if (state.price?.comparables.length) inside.push(el("div", { className: "ip-h", textContent: "Genuine prices compared" }), el("ul", { className: "ip-cmp" },
          ...state.price.comparables.map((c) => el("li", {}, c.text, ...(c.url ? [" · ", link(c.url, c.source || "source")] : [])))));
        if (problems.length && fine.length) inside.push(el("div", { className: "ip-h", textContent: "Other claims checked" }), ...fine.map(claimLine));
        if (state.claims?.sources.length) inside.push(el("div", { className: "ip-why" }, "Sources: ", ...state.claims.sources.flatMap((src, i) => [...(i ? [" · "] : []), link(src.url, src.title)])));
        if (reasons.length) inside.push(el("div", { className: "ip-h", textContent: "How this was decided" }), el("ul", {}, ...reasons.map((t) => el("li", { textContent: t }))));
        if (inside.length && state.stage === "done") {
          const more = el("details", { className: "ip-more" }, el("summary", { textContent: "Why this verdict" }), ...inside);
          more.addEventListener("toggle", place);
          kids.push(more);
        }
        w.className = state.stage === "done" ? "ip" : "ip loading";
        w.replaceChildren(...kids);
        place();
      };
      const ask = (msg) => new Promise((resolve) => { try { chrome.runtime.sendMessage(msg, (res) => resolve(res)); } catch (_) { resolve(null); } });
      (async () => {
        try {
          if (!(await guard("check", getPage().url, "Check this product", getPage()))) return w.remove(); // TEMP cost guard: approved with the check
          const { url, title, price, currency, seller, page_text } = getPage();
          const listing = { url, title, price, currency, seller, page_text };
          const t = await ask({ type: "safeshelf:tech", listing }); // 1. the technology
          if (t?.ok && t.result) { state.claims = t.result.claims; state.answer = t.result.answer; state.demo ||= t.result.demo; }
          if (state.claims?.verdict === "not_possible") { state.stage = "done"; return draw(); } // cannot exist: forget the price
          state.stage = "price"; draw();
          const p = await ask({ type: "safeshelf:price", listing, claims: state.claims }); // 2. the price, for technology that can exist
          if (p?.ok && p.result) { state.price = p.result.price; state.answer = p.result.answer; state.demo ||= p.result.demo; }
          else state.priceError = p?.error || chrome.runtime.lastError?.message || "no answer";
          if (!state.claims && !state.price) { state.stage = "done"; w.className = "ip"; w.replaceChildren(el("div", { className: "ip-q", textContent: "Is it possible?" }), el("div", { className: "ip-line", textContent: `Not available this time (${state.priceError}).` })); return place(); }
          state.stage = "done"; draw();
        } catch (_) { w.remove(); } // the extension was reloaded; the new script takes over
      })();
      return w;
    };

    // sellerAge: how long has this product been listed? From the page's "Date First Available". The LISTING's age, not the
    // seller's (marketplaces do not publish a join date), and the box says so. Nothing is shown when the page has no date.
    const sellerAgeWidget = () => {
      const w = el("div", { className: "sa", role: "group", ariaLabel: "How long this product has been listed" });
      const fill = (vm) => {
        const more = el("details", { className: "sa-more" }, el("summary", { textContent: "Why this verdict" }), el("ul", {}, ...vm.reasons.map((t) => el("li", { textContent: t }))));
        more.addEventListener("toggle", place);
        w.className = `sa ${vm.tone}`;
        w.replaceChildren(...(vm.demo ? [el("span", { className: "ip-demo", textContent: "Demo data: example answer from the local API" })] : []),
          el("div", { className: "sa-top" }, el("span", { className: "sa-word", textContent: vm.word }), ...(vm.band ? [el("span", { className: "sa-band", textContent: vm.band })] : [])),
          el("div", { className: "sa-line", textContent: vm.text }), el("div", { className: "sa-sub", textContent: [vm.listed, vm.note].filter(Boolean).join(" · ") }),
          ...(vm.brand ? [el("div", { className: "sa-brand", textContent: vm.brand })] : []), more);
        place();
      };
      const note = (t) => { w.className = "sa"; w.replaceChildren(el("div", { className: "sa-sub", textContent: t })); place(); };
      (async () => {
        try {
          const { url, page_text } = getPage();
          const first = readFirstAvailable();
          // No date on the page: its reviews are the next evidence (the oldest one; or "no reviews" when all were read)
          const cov = first ? null : await reviewCoverage();
          const listing = { url, first_available: first, page_text, oldest_review: cov?.oldest || undefined, reviews_read: cov?.read,
            reviews_complete: cov?.complete, ratings_total: cov?.ratings ?? undefined, brand_text: readBrandText() };
          chrome.runtime.sendMessage({ type: "safeshelf:listing-age", listing }, (res) => {
            if (!res?.ok) return note(`Listing age: couldn't be worked out (${res?.error || chrome.runtime.lastError?.message || "no answer"}).`);
            if (!res.result) return note("Listing age: this page does not show when the product was first listed, and its reviews cannot date it.");
            fill(res.result);
          });
        } catch (_) { w.remove(); } // the extension was reloaded; the new script takes over
      })();
      return w;
    };

    // officialSeller: who is selling it, against the lists brands themselves published. It shows nothing for a brand that
    // published nothing usable. Never a score and never a warning colour: a third-party seller can be genuine.
    const officialSellerWidget = () => {
      const w = el("div", { className: "os", role: "group", ariaLabel: "Who is selling this" });
      const fill = (vm) => {
        if (vm.quiet) { w.className = "os"; w.replaceChildren(...(vm.demo ? [el("span", { className: "ip-demo", textContent: "Demo data: example answer from the local API" })] : []), el("div", { className: "os-src", textContent: vm.text })); return place(); }
        const src = vm.source ? el("div", { className: "os-src" }, "Source: ", ...(vm.source.url ? [el("a", { href: vm.source.url, target: "_blank", rel: "noopener", textContent: vm.source.text })] : [vm.source.text]), ...(vm.source.when ? [` · ${vm.source.when}`] : [])) : null;
        // The source sits under "How this was decided", with the reasons: the answer itself stays short
        const more = el("details", { className: "os-more" }, el("summary", { textContent: "How this was decided" }), ...(src ? [src] : []), el("ul", {}, ...vm.reasons.map((t) => el("li", { textContent: t }))));
        more.addEventListener("toggle", place);
        w.className = `os ${vm.tone}`;
        w.replaceChildren(...(vm.demo ? [el("span", { className: "ip-demo", textContent: "Demo data: example answer from the local API" })] : []),
          el("div", {}, el("span", { className: `os-pill ${vm.official === true ? "yes" : vm.official === false ? "no" : "maybe"}`, textContent: vm.word })),
          el("div", { className: "os-line", textContent: vm.text }), more);
        place();
      };
      (async () => {
        try {
          const { url, title, seller } = getPage();
          // Amazon's own "Visit the Portronics Store" link under the title: only a brand's owner can open a brand store
          const brand_store = tidy(document.querySelector("#bylineInfo")?.textContent).match(/Visit the (.{1,60}?) Store/i)?.[1];
          chrome.runtime.sendMessage({ type: "safeshelf:official-seller", listing: { url, title, seller, ...(brand_store ? { brand_store } : {}) } }, (res) => {
            if (!res?.ok) return w.remove(); // no answer (the API could not be reached): nothing to say
            if (!res.result) return w.remove();
            fill(res.result);
          });
        } catch (_) { w.remove(); } // the extension was reloaded; the new script takes over
      })();
      return w;
    };

    const render = (r, fresh = false) => {
      stopTicker();
      result = r;
      const lvl = level(r);
      const word = VERDICT_WORD[lvl];
      fab.className = `fab ${lvl}`;
      label(fab, `SafeShelf: ${word}`, word);
      box.className = `box ${lvl}`;
      const speakBtn = el("button", { type: "button", className: "small", textContent: "Read aloud" });
      speakBtn.onclick = () => speak(r);
      const againBtn = el("button", { type: "button", className: "small", textContent: "Check again" });
      againBtn.onclick = () => run(true);
      // Investigate (the Shopper Agent, investigate.js): only on a product page, never for a card on a results page.
      const investigateBtn = mode === "float" && window.__safeshelfInvestigate
        ? el("button", { type: "button", className: "small", textContent: "Investigate the page", title: "Let SafeShelf look through the photos, label, reviews and seller (read-only)" })
        : null;
      if (investigateBtn) investigateBtn.onclick = async () => { setOpen(false); window.__safeshelfInvestigate(await withMoreReviews(getPage())); };
      const askBtn = chatBtn ? el("button", { type: "button", className: "primary" }, icon("ask"), "Ask a question about it") : null;
      if (askBtn) askBtn.onclick = () => setChatOpen(true);
      // Only on a product page, for a product SafeShelf has no exact match for, and never for example data.
      const deeper = mode === "float" && !r.product_id && r.source !== "mock" ? firstLook(r, fresh) : null;
      heroEl = plainHero(r, lvl);
      const plain = r.outcome?.plain;
      show(
        ...(r.source === "mock" ? [el("div", { className: "demo", textContent: "Demo data: these are example results, not real findings about this product." })] : []),
        cardHead(r.host, closeX()),
        heroEl,
        ...(mode === "float" && r.source !== "mock" ? [reviewsWidget(), possibleWidget(), sellerAgeWidget(), officialSellerWidget()] : []), // product pages only, never for example data
        panelTabs(r, [
          ...(plain ? [todoBox(plain)] : []),
          // Before purchase the buy button is guarded (below); after purchase: steps, refund and complaint drafts.
          ...(deeper ? [deeper] : []),
          ...(plain ? [placesBlock(plain)] : [section("Is it safe?", r.safe)]),
          section("Is the seller genuine?", r.real),
          // After the two answers, in its own labelled block, so "I already bought it" never reads as part of the pre-purchase verdict.
          ...(globalThis.SafeShelfAftercare && r.source !== "mock" && mode === "float"
            ? [el("div", { className: "aftercare-block" }, el("p", { className: "dividerlabel" }, "Already bought it?"), SafeShelfAftercare.afterPanel(el, r, getPage()))]
            : []),
          detailsBox(...(plain ? [section("Safety check, in detail", r.safe)] : []), coverageBlock(r.outcome),
            el("details", { className: "read" }, el("summary", { textContent: "What SafeShelf read from this page" }), contextCard(getPage()))),
          el("p", { className: "foot", textContent: `${r.label} · v${chrome.runtime.getManifest().version}` }),
          ...(mode === "inline" ? [inlineChat(r)] : []),
        ]),
        el("div", { className: "actions" }, ...(askBtn ? [askBtn] : []), el("div", { className: "more" }, ...[investigateBtn, speakBtn, againBtn].filter(Boolean)),
          ...(globalThis.SafeShelfAftercare && r.outcome?.plain ? [SafeShelfAftercare.voiceToggle(el)] : [])),
      );
      place();
      if (mode === "float" && r.source !== "mock" && globalThis.SafeShelfAftercare) { SafeShelfAftercare.guardBuy(r, lvl); SafeShelfAftercare.autoSpeak(r); }
    };

    // While the check runs: what it covers and how long it has taken so far.
    const waiting = () => {
      stopTicker();
      const STAGES = ["Reading the listing", "Looking for recalls and danger reports", "Checking the safety marks", "Comparing it with the genuine product",
        "Still working: a product SafeShelf has never seen can take up to half a minute"];
      const stage = el("div", { className: "stage", textContent: `${STAGES[0]}…` });
      const started = Date.now();
      const t = setInterval(() => {
        const s = Math.round((Date.now() - started) / 1000);
        stage.textContent = `${STAGES[Math.min(Math.floor(s / 3), STAGES.length - 1)]}… ${s} s`;
      }, 1000);
      setLoading(true);
      stopTicker = () => { clearInterval(t); setLoading(false); };
      return el("div", { className: "wait" }, el("span", { className: "mark", ariaHidden: "true", textContent: "✦" }), el("strong", { textContent: "Checking this product" }), stage,
        ...[92, 74, 84].map((w) => el("div", { className: "skel", style: `width:${w}%` })));
    };

    const run = async (fresh = false) => {
      if (!(await guard("check", getPage().url, "Check this product", getPage()))) { // TEMP cost guard
        checked = false;
        box.className = "box";
        const go = el("button", { type: "button", className: "primary", textContent: "Check now" });
        go.onclick = () => run();
        show(cardHead("Check", closeX()), el("div", { className: "state" }, el("p", { textContent: "Check cancelled. Nothing was sent and nothing was charged." }), go));
        return;
      }
      checked = true;
      box.className = "box";
      show(cardHead("Check", closeX()), waiting());
      place();
      try {
        const page = mode === "float" ? await withMoreReviews(getPage()) : getPage();
        chrome.runtime.sendMessage({ type: "safeshelf:check", page, fresh }, (res) => {
          if (res?.ok) return render(res.result, fresh);
          stopTicker();
          checked = false; // opening the card again tries again
          if (res?.signin) { // nothing works without a sign-in (session.js)
            const signIn = el("button", { type: "button", className: "primary" }, "Sign in with Google");
            signIn.onclick = () => chrome.runtime.sendMessage({ type: "safeshelf:signin" });
            return show(cardHead("Check", closeX()), el("div", { className: "state" }, el("strong", { textContent: "Sign in to check this page" }),
              el("p", { textContent: "SafeShelf checks products for signed-in people. Sign in, then press Check again." }), signIn));
          }
          const retry = el("button", { type: "button", className: "primary" }, icon("refresh"), "Try again");
          retry.onclick = () => run(true);
          show(cardHead("Check", closeX()), el("div", { className: "state" }, el("strong", { textContent: "SafeShelf couldn't check this page" }),
            el("p", { textContent: `${res?.error || chrome.runtime.lastError?.message || "No answer"}. The API may be busy or starting up; trying again usually works.` }), retry));
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
        const meta = { title: page.title, url: page.url, image_url: (page.image_urls || [])[0] || null, host: r?.host || location.hostname, level: r ? level(r) : null };
        chrome.runtime.sendMessage({ type: "safeshelf:save", product_id: pid, meta }, (res) => {
          if (res?.ok) {
            const item = res.result;
            saved = true;
            const note = item.synced ? "Saved to your SafeShelf account. We'll re-check recalls daily."
              : item.api_error ? `The API did not accept it (${item.api_error}), so it is saved on this browser only.`
              : "Saved on this browser.";
            toast(note, "View shelf", openShelf);
            showSaved(`${note} Click again to remove it.`, true);
          } else {
            label(shelfBtn, "Could not save. Retry", "Retry");
            shelfBtn.title = res?.error || chrome.runtime.lastError?.message || "";
            toast(`Could not save to My Shelf: ${shelfBtn.title || "unknown error"}`);
            shelfBtn.disabled = false;
          }
        });
      } catch (_) { shelfBtn.disabled = false; }
    };
    // Takes this page off My Shelf; the bookmark goes back to empty.
    const unsave = () => {
      shelfBtn.disabled = true;
      try {
        chrome.runtime.sendMessage({ type: "safeshelf:unsave", url: getPage().url }, (res) => {
          shelfBtn.disabled = false;
          if (!res?.ok) return toast(`Could not remove from My Shelf: ${res?.error || chrome.runtime.lastError?.message || "unknown error"}`);
          saved = false;
          clearTimeout(savedTimer);
          shelfBtn.dataset.kind = "save";
          shelfBtn.classList.remove("saved", "just-saved");
          label(shelfBtn, "Save to My Shelf", "Save");
          shelfBtn.title = "";
          toast("Removed from My Shelf.");
        });
      } catch (_) { shelfBtn.disabled = false; }
    };
    shelfBtn.onclick = () => {
      if (saved) return unsave();
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
      stopTicker();
      discoveryRun++; // a first look still running belongs to the old product
      checked = false;
      result = null;
      saved = false;
      resetChat();
      clearTimeout(savedTimer);
      shelfBtn.disabled = false;
      shelfBtn.dataset.kind = "save";
      shelfBtn.classList.remove("just-saved", "saved");
      label(shelfBtn, "Save to My Shelf", "Save");
      shelfBtn.title = "";
      markIfSaved();
      fab.className = "fab";
      label(fab, "Check with SafeShelf", "Check");
      setOpen(false);
    };
    if (chatBtn) {
      // The check result for this page (cached for 10 minutes, so this is free after Check). Needed even when
      // SafeShelf does not know the product: the chat then answers from the page and the check, with no safety claim.
      const getCheck = () => new Promise((done) => {
        if (result) done({ r: result }); else identify((r, why) => done({ r, why }));
      });
      const historyBtn = iconBtn("history", "Past chats");
      historyBtn.setAttribute("aria-pressed", "false");
      const newBtn = iconBtn("plus", "New chat");
      const closeChat = iconBtn("close", "Close");
      closeChat.onclick = () => { setChatOpen(false); chatBtn.focus(); };
      const histView = el("div", { className: "hist", hidden: true });
      const note = el("p", { className: "muted", role: "status" });
      const about = el("div", { className: "intro" }); // the product strip and what is read from the page, refreshed each time the chat opens
      const chat = chatUI({ suggestions: ["Is this safe in a child's room?", "Is it genuine?", "Is there a safer option?", "Draft a refund request"],
        hello: "Answers come only from SafeShelf's evidence, with sources. Try one of these:", placeholder: "Ask about this product…",
        what: "Ask SafeShelf a question (your question, the check result and this page's product details are sent)", getCheck, context: chatContext,
        onAsk: () => { showHistory(false); note.textContent = ""; } });

      // Moves the current conversation into Past chats, then starts a new one.
      const archive = async () => {
        if (chat.convo.length) {
          const page = getPage();
          const list = await history.get();
          await history.set([{ id: Date.now(), title: page.title || page.url, url: page.url, at: new Date().toISOString(), messages: chat.convo.slice() }, ...list].slice(0, 30));
        }
        chat.reset();
      };
      const showHistory = async (show) => {
        histView.hidden = !show;
        chat.log.hidden = chat.form.hidden = show;
        chat.intro.hidden = show || !!chat.log.firstChild;
        historyBtn.setAttribute("aria-pressed", String(show));
        if (!show) return;
        const list = await history.get();
        const wipe = el("button", { type: "button", className: "small", textContent: "Delete all past chats" });
        wipe.onclick = async () => { await history.set([]); showHistory(true); };
        histView.replaceChildren(
          el("div", { className: "vh", textContent: "Past chats" }),
          ...(list.length ? [] : [el("p", { className: "muted", textContent: "No past chats yet. Press New chat (+) and the current chat is kept here." })]),
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
      newBtn.onclick = async () => {
        const had = chat.convo.length > 0;
        await archive();
        showHistory(false);
        note.textContent = had ? "New chat started. The last one is in Past chats." : "";
        chat.input.focus();
      };

      chatBox.append(el("div", { className: "card" },
        cardHead("AI", historyBtn, newBtn, closeChat),
        el("h2", { className: "headline", textContent: "Ask about this product" }),
        about, chat.log, histView, chat.intro, chat.form, note,
      ));
      chatBox.addEventListener("keydown", (e) => { if (e.key === "Escape") { setChatOpen(false); chatBtn.focus(); } });

      setChatOpen = (open) => {
        chatBox.hidden = !open;
        syncDrawer();
        chatBtn.setAttribute("aria-expanded", String(open));
        if (!open) return speechSynthesis.cancel();
        setOpen(false);
        const page = getPage();
        about.replaceChildren(productStrip(page, result),
          el("details", { className: "read" }, el("summary", { textContent: "What SafeShelf reads from this page" }), contextCard(page)));
        chat.input.focus();
      };
      resetChat = () => { archive(); showHistory(false); note.textContent = ""; setChatOpen(false); }; // a new product starts a fresh chat; the old one goes to Past chats
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
  let lastUrl = ""; // empty, so the first tick treats the page as new (and fills a missing shelf image on a direct visit)

  // Products saved before images were captured have none on My Shelf. Opening the product page again fills it in.
  const fillShelfImage = () => {
    try {
      const { url, image_urls } = readPage();
      if (image_urls?.[0]) chrome.runtime.sendMessage({ type: "safeshelf:shelf-image", url, image_url: image_urls[0] }, () => void chrome.runtime.lastError);
    } catch (_) {} // the extension was reloaded; nothing to fill
  };
  // The rail's height changes (product page or not, size setting), so its saved position is re-fitted on screen. Never mid-drag.
  const refitRail = () => { if (!floating.host.classList.contains("dragging")) placeY(floating.host, fitY(floating.host, widgetY)); };
  const tick = () => {
    if (!enabled) { // turned off from the toolbar menu: remove everything we added
      speechSynthesis.cancel();
      toastHost?.remove();
      dock();
      floating.host.remove();
      inline.forEach((w) => w.remove());
      inline.clear();
      document.querySelectorAll("[data-safeshelf-card]").forEach((c) => delete c.dataset.safeshelfCard);
      return;
    }
    if (site.isProduct()) {
      inline.forEach((w) => w.remove());
      inline.clear();
      floating.host.classList.remove("shelf-only");
      if (!floating.host.isConnected) document.body.append(floating.host);
      refitRail();
      if (location.href !== lastUrl) { lastUrl = location.href; floating.reset(); setTimeout(fillShelfImage, 2000); }
      return;
    }
    // Not a product page: the rail shows only the My Shelf button.
    if (location.href !== lastUrl) { lastUrl = location.href; floating.reset(); }
    floating.host.classList.add("shelf-only");
    if (!floating.host.isConnected) document.body.append(floating.host);
    refitRail();
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
    if (msg !== "safeshelf:toggle") return;
    tick();
    if (floating.host.isConnected) floating.toggle();
    reply?.({ ok: floating.host.isConnected }); // the toolbar menu says why nothing opened
  };
  chrome.runtime.onMessage.addListener(onMessage);
  window.__safeshelf = {
    cleanup() {
      clearInterval(timer);
      toastHost?.remove();
      dock();
      floating.host.remove();
      inline.forEach((w) => w.remove());
      document.querySelectorAll("[data-safeshelf-card]").forEach((c) => delete c.dataset.safeshelfCard);
      try { chrome.runtime.onMessage.removeListener(onMessage); } catch (_) { /* context already invalidated */ }
    },
  };

  const setEnabled = (value) => { enabled = value !== false; tick(); };
  const readY = (y) => { widgetY = clampY(y); placeY(floating.host, fitY(floating.host, widgetY)); };
  chrome.storage.local.get(["enabled", "widgetY", ...Object.keys(LOOK)], (data = {}) => { readLook(data); if ("widgetY" in data) readY(data.widgetY); setEnabled(data.enabled); });
  const onStorage = (changes, area) => {
    if (area !== "local") return;
    if (Object.keys(LOOK).some((k) => changes[k])) readLook(Object.fromEntries(Object.entries(changes).map(([k, c]) => [k, c.newValue])));
    if (changes.widgetY) readY(changes.widgetY.newValue); // moved in another tab
    if (changes.enabled) setEnabled(changes.enabled.newValue);
  };
  chrome.storage.onChanged.addListener(onStorage);
  const oldCleanup = window.__safeshelf.cleanup;
  window.__safeshelf.cleanup = () => {
    try { chrome.storage.onChanged.removeListener(onStorage); } catch (_) { /* context already invalidated */ }
    oldCleanup();
  };
}
