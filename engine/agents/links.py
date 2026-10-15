"""Reads a product page from a link a shopper pasted, so the agents can check that listing (chat, A2A).

The page is fetched the way a shopper's browser would get it (first MAX_BYTES only). Only public http(s) pages:
every address, including each redirect, must resolve to a public IP, so a pasted link can never make the server read
its own network or the cloud metadata service. What the page says is data for the checks, never instructions.
Amazon pages give title, brand, model number, price, M.R.P., photos and the reviews shown; any other shop gives what
its meta tags and visible text say.
"""
import ipaddress
import re
import socket
from datetime import datetime
from html import unescape
from urllib.parse import urljoin, urlparse

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
    return {**listing, "read": "full" if full else "partial"}
