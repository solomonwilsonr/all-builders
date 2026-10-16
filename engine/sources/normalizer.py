"""Turns a regulator's own wording into the shared record shape: model numbers, batches and GTINs named in the notice,
dates, and the claims the record supports. Code only: a notice whose models code can't read keeps an empty list, and
the scope check then treats it as "family named, no models" (needs a person), never as a match.
"""
import re
from datetime import UTC, date, datetime

from engine import locales as locale

# "model number ZHX-PB22", "model numbers A1, A2 and A3", "Model: GCV22-F", "part code WMPB10A", "SKU 12345".
EN_MODEL_LEAD = re.compile(
    r"\b(?:model|item|part|style|sku|catalog(?:ue)?|product)\s*(?:numbers?|nos?\.?|codes?|#)?\s*[:#]?\s*"
    r"((?:[\"“”']?[A-Z0-9][A-Z0-9\-/.]*\d[A-Z0-9\-/.]*[\"“”']?(?:\s*(?:,|;|and|or|&)\s*)?)+)", re.IGNORECASE)
# Japanese notices: 型番：W5PRO, 型式 ABC-12, 品番: X-1, 製品番号
JA_MODEL_LEAD = re.compile(r"(?:型番|型式|品番|製品番号|機種名)\s*[:：]?\s*([^\n、。]+)")
TOKEN = re.compile(r"[A-Z0-9][A-Z0-9\-/.]*\d[A-Z0-9\-/.]*|[A-Z0-9]*\d[A-Z0-9\-/.]*[A-Z][A-Z0-9\-/.]*", re.IGNORECASE)
NOT_MODEL = re.compile(r"^(?:\d{1,3}(?:[.,]\d+)?(?:MAH|W|V|A|MM|CM|KG|G|L|ML|IN)?|\d{4}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|"
                       r"(?:19|20)\d{2}-\d{2}(?:-\d{2})?)$", re.IGNORECASE)
BATCH_LEAD = re.compile(
    r"\b(?:serial numbers?|lot (?:numbers?|codes?)|batch (?:numbers?|codes?)|date codes?|production codes?|"
    r"manufactur\w+ dates?)\b[^.\n]{0,160}", re.IGNORECASE)
JA_BATCH_LEAD = re.compile(r"(?:製造番号|ロット番号|ロット|シリアル番号|製造年月|製造期間)\s*[:：]?\s*([^\n。]+)")
CORRECTION = re.compile(r"\b(?:correction|corrected|update[d]?|amended|revised|retract\w*|withdrawn)\b|訂正|更新|取り下げ|撤回",
                        re.IGNORECASE)


def to_datetime(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    parsed = locale.parse_date(str(value))
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=UTC) if parsed else None


def models_in(text: str | None) -> list[str]:
    """Model numbers a notice names, as written (deduplicated by their comparable form)."""
    text = text or ""
    found: list[str] = []
    for lead in EN_MODEL_LEAD.finditer(text):
        found += TOKEN.findall(lead.group(1))
    for lead in JA_MODEL_LEAD.finditer(locale.fold(text)):
        found += TOKEN.findall(lead.group(1))
    out, seen = [], set()
    for token in found:
        token = token.strip("\"“”'.,-/")
        key = locale.comparable_model(token)
        if len(key) >= 3 and not NOT_MODEL.match(token) and key not in seen:
            seen.add(key)
            out.append(token)
    return out


def batches_in(text: str | None) -> list[str]:
    """The sentences that limit a notice to some serials, lots or dates (kept as text for the scope check)."""
    text = text or ""
    out = [m.group(0).strip() for m in BATCH_LEAD.finditer(text)]
    out += [m.group(0).strip() for m in JA_BATCH_LEAD.finditer(locale.fold(text))]
    return list(dict.fromkeys(out))[:6]


def gtins_in(text: str | None) -> list[str]:
    return [g for g in re.findall(r"(?<!\d)(\d{8}|\d{12,14})(?!\d)", locale.fold(text or "")) if locale.gtin_valid(g)]


def title_codes(title: str) -> list[str]:
    """Model codes written in a notice title without a "model" label ("Anker 334 MagGo ... A1642")."""
    from engine.normalize import model_candidates
    return [m for m in model_candidates(locale.fold(title or "")) if re.search(r"[A-Z]", m) and len(m) >= 4]


def identifiers(brands: list[str], text: str, models: list[str] | None = None, title: str = "") -> dict:
    found = list(dict.fromkeys((models or []) + models_in(text)))
    if not found and title:  # only when the notice labels no model: the title's own codes
        found = title_codes(title)
    return {"brands": [b for b in dict.fromkeys(brands) if b],
            "models": found,
            "gtins": list(dict.fromkeys(gtins_in(text))), "batches": batches_in(text)}


def is_correction(*texts: str) -> bool:
    return any(CORRECTION.search(t or "") for t in texts)


def excerpt(text: str | None, around: str | None = None, width: int = 240) -> str:
    """A short exact excerpt (never paraphrased), centred on `around` when it appears."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""
    at = text.lower().find((around or "").lower()) if around else -1
    start = max(0, at - width // 3) if at >= 0 else 0
    return text[start:start + width]


def recall_claims(title: str, hazard: str, remedy: str, models: list[str], record_type: str, text: str) -> list[dict]:
    """The atomic claims an official notice supports, each with its exact excerpt."""
    claims = [{"claim_type": record_type, "text": title, "excerpt": excerpt(title)}]
    if hazard:
        claims.append({"claim_type": "hazard", "text": hazard, "excerpt": excerpt(hazard)})
    if models:
        claims.append({"claim_type": "affected_models", "text": ", ".join(models),
                       "excerpt": excerpt(text, models[0], width=160)})
    if remedy:
        claims.append({"claim_type": "remedy", "text": remedy, "excerpt": excerpt(remedy)})
    return claims
