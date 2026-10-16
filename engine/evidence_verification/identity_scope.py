"""Exact product / variant / batch verification (plan v2.2 J1, J3 step 3, section 2A matching safeguards).

    check(product, record, market) -> {tier, scope, local, reasons, would_change}

Tiers: exact (same model code, same brand or a distinctive code), variant (same base code with a regional or
colour suffix), suspected_rebrand (same code under another brand), lookalike (same brand and kind, different code),
family_named (the notice names the brand and kind but no model codes: a person must check), unresolved (the product
has no model code), none. Only exact + in_scope can ever confirm a recall, and only from a local notice. Weak edges
never chain: this compares the product with the notice directly, never through another product.
"""
import re

from engine import locales
from engine.normalize import norm_brand
from engine.region_policy import is_local

# A variant suffix after a separator ("PB22-EU", "X100/BK", "W5 PRO"), or a region code glued on ("PB22EU").
# Digits never count as a suffix: CX-65 and CX-650 are different models.
SEP_SUFFIX = re.compile(r"^(?P<base>.+?)[\s\-/_](?:EU|UK|US|AU|JP|IN|SG|KR|CN|BK|WH|BL|GR|RD|B|W|S|PRO|PLUS|MAX|"
                        r"MINI|LITE|V\d)$", re.IGNORECASE)
GLUED_REGION = re.compile(r"^(?P<base>.+?)(?:EU|UK|US|AU|JP|IN|SG|KR)$")
RANGE = re.compile(r"([A-Z]*\d[\w-]*)\s*(?:to|through|thru|until|-|–|~|〜|から)\s*([A-Z]*\d[\w-]*)", re.IGNORECASE)
GENERIC = {"POWERBANK", "CHARGER", "ADAPTER", "HEATER", "BATTERY", "CABLE", "USBC", "TYPEC"}


def base_code(model: str) -> str:
    raw = locales.fold(model).strip().upper()
    if (m := SEP_SUFFIX.match(raw)) and len(locales.comparable_model(m.group("base"))) >= 4:
        return locales.comparable_model(m.group("base"))
    code = locales.comparable_model(raw)
    if (m := GLUED_REGION.match(code)) and len(m.group("base")) >= 4 and re.search(r"\d", m.group("base")):
        return m.group("base")
    return code


def _brand_in(record: dict, brand: str) -> bool:
    b = norm_brand(brand)
    if len(b) < 2:
        return False
    names = [norm_brand(x) for x in record.get("product_identifiers", {}).get("brands", [])]
    text = norm_brand(f"{record.get('title')} {record.get('original_text')}")
    return any(b == n or (len(b) >= 4 and b in n) for n in names) or (len(b) >= 3 and b in text)


GENERIC_WORDS = {"black", "white", "with", "original", "brand", "pack", "portable", "power", "battery", "digital",
                 "smart", "wireless", "charging", "fast", "compact", "ultra", "premium", "travel", "high", "speed",
                 "poweriq", "inch", "litre", "liter", "pieces", "piece", "multi", "universal", "electric"}


def same_kind(product: dict, notice_title: str) -> bool:
    """Does the notice name this kind of product? By the product's category (power bank, heater...) when known, else
    by the title's distinctive nouns. The brand name never counts: an Anker scooter is not an Anker power bank."""
    from engine.normalize import CATEGORIES, category_of
    named = notice_title.lower()
    category = product.get("category") or category_of(product.get("title") or "")
    if category in CATEGORIES:
        return bool(re.search(CATEGORIES[category], named))
    brand = norm_brand(product.get("brand"))
    text = f"{category or ''} {product.get('title') or ''}".replace("_", " ").lower()
    words = [w.rstrip("s") for w in re.findall(r"[a-z]{5,}", text)
             if w not in GENERIC_WORDS and norm_brand(w) != brand and not (brand and norm_brand(w) in brand)]
    return any(re.search(rf"\b{re.escape(w)}", named) for w in words[:6])


