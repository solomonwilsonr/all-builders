"""officialSeller: is the seller an official partner of the brand? POST /v1/listings/official-seller.

Plain code over the registry of brand-published lists (data/authorised_sellers.json, read by engine.trust). It needs only
the listing's URL, title and seller name: no page text, no AI, no search, no network, no cost. The brand comes from the
title: a registry brand the title opens with is the product's brand; if it opens with anything else ("33W Type-C Charger
... Compatible with CMF by Nothing"), a registry brand the title names is checked on this shop. It is information, never
a score, and every statement cites the brand's own page and its date.

What a brand published decides what can be said:
  a seller list for this shop     -> the seller is on it (official), or is not on it (not official; the list may use the
                                      seller's company name, which the details say)
  official channels, no sellers   -> the shop is one of them, or is not (the brand's own words)
  only its own websites           -> nothing is said about marketplace sellers (verdict "no_list": one quiet line)
  no registry brand in the title   -> nothing to check (verdict "unknown_brand": one quiet line)
"""
import re

from engine import trust
from engine.normalize import norm_brand

POLICY = "official-seller-v1"
LABEL = ("From the brand's own published page, not a regulator's finding. A seller that is not named can still be "
         "genuine: lists change, and a seller may trade under another name.")
SHOPS = {"amazon.in": "Amazon.in", "flipkart.com": "Flipkart", "myntra.com": "Myntra", "snapdeal.com": "Snapdeal",
         "tatacliq.com": "Tata Cliq", "paytmmall.com": "Paytm", "nykaa.com": "Nykaa", "croma.com": "Croma",
         "reliancedigital.in": "Reliance Digital", "vijaysales.com": "Vijay Sales", "jiomart.com": "JioMart",
         "meesho.com": "Meesho", "cred.club": "CRED", "ajio.com": "Ajio", "firstcry.com": "FirstCry"}
AMAZON_ITSELF = {"amazon", "amazonin", "amazonretail", "amazonretailindia", "amazonindia"}
MENTION_SHOWN = {"official_seller", "third_party", "channel_not_listed", "channel_listed"}
SHOWN = {"official_brand", "official_seller", "amazon_retail", "channel_not_listed", "channel_listed",
         "official_website", "third_party_website"}


def shop_name(shop: str) -> str:
    return SHOPS.get(shop, shop)


COMPANY_WORDS = {"electronics", "india", "pvt", "ltd", "private", "limited", "corporation", "corp", "co", "inc", "technologies",
                 "technology", "llp", "llc", "mobility", "lifestyle", "digital", "appliances"}


def has_brand_name(seller: str, names: set[str]) -> bool:
    """The seller's name is the brand's name plus only plain company words ("Samsung India Electronics Pvt Ltd"). A
    marketplace seller can type any display name, so this is a hint that the brand sells it, never proof."""
    words = re.findall(r"[a-z0-9]+", (seller or "").lower())
    for cut in range(1, len(words) + 1):
        if "".join(words[:cut]) in names and all(w in COMPANY_WORDS for w in words[cut:]):
            return True
    return False


def source_of(entry: dict) -> dict:
    return {"text": entry.get("source"), "url": entry.get("source_url"), "as_of": entry.get("as_of"),
            "retrieved": entry.get("retrieved")}


OFFICIAL = {"official_seller": True, "channel_listed": True, "official_website": True, "third_party": False,
            "channel_not_listed": False, "third_party_website": False}


def answer(verdict, headline, tone, text, brand, seller, shop, entry, reasons, channels=None) -> dict:
    """official: True / False when the brand's own page settles whether this is an official partner, else None."""
    return {"verdict": verdict, "official": OFFICIAL.get(verdict), "headline": headline, "tone": tone, "text": text,
            "brand": brand,
            "seller": seller,
            "marketplace": shop, "official_channels": channels, "source": source_of(entry) if entry else None,
            "reasons": reasons, "policy_version": POLICY, "label": LABEL}


