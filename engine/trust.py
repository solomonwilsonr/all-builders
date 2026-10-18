"""M6 "Is it real?": does this listing look like the genuine product sold by someone who may sell it?
(SAFESHELF.md section 4, items 7 and 8)

    trust_check(listing) -> TrustCheck answer (contract: POST /v1/listings/trust-check)

Four checks against the genuine product (found by M3, read-only): copied photos, impossible price, brand-new
website, conflicting specs. Plus a scan for hidden instructions aimed at AI agents. Code sets every flag and writes
the summary: always "Be careful: ..." with reasons, never "scam". The checks describe the listing; the shopper
decides.

When no genuine product is on file, the listing is checked on its own: who sells it (the brand's own store, an
authorised seller or a third party), its price against the M.R.P. printed on the page, and the website. What looks
right is listed in good_signs, so an unknown product gets reasons instead of a row of "could not verify".
"""
import io
import json
import re
from datetime import UTC, date, datetime
from functools import cache
from pathlib import Path
from urllib.parse import urlparse

import requests

from engine import identity, store
from engine.normalize import attributes, norm_brand
from engine.rules import attribute_conflicts

DATA = Path(__file__).resolve().parents[1] / "data"
LABEL = "Evidence for the shopper - not a legal finding"
PRICE_FLOOR = 0.40  # below 40% of the lowest credible price is not a discount
NEW_DOMAIN_DAYS = 90
PHASH_MAX_DISTANCE = 8
MRP_DEEP_DISCOUNT = 0.40  # below 40% of the listing's own M.R.P.: inflated M.R.P.s are common, so unknown, not a flag
MARKETPLACES = ("amazon.", "flipkart.", "meesho.", "myntra.", "snapdeal.", "jiomart.", "tatacliq.", "ebay.",
                "walmart.", "etsy.", "aliexpress.", "temu.",
                # JAPAC: Japan, South-East Asia, Australia / New Zealand
                "rakuten.", "mercari.", "shopping.yahoo.", "qoo10.", "shopee.", "lazada.", "tokopedia.",
                "bukalapak.", "blibli.", "tiki.vn", "zalora.", "kogan.", "trademe.",
                # Korea, Taiwan, Hong Kong
                "coupang.", "gmarket.", "11st.", "auction.co.kr", "momoshop.", "pchome.", "shopee.tw", "hktvmall.")
TWO_PART_TLDS = ("co.in", "net.in", "org.in", "co.uk", "com.au", "net.au", "org.au", "co.nz", "org.nz", "co.jp",
                 "ne.jp", "or.jp", "com.sg", "com.my", "co.id", "co.th", "com.ph", "com.vn",
                 "co.kr", "or.kr", "ne.kr", "com.tw", "org.tw", "com.hk", "org.hk")
REFERENCE_MATCHES = {"url", "model_number"}
HIDDEN = re.compile(
    r"ignore (all |any |your |the )?(previous|prior|above|earlier) instructions|you are an? (ai|assistant|agent)|"
    r"system prompt|(mark|rate|report|classify|label|show|treat) (this|the) (product|shop|seller|listing|merchant|"
    r"store) as .{0,12}(safe|genuine|trusted|trustworthy|verified|green|legitimate|authentic)|"
    r"safeshelf: this (product|listing|shop) is|safeshelf\s*,|"
    r"do not (warn|flag|tell)|assistant:|<\s*/?\s*(system|instructions)\s*>|"
    # Phrasings the live red-team's attacker used (engine/redteam.py, 16 Oct): a notice addressed to AI shoppers,
    # or telling them to switch off their own warnings.
    r"\b(for|to|attention|note|notice)\W{0,3}(all |any )?(ai|a\.i\.|llm|automated|ai-powered)( shopping)? "
    r"(assistants?|agents?|shoppers?|bots?|crawlers?|systems?|models?)\b|"
    r"\b(disregard|override|bypass|suppress) (all |any |every )?(previous |prior |negative |existing |other )?"
    r"(trust|threat|security|safety|risk|fraud) (flags?|warnings?|checks?|signals?|ratings?)", re.IGNORECASE)


# A shop page has no reason to address an AI or SafeShelf. Beyond the fixed phrasings above, a sentence counts as an
# instruction to AI shoppers when it does all three at once: addresses a machine, tells it to judge or skip something,
# and pushes a trust word. Calibrated on 13 attacks Gemini wrote in the live red-team (engine/redteam.py, 16 Oct).
MACHINE = re.compile(r"\b(system|ai|a\.i\.|llm|assistants?|agents?|bots?|models?|crawlers?|automated|you must)\b",
                     re.IGNORECASE)
