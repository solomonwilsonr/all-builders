"""M3 step 02: normalise brand, model and units from listing text (SAFESHELF.md 7.2)."""
import re

UNIT_PATTERNS = {
    "power_watts": r"(\d+(?:\.\d+)?)\s*w(?:att)?s?\b",
    "capacity_mah": r"(\d{3,6})\s*mah\b",
    "voltage": r"(\d+(?:\.\d+)?)\s*v(?:olts?)?\b",
}
PORT_PATTERNS = {
    "ports_usb_c": r"(\d)\s*(?:x\s*)?(?:usb[- ]?c|type[- ]?c)\b",
    "ports_usb_a": r"(\d)\s*(?:x\s*)?usb[- ]?a\b",
}
# Tokens that look like model numbers but aren't.
NOT_MODELS = re.compile(
    r"^(USB\d?|USBC|PD\d*|QC\d(\.\d)?|GAN\d?|IPHONE\d*|GALAXY|S\d{1,2}|TYPEC|CE|UL\d*|ETL|FCC|BIS|HDMI\d?|"
    r"\d+(\.\d+)?(W|MAH|V|A|MM|CM|M|IN|INCH|FT|PCS|PACK|K|GB|TB|HZ|MP|MONTHS?|YEARS?|YRS?|DAYS?|HOURS?|HRS?|WEEKS?|ML|L|LTR|LITRE|LITER|G|GM|GMS|KG|OZ|LB|LBS)?)$"
)
MODEL_TOKEN = re.compile(
    r"\b[A-Za-z]{1,6}-?\d{2,6}[A-Za-z0-9-]{0,10}\b"  # A1366, CX-65, VN-65PD, RS76CG8003S9HL
    r"|\b[A-Za-z]{1,6}-[A-Za-z]{0,2}\d{1,6}[A-Za-z0-9]{0,4}\b"  # OD-B7
    r"|\b\d{2,5}[A-Za-z]{1,3}\d{0,3}\b"
    r"|\b[A-Za-z]{1,3}\d(?:PRO|MAX|PLUS|LITE|MINI|ULTRA)\b"  # W5PRO (the CAA notice's 型番), X1MAX
)


def norm_brand(brand: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (brand or "").lower())


def norm_model(model: str | None) -> str:
    """'CX-65' and 'cx 65' are the same model number; 'CX-65' and 'CX-650' are not."""
    return re.sub(r"[^A-Z0-9]", "", (model or "").upper())


# "Convertible 5-in-1", "2 in 1 laptop": a feature, not a model number (it was read as model "IN1").
N_IN_ONE = re.compile(r"\b\d+\s*-?\s*in\s*-?\s*\d+\b", re.IGNORECASE)
# The model number the shop states in its details table: "Item model number ‎RS76CG8003S9HL", "Model Number: A1263".
LABELLED_MODEL = re.compile(r"\b(?:item\s+)?model\s*(?:number|no\.?)\s*[:\-]?[\s\u200e\u200f]*([A-Za-z0-9][A-Za-z0-9\-/.]{2,24})", re.IGNORECASE)


def labelled_model(text: str) -> str:
    """The model number from a 'Model number' label in the page's details, if it looks like one."""
    for match in LABELLED_MODEL.finditer(text or ""):
        model = norm_model(match.group(1))
        if len(model) >= 4 and re.search(r"\d", model) and re.search(r"[A-Z]", model) and not NOT_MODELS.match(model):
            return model
    return ""


def model_candidates(text: str) -> list[str]:
    seen: list[str] = []
    for token in MODEL_TOKEN.findall(N_IN_ONE.sub(" ", text or "")):
        model = norm_model(token)
        if model and not NOT_MODELS.match(model) and model not in seen:
            seen.append(model)
    return seen


# A charger's label gives the mains input ("Input: 100-240V~ 1.5A") before the output ("Output: 20V 3.25A"); the
# product's voltage is the output, so input ratings and voltage ranges are skipped.
INPUT_RATING = re.compile(r"\binput\s*:?\s*.*?(?=\boutput\b|[\n;|]|$)|\b\d+\s*[-–~/]\s*\d+\s*v(?:ac)?\b~?")

COUNT_WORDS = {"single": "1", "one": "1", "dual": "2", "two": "2", "twin": "2", "triple": "3", "three": "3"}


def attributes(text: str) -> dict[str, float | int]:
    lowered = re.sub(r"\b(" + "|".join(COUNT_WORDS) + r")\b", lambda m: COUNT_WORDS[m.group(1)], (text or "").lower())
    lowered = INPUT_RATING.sub(" ", lowered)
    found: dict[str, float | int] = {}
    for name, pattern in {**UNIT_PATTERNS, **PORT_PATTERNS}.items():
        match = re.search(pattern, lowered)
        if match:
            value = float(match.group(1))
            found[name] = int(value) if value.is_integer() else value
    return found


def normalise(listing: dict) -> dict:
    """Listing fields in, a fingerprint's identifier part out. Explicit fields win over text parsing."""
    text = " ".join(str(listing.get(k) or "") for k in ("title", "description", "page_text"))
    attrs = attributes(text)
    attrs.update({k: v for k, v in (listing.get("attributes") or {}).items() if v is not None})
    candidates = model_candidates(listing.get("title") or text)
    # Explicit field first, then the shop's own "Model number" label, then the first code in the title.
    model = norm_model(listing.get("model")) or labelled_model(listing.get("page_text") or "") or (candidates[0] if candidates else "")
    return {
        "brand": listing.get("brand") or "",
        "brand_norm": norm_brand(listing.get("brand")),
        "model": listing.get("model") or model,
        "model_norm": model,
        "gtin": (listing.get("gtin") or "").strip() or None,
        "category": listing.get("category") or "",
        "attributes": attrs,
    }


def brand_blind_text(listing: dict, fingerprint: dict) -> str:
    """Text for the embedding with the brand removed, so a rebrand lands next to the original."""
    title = listing.get("title") or ""
    if fingerprint["brand"]:
        title = re.sub(re.escape(fingerprint["brand"]), "", title, flags=re.IGNORECASE)
    attrs = ", ".join(f"{k}={v}" for k, v in sorted(fingerprint["attributes"].items()))
    visual = listing.get("visual_features") or {}
    looks = ", ".join(f"{k}={v}" for k, v in sorted(visual.items()))
    return f"{fingerprint['category']}. {title.strip()}. {attrs}. {looks}".strip()


# Product categories from a listing title (catalog loader and Catalog Scan).
CATEGORIES = {
    "usb_charger": r"wall charger|usb[- ]?c charger|fast charger|gan charger|charging block|charger block|mobile charger",
    "power_bank": r"power ?bank|portable charger|battery pack",
    "heated_blanket": r"heated blanket|electric blanket|heated throw",
    "space_heater": r"space heater|room heater|fan heater|heater",
    "extension_cord": r"extension cord|extension board|power strip|surge protector|spike guard",
    "television": r"smart tv|led tv|4k tv|television|uhd tv",
}
# Clear accessory words only: real chargers say "compatible with iPhone" or "with cable", so those stay in.
ACCESSORY = re.compile(r"\b(mount|stand|remote|cover|case|bag|pouch|bracket|antenna|screen protector|skin|holder|"
                       r"sticker|organi[sz]er|wall plate|dust plug)\b", re.IGNORECASE)


def category_of(title: str) -> str | None:
    if ACCESSORY.search(title or ""):
        return None
    return next((c for c, p in CATEGORIES.items() if re.search(p, title or "", re.IGNORECASE)), None)
