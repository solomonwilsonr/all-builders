"""Reads a product page from a link a shopper pasted, so the agents can check that listing (chat, A2A).

The page is fetched the way a shopper's browser would get it (first MAX_BYTES only). Only public http(s) pages:
every address, including each redirect, must resolve to a public IP, so a pasted link can never make the server read
its own network or the cloud metadata service. What the page says is data for the checks, never instructions.
Amazon pages give title, brand, model number, price, M.R.P., photos and the reviews shown; any other shop gives what
its meta tags and visible text say.
"""
import ipaddress
import json
import os
import re
import socket
from datetime import datetime
from html import unescape
from urllib.parse import unquote, urljoin, urlparse

import httpx

from engine import region

URL = re.compile(r"https?://[^\s<>\"']+")
MAX_BYTES = 3_000_000
MAX_REDIRECTS = 4
HEADERS = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/141.0 Safari/537.36", "accept-language": "en-IN,en;q=0.9", "accept": "text/html"}


class BlockedLink(ValueError):
    pass


def first_url(text: str) -> str | None:
    match = URL.search(text or "")
    return match.group(0).rstrip(".,);]") if match else None


# What shop apps add around a shared link ("Check out this deal on Amazon!", ": Amazon.in: Home & Kitchen").
SHARE_NOISE = re.compile(
    r"check (?:this|it) out|check out this (?:deal|product|item)?|(?:have a )?look at this|i found this|"
    r"\b(?:on|at|via|from) (?:amazon|flipkart)(?:\.[a-z.]+)?\b|:\s*amazon\.[a-z.]+\s*:[^\n]*|\bamazon\.[a-z.]+\b",
    re.IGNORECASE)
NOT_A_NAME = {"is", "are", "can", "could", "should", "would", "will", "does", "do", "did", "what", "which", "how",
              "why", "when", "where", "who", "please", "pls", "tell", "check", "hey", "hi", "hello", "ok", "safe",
              "real", "fake", "genuine", "kya", "क्या", "यह", "ये"}


def shared_name(message: str) -> str | None:
    """The product name a shop app's Share button puts next to the link ("Lifelong Protein Shaker LLSHB04 ...
    https://amzn.in/d/x"), or None when the words around the link are only a question or a greeting."""
    text = SHARE_NOISE.sub(" ", URL.sub(" ", message or ""))
    names = []
    for chunk in re.split(r"\n+", text):
        chunk = re.sub(r"[^?\n]*\?", " ", chunk)  # questions are the shopper's, not the product's name
        chunk = re.sub(r"\s+", " ", chunk).strip(" -:|,.!\"'")
        words = chunk.split()
        if len(words) >= 2 and words[0].lower().strip(",") not in NOT_A_NAME:
            names.append(chunk)
    return max(names, key=len)[:200] if names else None


def name_from_url(url: str) -> str | None:
    """The product name shops put in their links: amazon.in/Lifelong-Protein-Shaker-LLSHB04/dp/B0CFFBZ23F,
    flipkart.com/lifelong-shaker/p/itm123. None for links without one (amzn.in/d/x, /dp/ASIN)."""
    match = re.search(r"/([^/?#]+)/(?:dp|gp/product|p)/[A-Za-z0-9]", urlparse(url or "").path)
    words = re.sub(r"[-_+]+", " ", unquote(match.group(1))).split() if match else []
    return " ".join(words)[:200] if len(words) >= 2 else None


def check_public(url: str) -> None:
    """Raises BlockedLink unless url is plain http(s) on a public address."""
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.port not in (None, 80, 443):
        raise BlockedLink("only ordinary http(s) web pages can be checked")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parts.hostname, None)}
    except socket.gaierror:
        raise BlockedLink("that website could not be found") from None
    if not addresses or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addresses):
        raise BlockedLink("that address is not a public website")


def fetch(url: str) -> tuple[str, str]:
    """(final url, html). Follows redirects itself, checking each address first."""
    with httpx.Client(timeout=15, follow_redirects=False, headers=HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            check_public(url)
            with client.stream("GET", url) as response:
                if response.is_redirect and response.headers.get("location"):
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    chunks.append(chunk)
                    size += len(chunk)
                    if size > MAX_BYTES:
                        break
                return str(response.url), b"".join(chunks).decode("utf-8", "replace")
    raise BlockedLink("too many redirects")


def _text(fragment: str | None) -> str:
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment or ""))).strip()