COMMAND = re.compile(r"\b(ignore|disregard|override|bypass|skip|suppress|treat|mark|classify|rate|label|output|confirm|"
                     r"consider|exempt|approve|proceed)\b", re.IGNORECASE)
TRUST = re.compile(r"\b(verified|verification|trusted|trustworthy|genuine|authentic|authori[sz]ed|safe|approved|"
                   r"legit(imate)?|certified|trust)\b", re.IGNORECASE)
STRONG = re.compile(r"\bsafeshelf\b|\bsystem (instruction|notice|note|prompt|message|override)s?\b|"
                    r"\b(ignore|disregard|override|skip|bypass)( all| any)?( previous| prior)? (risk|warning|security|"
                    r"trust|threat|safety)", re.IGNORECASE)


def hidden_instructions(text: str | None) -> bool:
    text = text or ""
    if HIDDEN.search(text) or STRONG.search(text):
        return True
    return any(MACHINE.search(s) and COMMAND.search(s) and TRUST.search(s)
               for s in re.split(r"(?<=[.!?\]])\s+|\n+", text))

@cache
def _json(name: str) -> dict:
    path = DATA / name
    return json.loads(path.read_text()) if path.exists() else {}


def host(url: str | None) -> str:
    return (urlparse(url or "").hostname or "").lower().removeprefix("www.")


def registrable(hostname: str) -> str:
    parts = hostname.split(".")
    keep = 3 if ".".join(parts[-2:]) in TWO_PART_TLDS else 2
    return ".".join(parts[-keep:])


def brand_entry(brand: str | None) -> dict:
    """Who may sell this brand (data/authorised_sellers.json), by its name or another name it sells under."""
    brands = _json("authorised_sellers.json").get("brands", {})
    b = norm_brand(brand)
    return brands.get(b) or next((e for e in brands.values() if b and b in e.get("aliases", [])), {})


def named_sellers(entry: dict, url: str | None) -> list[str]:
    """The sellers the brand named for the shop this URL is on. A brand that published a list per shop (boAt: Amazon's
    sellers are not Flipkart's) is held to that shop's list; one that published a single list uses it everywhere."""
    by_shop = entry.get("marketplaces") or {}
    if by_shop:
        names = by_shop.get(registrable(host(url)), {}).get("sellers", []) if host(url) else []
    else:
        names = entry.get("sellers", [])
    aliases = entry.get("seller_aliases") or {}  # other names a named company trades under (SafeShelf's additions)
    return [*names, *(a for n in names for a in aliases.get(n, []))]


def authorised(brand: str, seller: str | None, url: str | None) -> bool:
    entry = brand_entry(brand)
    domain = host(url)
    if domain and any(domain == d or domain.endswith("." + d) for d in entry.get("domains", [])):
        return True
    s = norm_brand(seller)
    named = [norm_brand(n) for n in named_sellers(entry, url)]
    # Marketplaces show the full company name: "Clicktech Retail Private Ltd" for the "Clicktech Retail" a brand names
    return bool(s) and (s == norm_brand(brand) or any(s == n or (len(n) >= 5 and s.startswith(n)) for n in named))


def ships_from(page_text: str | None) -> str | None:
    """Amazon's "Ships from Amazon" / "Fulfilled by Amazon": Amazon holds the stock and handles returns."""
    return "Amazon" if re.search(r"Ships from\s*:?\s*Amazon\b|Fulfilled by Amazon", page_text or "", re.IGNORECASE) \
        else None


# ---------- checks (pure functions, unit-tested) ----------

def price_check(price: float | None, lowest_credible: float | None, currency: str = "INR") -> dict:
    if not price or not lowest_credible:
        return {"result": "unknown", "price": price, "currency": currency, "lowest_credible_price": lowest_credible,
                "reason": "no price" if not price else f"no {currency} price from an authorised seller to compare with"}
    ratio = round(price / lowest_credible, 2)
    return {"result": "flag" if ratio < PRICE_FLOOR else "ok", "price": price, "currency": currency,
            "lowest_credible_price": lowest_credible, "ratio": ratio}