def tier(product: dict, record: dict) -> tuple[str, list[str]]:
    model = locales.comparable_model(product.get("model"))
    brand = product.get("brand") or ""
    notice_models = record.get("product_identifiers", {}).get("models") or []
    codes = {locales.comparable_model(m): m for m in notice_models if len(locales.comparable_model(m)) >= 3}
    gtins = set(record.get("product_identifiers", {}).get("gtins") or []) | \
        set(record.get("product_identifiers", {}).get("upcs") or [])
    brand_named = _brand_in(record, brand) if brand else False
    if product.get("gtin") and product["gtin"] in gtins:
        return "exact", [f"the notice lists this product's barcode {product['gtin']}"]
    if not model:
        if brand_named:
            return "unresolved", ["the notice names this brand, but the product's model number is not known"]
        return "none", []
    if model in GENERIC:
        return "unresolved", [f"'{product.get('model')}' is a product type, not a model number"]
    if model in codes:
        if brand_named or not brand or len(model) >= 6:
            why = f"the notice names model {codes[model]}"
            return "exact", [why + (" and this brand" if brand_named else "")]
        return "suspected_rebrand", [f"the notice names model {codes[model]} under another brand"]
    # Shops often list the full product code: Anker's A1263011 is the recalled A1263 plus a colour / pack code.
    for code, original in codes.items():
        rest = model[len(code):] if len(code) >= 5 and model.startswith(code) else ""
        if rest and rest.isdigit() and len(rest) <= 3 and re.search(r"\d", code) and (brand_named or not brand):
            return "exact", [f"the notice names model {original}; this listing's code {product.get('model')} is "
                             f"{original} plus a colour or pack code ({rest})"]
    base = base_code(product.get("model") or "")
    for original in codes.values():
        if len(base) >= 4 and base_code(original) == base:
            return ("variant" if brand_named or not brand else "suspected_rebrand"), \
                [f"the notice names {original}, a variant of {product.get('model')} (same base code {base})"]
    if codes and brand_named:
        return "lookalike", [f"the notice names {', '.join(list(codes.values())[:4])}, not {product.get('model')}"]
    if not codes and brand_named and same_kind(product, record.get("title") or ""):
        return "family_named", ["the notice names this brand and product type but no model numbers"]
    return "none", []


def _in_range(value: str, low: str, high: str) -> bool | None:
    """Is a serial or lot number inside a numeric range? None when the parts aren't comparable numbers."""
    v, a, b = (re.sub(r"\D", "", x) for x in (value, low, high))
    if not (v and a and b):
        return None
    return int(a) <= int(v) <= int(b)


def batch_scope(product: dict, record: dict) -> tuple[str, list[str]]:
    """in_scope, batch_excluded or batch_unknown, from the notice's serial / lot / date-code limits."""
    limits = record.get("product_identifiers", {}).get("batches") or []
    if not limits:
        return "in_scope", []
    batch = (product.get("batch") or "").strip()
    if not batch:
        return "batch_unknown", [f"the notice covers only some units ({limits[0][:120]})"]
    for text in limits:
        for low, high in RANGE.findall(locales.fold(text)):
            inside = _in_range(batch, low, high)
            if inside is True:
                return "in_scope", [f"batch {batch} is inside {low}–{high}"]
            if inside is False:
                return "batch_excluded", [f"batch {batch} is outside {low}–{high}"]
        if locales.comparable_model(batch) and locales.comparable_model(batch) in locales.comparable_model(text):
            return "in_scope", [f"the notice lists batch {batch}"]
    return "batch_unknown", [f"couldn't tell whether batch {batch} is covered ({limits[0][:120]})"]


def check(product: dict, record: dict, market: str | None) -> dict:
    t, reasons = tier(product, record)
    scope, more = ("not_applicable", []) if t in ("none", "lookalike") else batch_scope(product, record)
    local = is_local(record.get("jurisdiction"), record.get("affected_markets"), market)
    would_change = []
    if t == "unresolved":
        would_change.append("the model number printed on the product's label")
    if scope == "batch_unknown":
        would_change.append("the serial, lot or date code on the shopper's unit")
    if t in ("exact", "variant") and not local:
        would_change.append(f"whether the {market or 'local'} version is the same model and batch (importer, "
                            "model suffix, local notice)")
    if t in ("variant", "suspected_rebrand", "family_named"):
        would_change.append("a person comparing the exact model code and photos with the notice")
    return {"tier": t, "scope": scope, "local": local, "reasons": reasons + more, "would_change": would_change}