def _meta(html: str, name: str) -> str | None:
    m = re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]*content=["\']([^"\']+)', html, re.IGNORECASE) \
        or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{re.escape(name)}["\']', html, re.IGNORECASE)
    return unescape(m.group(1)).strip() if m else None


def _number(text: str | None) -> float | None:
    m = re.search(r"\d[\d,]*(\.\d+)?", text or "")
    return float(m.group(0).replace(",", "")) if m else None


def amazon_reviews(html: str) -> list[dict]:
    out = []
    for block in html.split('data-hook="review"')[1:31]:
        block = block[:12000]
        text = re.search(r'data-hook="reviewRichContentContainer"[^>]*>(.*?)</div>', block, re.DOTALL) or \
            re.search(r'data-hook="review-body"[^>]*>(.*?)</span>\s*</span>', block, re.DOTALL)
        body = _text(text.group(1) if text else "")
        if not body:
            continue
        title = re.search(r'data-hook="review(?:Title|-title)"[^>]*>(.*?)</(?:h5|a|span)>', block, re.DOTALL)
        stars = re.search(r"([\d.]+) out of 5 stars", block)
        when = re.search(r'data-hook="review-date"[^>]*>[^<]*? on (\d{1,2} \w+ \d{4})', block)
        date = None
        if when:
            try:
                date = datetime.strptime(when.group(1), "%d %B %Y").date().isoformat()
            except ValueError:
                pass
        out.append({"title": re.sub(r"^[\d.]+ out of 5 stars\s*", "", _text(title.group(1) if title else ""))[:200]
                    or None, "text": body[:1500], "rating": float(stars.group(1)) if stars else None, "date": date})
    return out


def _ld_product(html: str) -> dict:
    """The schema.org Product a shop publishes in its page (Flipkart and most shops do): name, price, photos, reviews."""
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.IGNORECASE | re.DOTALL):
        try:
            data = json.loads(block.strip())
        except ValueError:
            continue
        for item in [*(data if isinstance(data, list) else [data]), *((data.get("@graph") or []) if isinstance(data, dict) else [])]:
            if isinstance(item, dict) and "Product" in ([item.get("@type")] if isinstance(item.get("@type"), str) else item.get("@type") or []):
                return item
    return {}


NOT_FOUND = re.compile(r"page not found|404|sorry! we couldn.t find that page|looking for something\?", re.IGNORECASE)


def listing_from_html(url: str, html: str) -> dict:
    """What a shop page says about itself."""
    page_title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = _text((re.search(r'id="productTitle"[^>]*>(.*?)</span>', html, re.DOTALL) or [None, None])[1]) or \
        _meta(html, "og:title") or _text(page_title.group(1) if page_title else "")
    byline = _text((re.search(r'id="bylineInfo"[^>]*>(.*?)</a>', html, re.DOTALL) or [None, None])[1])
    brand = (re.sub(r"^(Visit the |Brand: )|( Store)$", "", byline).strip() or None) if byline else None
    model = re.search(r"(?:Item model number|Model Number|Model Name)\s*</[^>]+>\s*(?:<[^>]+>\s*)*([^<]{2,40})<", html)
    core = html[html.find("corePrice"):][:20000] if "corePrice" in html else html
    price = _number((re.search(r'class="a-price-whole">([\d,]+)', core) or [None, None])[1]) or \
        _number(_meta(html, "product:price:amount") or _meta(html, "og:price:amount"))
    mrp = re.search(r"M\.R\.P\.:?\s*</span>.*?₹\s?([\d,]+)", html, re.DOTALL)
    images = list(dict.fromkeys(re.findall(r'"hiRes":"(https:[^"]+)"', html)))[:6] or \
        [u for u in [_meta(html, "og:image")] if u]
    details = [f"Brand: {brand}" if brand else "", f"Model: {model.group(1).strip()}" if model else "",
               f"M.R.P.: ₹{mrp.group(1)}" if mrp else ""]
    body = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    visible = _text(body)
    listing = {"url": url, "title": title[:300] if title else None, "brand": brand, "price": price,
               "currency": _meta(html, "product:price:currency") or _meta(html, "og:price:currency") or
               region.CURRENCY.get(region.of(url) or ""),
               "image_urls": images, "reviews": amazon_reviews(html),
               "page_text": "\n".join(d for d in details if d) + "\n" + visible[:3000]}
    # schema.org data fills what the shop-specific patterns missed
    ld = _ld_product(html)
    offer = ld.get("offers") or {}
    offer = (offer[0] if isinstance(offer, list) and offer else offer) if isinstance(offer, (list, dict)) else {}
    if ld:
        listing["title"] = listing.get("title") if listing.get("title") and not NOT_FOUND.search(listing["title"]) else (str(ld.get("name") or "")[:300] or listing.get("title"))
        if not listing.get("price"):
            listing["price"] = _number(str(offer.get("price") or offer.get("lowPrice") or ""))
        if offer.get("priceCurrency"):
            listing["currency"] = offer["priceCurrency"]
        if not listing.get("brand") and ld.get("brand"):
            listing["brand"] = (ld["brand"].get("name") if isinstance(ld["brand"], dict) else str(ld["brand"])) or None
        photos = ld.get("image")
        photos = [photos] if isinstance(photos, str) else [p if isinstance(p, str) else (p or {}).get("url") for p in (photos or [])]
        if photos and not listing.get("image_urls"):
            listing["image_urls"] = [p for p in photos if p and p.startswith("https:")][:6]
        if not listing.get("reviews"):
            listing["reviews"] = [{"title": str(r.get("name") or "")[:200], "text": str(r.get("reviewBody") or "")[:1500],
                                   "rating": _number(str((r.get("reviewRating") or {}).get("ratingValue") or ""))}
                                  for r in (ld.get("review") or [])[:20] if isinstance(r, dict) and r.get("reviewBody")]
        seller = (offer.get("seller") or {}) if isinstance(offer.get("seller"), dict) else {}
        if seller.get("name"):
            listing["seller"] = str(seller["name"])[:120]
    # a shop's "page not found" is not a product
    if listing.get("title") and NOT_FOUND.search(listing["title"]) and not ld:
        return {"url": url}
    return {k: v for k, v in listing.items() if v not in (None, "", [])}