def spec_check(listing: dict, genuine: dict) -> dict:
    text = " ".join(str(listing.get(k) or "") for k in ("title", "page_text"))
    conflicts = attribute_conflicts(attributes(text), genuine.get("attributes") or {})
    return {"result": "flag" if conflicts else "ok", "conflicts": conflicts}


def age_from_rdap(payload: dict) -> date | None:
    for event in payload.get("events", []):
        if event.get("eventAction") == "registration":
            return datetime.fromisoformat(event["eventDate"]).date()
    return None


def website_check(url: str | None, today: date | None = None) -> dict:
    hostname = host(url)
    today = today or datetime.now(UTC).date()
    if not hostname:
        return {"result": "unknown", "reason": "no URL"}
    if hostname in ("localhost", "127.0.0.1"):  # a page served from this computer: nothing to look up
        return {"result": "unknown", "reason": "a local test page has no registration date"}
    if any(m in hostname for m in MARKETPLACES):
        return {"result": "skipped", "reason": "large marketplace; the seller, not the website, is what matters"}
    domain = registrable(hostname)
    demo = _json("demo_domains.json").get("domains", {}).get(domain)
    if demo:  # fictional demo shops; labelled so nobody mistakes it for a real lookup
        registered, source = date.fromisoformat(demo), "demo data (fictional shop)"
    else:
        try:
            response = requests.get(f"https://rdap.org/domain/{domain}", timeout=10)
            registered, source = (age_from_rdap(response.json()) if response.ok else None), "RDAP"
        except (requests.RequestException, ValueError):
            registered, source = None, "RDAP"
    if not registered:
        return {"result": "unknown", "domain": domain, "reason": "registration date not available", "source": source}
    days = (today - registered).days
    return {"result": "flag" if days < NEW_DOMAIN_DAYS else "ok", "domain": domain,
            "domain_registered_days_ago": days, "source": source}


def phash(url: str):
    import imagehash
    from PIL import Image

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return imagehash.phash(Image.open(io.BytesIO(response.content)))


def photo_check(listing_images: list[str], genuine_images: list[str], seller_ok: bool, hasher=phash) -> dict:
    if not listing_images or not genuine_images:
        return {"result": "unknown", "reason": "no photos to compare"}
    genuine, matches = [], 0
    for url in genuine_images[:6]:
        try:
            genuine.append(hasher(url))
        except Exception:  # noqa: BLE001, S112  unreachable or unreadable image: skip it
            continue
    for url in listing_images[:6]:
        try:
            h = hasher(url)
        except Exception:  # noqa: BLE001, S112
            continue
        matches += any(h - g <= PHASH_MAX_DISTANCE for g in genuine)
    copied = matches > 0
    return {"result": "flag" if copied and not seller_ok else "ok", "matches_official_listing": copied,
            "matching_photos": matches, "seller_authorised": seller_ok}


def summary(checks: dict, hidden: bool) -> str:
    reasons = []
    marketplace = "marketplace" in (checks["price"].get("reference") or checks["copied_photos"].get("reference") or "")
    if checks["copied_photos"]["result"] == "flag":
        reasons.append("photos copied from the genuine product's " + (
            "marketplace listing, on a site that is not a known seller" if marketplace else
            "official listing, but the seller is not authorised"))
    if checks["price"]["result"] == "flag":
        reasons.append(f"price is {round(100 * checks['price']['ratio'])}% of the genuine product's lowest " +
                       ("marketplace price" if marketplace else "price from an authorised seller"))
    if checks["website_age"]["result"] == "flag":
        reasons.append(f"website registered only {checks['website_age']['domain_registered_days_ago']} days ago")
    if checks["spec"]["result"] == "flag":
        reasons.append("specs differ from the genuine model (" + "; ".join(checks["spec"]["conflicts"]) + ")")
    if hidden:
        reasons.append("the page hides instructions aimed at AI assistants")
    if not reasons:
        return "No warning signs found in these checks."
    return "Be careful: " + "; ".join(reasons) + "."


def listing_brand(listing: dict) -> str:
    """The brand the listing claims: an explicit field, the page's "Brand" row or "Visit the X Store" link,
    else the first word of the title."""
    if listing.get("brand"):
        return listing["brand"].strip()
    text = listing.get("page_text") or ""
    found = re.search(r"^\s*Brand(?: Name)?\s*:?[ \t]+(?!new\b)([^\n]{1,40}?)\s*$", text, re.MULTILINE | re.IGNORECASE) or \
        re.search(r"Visit the (.+?) Store", text)
    if found:
        return found.group(1).strip()
    words = (listing.get("title") or "").split()
    return words[0].strip(",:-") if words else ""