def opening_brand(title: str) -> tuple[str, dict, str] | None:
    """The registry brand the title opens with ("boAt Airdopes 141", "Samsung Galaxy M35"): what a shopper reads as the product's
    brand. Two opening words are tried before one."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", title or "")
    for n in (2, 1):
        name = " ".join(words[:n])
        entry = trust.brand_entry(name) if name else {}
        if entry:
            return norm_brand(name), entry, name
    return None


def mentioned_brands(title: str, skip: set[str]) -> list[tuple[str, dict, str]]:
    """Registry brands the title names anywhere ("... compatible with CMF Phone 1"), in the order they appear, as the title
    writes them. Names of three or more letters only, whole words only, and never the brands in skip."""
    words = re.findall(r"[A-Za-z0-9]+", title or "")
    seen, out = set(), []
    for i, word in enumerate(words):
        for span in (word, word + words[i + 1] if i + 1 < len(words) else None):
            norm = norm_brand(span) if span else ""
            entry = trust.brand_entry(norm) if len(norm) >= 3 else {}
            if entry and norm not in skip and id(entry) not in seen:
                seen.add(id(entry))
                out.append((norm, entry, span))
    return out


def brand_store_answer(listing: dict, out: dict, shop: str | None) -> dict | None:
    """Amazon links a listing to "Visit the {brand} Store" only for a brand's own store (Brand Registry). When the registry
    can say nothing about this brand on Amazon, that link, read from the page and matching the title's brand, shows the
    brand sells officially there. It says nothing about which resellers are authorised."""
    name = re.sub(r"\s+", " ", str(listing.get("brand_store") or "")).strip()[:60]
    key = norm_brand(name)
    words = re.findall(r"[A-Za-z0-9]+", listing.get("title") or "")
    opens = key and any(norm_brand("".join(words[:n])) == key for n in (1, 2, 3))
    if shop != "amazon.in" or not opens or out["verdict"] not in ("no_list", "unknown_brand"):
        return None
    seller = out.get("seller")
    sold = f"{name} product sold by {seller} on Amazon.in." if seller else f"{name} product on Amazon.in."
    return {**out, "verdict": "channel_listed", "official": True, "headline": "Official brand store on Amazon.in", "tone": "ok",
            "text": f"{sold} {name} has an official brand store on Amazon.in.", "brand": name,
            "source": {"text": f"The listing links to the \"{name} Store\" on Amazon.in", "url": None, "as_of": None, "retrieved": None},
            "reasons": [f"Only a brand's owner can open a brand store on Amazon.in, so {name} sells officially there",
                        "It does not say which resellers are authorised"]}


def assess(listing: dict) -> dict:
    out = _assess(listing)
    url = listing.get("url")
    shop = trust.registrable(trust.host(url)) if trust.host(url) else None
    return brand_store_answer(listing, out, shop) or out


def _assess(listing: dict) -> dict:
    """Who is selling it, against the brand's own published lists, from the title and the seller name alone."""
    title = (listing.get("title") or "").strip()
    seller = (listing.get("seller") or "").strip()[:120] or None
    url = listing.get("url")
    shop = trust.registrable(trust.host(url)) if trust.host(url) else None
    explicit = listing.get("brand")  # a client that knows the brand may pass it; the page extension does not
    opening = (norm_brand(explicit), trust.brand_entry(explicit), str(explicit).strip()[:40]) \
        if explicit and trust.brand_entry(explicit) else opening_brand(title)
    if opening:  # the product's own brand: whatever it can say (or not) is the answer
        return judge(listing, *opening, seller, url, shop)
    for key, entry, written in mentioned_brands(title, set()):  # a brand the title only names ("compatible with CMF Phone 1")
        out = judge(listing, key, entry, written, seller, url, shop, mention=True)
        if out["verdict"] in MENTION_SHOWN:
            return {**out, "mentioned_brand": written}
    return answer("unknown_brand", "No official seller information", "none",
                  "No brand with a published seller list is named in the title." if title else
                  "The listing's title was not found, so there is no brand to check.",
                  None, seller, shop, {}, [])