def clean(url: str) -> str:
    """A product page without its tracking query (Amazon /dp/ASIN links keep only the product path)."""
    parts = urlparse(url)
    asin = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", parts.path)
    if asin and "amazon." in (parts.hostname or ""):
        return f"{parts.scheme}://{parts.hostname}/dp/{asin.group(1)}"
    return f"{parts.scheme}://{parts.hostname}{parts.path}"


def read(url: str) -> dict:
    """The listing behind a pasted link. A page that can't be read is still checked by its URL alone."""
    url = clean(url)
    try:
        final, html = fetch(url)
    except BlockedLink:
        raise
    except httpx.HTTPError:
        return {"url": url, "read": "none"}
    listing = listing_from_html(clean(final), html)
    # Big shops show servers less than they show shoppers (seen 15 Oct: Amazon gave Cloud Run the title but no price
    # or reviews). Then the answer says so instead of reading "0 reviews" as a finding.
    full = bool(listing.get("price")) or bool(listing.get("reviews"))
    return {**listing, "read": "full" if full else "partial" if listing.get("title") else "none"}


# --- A page read for the judges' page browser: directly first, then through a real browser when the shop held back ---
FIRECRAWL_SCRAPE = os.environ.get("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v2") + "/scrape"


def rendered_html(url: str) -> str | None:
    """The page as a real browser renders it (Firecrawl, 1 credit), or None without FIRECRAWL_API_KEY or on failure.
    Only public addresses are sent, as for a direct read."""
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        return None
    check_public(url)
    try:
        response = httpx.post(FIRECRAWL_SCRAPE, json={"url": url, "formats": ["rawHtml"], "onlyMainContent": False},
                              headers={"Authorization": f"Bearer {key}"}, timeout=90)
        data = (response.json() or {}).get("data") or {}
    except (httpx.HTTPError, ValueError):
        return None
    return data.get("rawHtml") or data.get("html") or None


def _richness(listing: dict) -> int:
    return sum([bool(listing.get("title")), 2 * bool(listing.get("price")), 2 * bool(listing.get("reviews")), bool(listing.get("image_urls"))])


def read_live(url: str) -> dict:
    """read(), and when the shop showed the server too little (no price, no reviews), the same page rendered by a
    real browser; the richer of the two. via says which one: "direct" or "browser"."""
    first = read(url)
    if first.get("read") == "full":
        return {**first, "via": "direct"}
    html = rendered_html(clean(url))
    if not html:
        return {**first, "via": "direct"}
    second = listing_from_html(clean(url), html)
    if _richness(second) <= _richness(first):
        return {**first, "via": "direct"}
    full = bool(second.get("price")) or bool(second.get("reviews"))
    return {**second, "read": "full" if full else "partial" if second.get("title") else "none", "via": "browser"}