def listing_mrp(page_text: str | None) -> float | None:
    found = re.search(r"M\.?\s*R\.?\s*P\.?[^\d\n]{0,12}([\d,]+(?:\.\d+)?)", page_text or "", re.IGNORECASE)
    try:
        return float(found.group(1).replace(",", "")) if found else None
    except ValueError:
        return None


def seller_check(brand: str, seller: str | None, url: str | None, page_text: str | None = None) -> dict:
    """Is the seller the brand itself or an authorised seller? A third party is not a warning, only not verified.
    Real brands are checked against the seller list the brand published (data/authorised_sellers.json)."""
    if not seller:
        return {"result": "unknown", "reason": "the page does not name the seller"}
    b, s_ = norm_brand(brand), norm_brand(seller)
    entry = brand_entry(brand)
    extra = {**({"ships_from": ships_from(page_text)} if ships_from(page_text) else {}),
             **({"source": entry["source_url"]} if entry.get("source_url") else {})}
    if len(b) >= 3 and s_.startswith(b):
        return {"result": "ok", "seller": seller, "relationship": "brand", "brand": brand, **extra}
    if brand and authorised(brand, seller, url):
        return {"result": "ok", "seller": seller, "relationship": "authorised", "brand": brand, **extra}
    if len(b) >= 4 and b in s_:  # "PATANJALI NUTRELA NUTRITION" for Nutrela: plausibly the brand's store, not proven
        return {"result": "unknown", "seller": seller, "relationship": "brand_named", "brand": brand, **extra,
                "reason": f"Sold by {seller}. The name includes {brand}, but we can't confirm it's {brand}'s own "
                          "store (any shop can use a brand's name)"}
    # 16 Oct: a shopper took Amazon's "Visit the Samsung Store" link for the seller of a fridge sold by DAWNTECH.
    who = brand or "the brand"
    reason = f"Sold by {seller}, not by {who} itself"
    if entry.get("sellers") and entry.get("source_url"):
        reason += f". They're not on the list of official sellers {who} published"
    else:
        reason += f". We can't confirm they're an official {who} seller"
    store_link = re.search(r"Visit the (.+?) Store", page_text or "")
    if store_link:
        name = store_link.group(1).strip()
        reason += f' ("Visit the {name} Store" is only {name}\'s brand page, not the seller)'
    return {"result": "unknown", "seller": seller, "relationship": "third_party", "brand": brand, **extra,
            "reason": reason}


def mrp_check(price: float | None, mrp: float | None, currency: str = "INR") -> dict:
    """Price against the M.R.P. printed on the listing. The seller sets both, so this can only reassure a little."""
    if not price or not mrp or price > mrp * 1.05:
        return {"result": "unknown", "price": price, "mrp": mrp, "reason": "no M.R.P. on the page to compare with"}
    ratio = round(price / mrp, 2)
    if ratio < MRP_DEEP_DISCOUNT:
        return {"result": "unknown", "price": price, "mrp": mrp, "ratio": ratio, "currency": currency,
                "reason": f"{round(100 * (1 - ratio))}% below the M.R.P. on the page; discounts this deep are often "
                          "an inflated M.R.P., so SafeShelf cannot tell"}
    return {"result": "ok", "price": price, "mrp": mrp, "ratio": ratio, "currency": currency,
            "reference": "the M.R.P. printed on the listing"}


def good_signs(checks: dict, url: str | None) -> list[str]:
    """Plain-words reasons for the checks that passed, for a listing with no genuine product on file."""
    signs = []
    seller = checks.get("seller") or {}
    if seller.get("relationship") == "brand":
        signs.append(f"Sold by the brand itself ({seller['seller']})")
    elif seller.get("relationship") == "authorised":
        signs.append(f"Sold by {seller['seller']}, an authorised seller of {seller['brand']}" +
                     (f" (on the list {seller['brand']} published)" if seller.get("source") else ""))
    if seller.get("ships_from") and seller.get("relationship") not in ("brand", "authorised"):
        signs.append(f"Shipped by {seller['ships_from']}, so returns are easy (this doesn't prove the seller is "
                     "official)")
    price = checks["price"]
    if price["result"] == "ok" and price.get("mrp"):
        off = round(100 * (1 - price["ratio"]))
        signs.append(f"Price is {off}% below the printed M.R.P., a normal discount" if off else
                     "Price matches the printed M.R.P.")
    website = checks["website_age"]
    if website["result"] == "ok":
        signs.append(f"Website registered {website['domain_registered_days_ago'] // 365} years ago")
    elif website["result"] == "skipped" and host(url):
        signs.append(f"Sold on {host(url)}, a big, well-known shop")
    return signs