def judge(listing, key, entry, written, seller, url, shop, mention=False) -> dict:
    brand = written
    marketplace = bool(shop) and any(m in trust.host(url) for m in trust.MARKETPLACES)
    kind = entry.get("list_kind", "sellers")
    shop_label = shop_name(shop) if shop else "this site"
    product = f"{brand} product"
    sold = f"{product} sold by {seller} on {shop_label}." if seller else f"{product} on {shop_label}."
    if mention:  # the title only names this brand (a compatible accessory, perhaps): say that, not "{brand} product"
        sold = f"{brand} is mentioned in the title."

    if not marketplace:  # another website: the brand's own, or not
        if trust.authorised(key, None, url):
            return answer("official_website", "Official website", "ok", f"This is one of {brand}'s own websites.",
                          brand, seller, shop, entry, [f"{shop} is listed as {brand}'s own website"])
        if entry.get("domains"):
            own = ", ".join(entry["domains"][:3])
            return answer("third_party_website", "Not an official website", "none",
                          f"{brand}'s own websites: {own}. This is not one of them.", brand, seller, shop, entry,
                          [f"{shop} is not among {brand}'s published websites", "It may still be a genuine reseller"])
        return answer("no_list", "No official seller information", "none", "No published list for this shop.", brand, seller, shop, entry, [])

    s = norm_brand(seller)
    if s in AMAZON_ITSELF:  # exactly Amazon: "Amazon Basics Traders" is a third party
        return answer("amazon_retail", "Sold by Amazon", "none", f"{product} sold by Amazon itself.",
                      brand, seller, shop, entry, ["The seller is Amazon"])
    if not seller:
        return answer("no_list", "No official seller information", "none", "The seller's name was not found on the page.", brand, seller, shop, entry, [])

    canonical = next((k for k, v in trust._json("authorised_sellers.json").get("brands", {}).items() if v is entry), key)
    named = trust.named_sellers(entry, url)
    on_list = any(s == n or (len(n) >= 5 and s.startswith(n)) for n in map(norm_brand, named))
    has_list = bool(named) or shop in (entry.get("marketplaces") or {})
    if on_list:  # named by the brand: the strongest statement, ahead of any guess from the seller's name
        company = next((n for n, others in (entry.get("seller_aliases") or {}).items()
                        if any(s == norm_brand(a) or (len(norm_brand(a)) >= 5 and s.startswith(norm_brand(a))) for a in others)), None)
        if company and company in named:  # the seller trades under a name the brand's list does not use
            return answer("official_seller", "Official partner", "ok",
                          f"{sold} {seller} is a trade name of {company}, which is on {brand}'s list of official {shop_label} sellers.",
                          brand, seller, shop, entry,
                          [f"{company} is on the list of authorised sellers {brand} published for {shop_label}",
                           f"'{seller}' is recorded by SafeShelf as a trade name of {company}: that name is not on the brand's own list"])
        return answer("official_seller", "Official partner", "ok",
                      f"{sold} {seller} is on {brand}'s list of official {shop_label} sellers.",
                      brand, seller, shop, entry, [f"{seller} is on the list of authorised sellers {brand} published for {shop_label}"])
    if has_brand_name(seller, {norm_brand(brand), key, canonical, *entry.get("aliases", [])}):
        return answer("official_brand", "Seller named like the brand", "none",
                      f"{sold} The seller carries the {brand} name (a hint, not proof).", brand, seller, shop, entry,
                      [f"The seller's name is {brand}'s name", "Any seller can choose a display name"])
    if has_list:  # the brand sells officially on this shop through named sellers; a reseller may be any of them or another
        shown = ", ".join(named[:3]) + (f" and {len(named) - 3} more" if len(named) > 3 else "")
        return answer("channel_listed", f"Official on {shop_label}", "ok",
                      f"{sold} {brand} is officially sold on {shop_label}. Its listed sellers: {shown}.",
                      brand, seller, shop, entry,
                      [f"{brand} publishes official {shop_label} sellers, so it sells officially there",
                       f"{seller} is not among the {len(named)} named sellers; the list may use its company name"])
    channels = [shop_name(c) for c in entry.get("official_channels", [])]
    if entry.get("official_channels") and kind in ("channels", "sellers"):
        if shop in entry["official_channels"]:
            return answer("channel_listed", "Official channel", "ok",
                          f"{sold} {shop_label} is one of {brand}'s official online partners; no individual sellers are named.",
                          brand, seller, shop, entry, [f"{shop_label} is among {brand}'s official channels"], channels)
        partners = (", ".join(channels) if len(channels) <= 4 else f"{', '.join(channels[:3])} and {len(channels) - 3} more")
        return answer("channel_not_listed", "Not an official partner", "none",
                      f"{sold} {brand}'s official online partners: {partners}.", brand, seller, shop, entry,
                      [f"{brand}'s published channels: {', '.join(channels)}; {shop_label} is not among them",
                       "A seller on a shop the brand does not list can still be genuine"], channels)
    return answer("no_list", "No official seller information", "none",
                  f"{brand} publishes no list of authorised {shop_label} sellers.", brand, seller, shop, entry,
                  [f"{brand}'s own pages name no marketplace sellers"])
