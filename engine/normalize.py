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
    r"\d+(\.\d+)?(W|MAH|V|A|MM|CM|IN|FT|PCS|PACK|K|GB|TB|HZ)?)$"
)
MODEL_TOKEN = re.compile(
    r"\b[A-Za-z]{1,6}-?\d{2,6}[A-Za-z0-9-]{0,6}\b"  # A1366, CX-65, VN-65PD
    r"|\b[A-Za-z]{1,6}-[A-Za-z]{0,2}\d{1,6}[A-Za-z0-9]{0,4}\b"  # OD-B7
    r"|\b\d{2,5}[A-Za-z]{1,3}\d{0,3}\b"
)


def norm_brand(brand: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (brand or "").lower())


def norm_model(model: str | None) -> str:
    """'CX-65' and 'cx 65' are the same model number; 'CX-65' and 'CX-650' are not."""
    return re.sub(r"[^A-Z0-9]", "", (model or "").upper())


def model_candidates(text: str) -> list[str]:
    seen: list[str] = []
    for token in MODEL_TOKEN.findall(text or ""):
        model = norm_model(token)
        if model and not NOT_MODELS.match(model) and model not in seen:
            seen.append(model)
    return seen


COUNT_WORDS = {"single": "1", "one": "1", "dual": "2", "two": "2", "twin": "2", "triple": "3", "three": "3"}


def attributes(text: str) -> dict[str, float | int]:
    lowered = re.sub(r"\b(" + "|".join(COUNT_WORDS) + r")\b", lambda m: COUNT_WORDS[m.group(1)], (text or "").lower())
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
    model = norm_model(listing.get("model")) or (candidates[0] if candidates else "")
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