# ---------- the answer ----------

REFERENCE_MARKETPLACES = ("amazon.in", "flipkart.com", "amazon.com")


def genuine_offer(product_id: str, brand: str, currency: str = "INR") -> tuple[float | None, list[str], str]:
    """Reference price (same currency) and photos for the genuine product: from the brand or an authorised seller
    when we know them, otherwise from its listings on the big marketplaces (said so in the answer)."""
    authorised_rows, marketplace_rows = [], []
    for row in store.product_listings(product_id):
        raw = row["raw"] or {}
        if authorised(brand, raw.get("seller"), row["url"]) or row["marketplace"] == "demo":
            authorised_rows.append(raw)
        elif row["marketplace"] in REFERENCE_MARKETPLACES:
            marketplace_rows.append(raw)
    rows, source = (authorised_rows, "brand or authorised seller") if authorised_rows else \
        (marketplace_rows, "the genuine product's listings on major marketplaces")
    prices = [float(r["price"]) for r in rows if r.get("price") and (r.get("currency") or "INR") == currency]
    images = [u for r in rows for u in r.get("image_urls") or []]
    return (min(prices) if prices else None), images, source


def safety_note(product_id: str) -> str:
    signals = store.conn().execute(
        "SELECT count(*) AS n FROM hazard_signals WHERE product_id = %s AND status = 'under_review'",
        (product_id,)).fetchone()["n"]
    recalled = store.conn().execute(
        "SELECT count(*) AS n FROM recall_products WHERE product_id = %s AND match_class = 'exact_model'",
        (product_id,)).fetchone()["n"]
    parts = ["recalled" if recalled else "no recall"]
    parts.insert(0, f"{signals} hazard finding{'s' if signals != 1 else ''} under review" if signals else
                 "no hazard findings")
    return ", ".join(parts)


def trust_check(listing: dict) -> dict:
    product_id, how = identity.resolve(listing, needs_reference=True)
    # Only the same product is a reference for price, photos and specs. A look-alike is another product: comparing
    # with it called a Rs 89 Lifelong shaker "far below the genuine Rs 2,699" (15 Oct), so the page's own checks run.
    genuine = store.latest_fingerprint(product_id) if product_id and how in REFERENCE_MATCHES else None
    url, seller = listing.get("url"), listing.get("seller")
    if genuine:
        lowest, images, source = genuine_offer(product_id, genuine["brand"], listing.get("currency") or "INR")
        # On a big marketplace the photos are the listing's own; elsewhere they need an authorised seller.
        seller_ok = authorised(genuine["brand"], seller, url) or any(m in host(url) for m in REFERENCE_MARKETPLACES)
        checks = {"copied_photos": {**photo_check(listing.get("image_urls") or [], images, seller_ok),
                                    "reference": source},
                  "price": {**price_check(listing.get("price"), lowest, listing.get("currency") or "INR"),
                            "reference": source},
                  "website_age": website_check(url),
                  "spec": spec_check(listing, genuine)}
    else:
        # Nothing to compare photos or specs with: skipped, not "unknown", so the listing's own checks decide.
        none = {"result": "skipped", "reason": "SafeShelf has no genuine product on file to compare with"}
        checks = {"copied_photos": none,
                  "price": mrp_check(listing.get("price"), listing_mrp(listing.get("page_text")),
                                     listing.get("currency") or "INR"),
                  "website_age": website_check(url), "spec": none,
                  "seller": seller_check(listing_brand(listing), seller, url, listing.get("page_text"))}
    hidden = hidden_instructions(listing.get("page_text"))
    answer = {
        "listing_url": url,
        "matched_product_id": product_id,
        "matched_by": how,
        "checks": checks,
        "hidden_instructions_found": hidden,
        "summary": summary(checks, hidden),
        "good_signs": [] if genuine else good_signs(checks, url),
        "safety_of_genuine_model": safety_note(product_id) if product_id else "unknown product",
        "label": LABEL,
    }
    evidence_id = store.add_evidence("trust_check", url or listing.get("title") or "", answer)
    answer["evidence_ids"] = [evidence_id]
    return answer
