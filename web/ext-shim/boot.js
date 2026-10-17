// Starts the real SafeShelf extension on one sample listing inside the judges' page:
// draws the shop page from the sample's listing, loads the extension's background code, then its content scripts
// in the manifest's order, exactly as Chrome would on a product page.
import { renderMessage, renderPage } from "../desk.js?v=20261017j";

const params = new URLSearchParams(location.search);
const box = document.getElementById("page");

async function listingToShow() {
  const id = params.get("sample");
  if (id) {
    const { presets } = await (await fetch("samples/presets.json")).json();
    const p = presets.find((x) => x.id === id);
    if (p) return { listing: p.request.listing, id };
  }
  const url = params.get("url");
  if (!url) return null;
  // a real page: read live by the API (directly, or through a real browser when the shop holds back)
  const tell = (m) => parent.postMessage({ type: "safeshelf:page-read", ...m }, location.origin);
  box.replaceChildren(Object.assign(document.createElement("p"), { className: "s-loading", textContent: "Opening the real page…" }));
  let page;
  try { page = await parent.SafeShelfDemo.readPage(url); }
  catch (err) { tell({ read: "error", error: err.message }); renderMessage(box, "This page couldn't be opened", err.message); return null; }
  if (page.read === "none" || !page.title) {
    tell({ read: "none", via: page.via });
    renderMessage(box, "This shop didn't show its page to SafeShelf", "Shops sometimes hold back pages from servers. Try another product link, or install the extension to check it in your own browser.");
    return null;
  }
  tell({ read: page.read, via: page.via });
  const { read, via, ...listing } = page;
  return { listing, id: "your-link" };
}

const loadScript = (src) => new Promise((resolve, reject) => {
  const s = document.createElement("script");
  s.src = src; s.onload = resolve; s.onerror = () => reject(new Error(`could not load ${src}`));
  document.head.append(s);
});

const shown = await listingToShow();
if (shown) {
  globalThis.__safeshelfListing = shown.listing;
  // the widget reads this page; the canonical link and listing id are what it uses on a local demo page
  document.body.dataset.safeshelfListingId = shown.id;
  const link = Object.assign(document.createElement("link"), { rel: "canonical", href: shown.listing.url });
  document.head.append(link);
  renderPage(box, { listing: shown.listing, bare: true });
  // schema.org Product data, as real shops publish it: the widget reads the price's currency from here
  const l = shown.listing;
  const ld = { "@context": "https://schema.org", "@type": "Product", name: l.title || l.url, url: l.url,
    ...(l.price !== undefined ? { offers: { "@type": "Offer", price: l.price, priceCurrency: l.currency || "INR", ...(l.seller ? { seller: { "@type": "Organization", name: l.seller } } : {}) } } : {}) };
  document.head.append(Object.assign(document.createElement("script"), { type: "application/ld+json", textContent: JSON.stringify(ld) }));

  const manifest = await (await fetch("ext/manifest.json")).json();
  globalThis.__safeshelfManifest = manifest;
  globalThis.__safeshelfPhase = "background";
  await import("./background.js");
  globalThis.__safeshelfPhase = "content";
  for (const file of manifest.content_scripts[0].js) await loadScript(`ext/${file}?v=${manifest.version}`);

  // the browser window's toolbar shield opens the widget, like the extension's toolbar button
  addEventListener("message", (e) => {
    if (e.origin !== location.origin || e.data?.type !== "safeshelf:open") return;
    chrome.tabs.sendMessage(1, "safeshelf:toggle");
  });
  parent.postMessage({ type: "safeshelf:frame-ready", id: shown.id }, location.origin);
}
