"""Language and local-identifier helpers for JAPAC evidence (plan v2.2 section 2A).

Original-language text is kept as published; these helpers only read it. A Japanese model string is compared after
NFKC folding (full-width "ＷＳ－１２" equals "WS-12") but stored exactly as written, and a machine translation is
always marked as one.
"""
import re
import unicodedata
from datetime import date

SCRIPTS = [("ja", re.compile(r"[぀-ヿ]")),              # kana: Japanese even when kanji are present
           ("ko", re.compile(r"[가-힯]")),
           ("hi", re.compile(r"[ऀ-ॿ]")),
           ("ta", re.compile(r"[஀-௿]")),
           ("th", re.compile(r"[฀-๿]")),
           ("zh", re.compile(r"[一-鿿]"))]
ERAS = {"令和": 2018, "平成": 1988, "昭和": 1925}  # era year 1 = base + 1
JA_DATE = re.compile(r"(令和|平成|昭和)?\s*(元|\d{1,4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")
EN_MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                         "dec"], 1)}
DMY = re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(\d{4})\b")
MDY = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s+(\d{4})\b")
ISO = re.compile(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)")
BIS_R = re.compile(r"\bR-?\d{8}\b", re.IGNORECASE)
ISI_LICENCE = re.compile(r"\bCM/L-?\d{7,10}\b", re.IGNORECASE)
PSE = re.compile(r"\bPSE\b|電気用品安全法|ＰＳＥ")


def fold(text: str | None) -> str:
    """NFKC: full-width letters and digits become ASCII, half-width kana become full-width."""
    return unicodedata.normalize("NFKC", text or "")


def comparable_model(model: str | None) -> str:
    """For matching only: folded, upper case, letters and digits. 'ＷＳ－１２' and 'ws 12' -> 'WS12'."""
    return re.sub(r"[^A-Z0-9]", "", fold(model).upper())


def detect_language(text: str | None) -> str:
    text = text or ""
    for code, pattern in SCRIPTS:
        if pattern.search(text):
            return code
    return "en"


def parse_date(text: str | None) -> date | None:
    """ISO, Japanese (2026年09月24日, 令和8年10月16日), '26 MAR 2025' and 'March 26, 2025'. None if unreadable."""
    text = fold(text).strip()
    if not text:
        return None
    if m := ISO.search(text):
        return _safe(int(m[1]), int(m[2]), int(m[3]))
    if m := JA_DATE.search(text):
        year = 1 if m[2] == "元" else int(m[2])
        if m[1]:
            year += ERAS[m[1]]
        return _safe(year, int(m[3]), int(m[4]))
    if m := DMY.search(text):
        month = EN_MONTHS.get(m[2][:3].lower())
        return _safe(int(m[3]), month, int(m[1])) if month else None
    if m := MDY.search(text):
        month = EN_MONTHS.get(m[1][:3].lower())
        return _safe(int(m[3]), month, int(m[2])) if month else None
    return None


def _safe(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except (ValueError, TypeError):
        return None


def gtin_valid(code: str) -> bool:
    """GS1 check digit for GTIN-8/12/13/14 (JAN codes are GTIN-13 starting 45 or 49)."""
    digits = re.sub(r"\D", "", code or "")
    if len(digits) not in (8, 12, 13, 14):
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def is_jan(code: str) -> bool:
    digits = re.sub(r"\D", "", code or "")
    return len(digits) in (8, 13) and digits[:2] in ("45", "49") and gtin_valid(digits)


def local_identifiers(text: str | None) -> dict:
    """Identifiers printed in a listing or label: BIS R-numbers, ISI licences, JAN/GTIN codes, a PSE mark claim."""
    text = fold(text)
    gtins = [g for g in re.findall(r"(?<!\d)(\d{8}|\d{12,14})(?!\d)", text) if gtin_valid(g)]
    out = {"bis_r": sorted({m.upper().replace("R", "R-", 1).replace("--", "-") for m in BIS_R.findall(text)}),
           "isi_licence": sorted({m.upper() for m in ISI_LICENCE.findall(text)}),
           "jan": sorted({g for g in gtins if is_jan(g)}),
           "gtin": sorted(set(gtins)),
           "pse_claimed": bool(PSE.search(text))}
    return {k: v for k, v in out.items() if v}


def translated(text: str, translation: str | None, source_lang: str, target_lang: str = "en") -> dict:
    """A translated field, always marked machine-made and kept next to (never instead of) the original."""
    return {"original": text, "original_lang": source_lang, "text": translation, "lang": target_lang,
            "machine_translation": True} if translation else {"original": text, "original_lang": source_lang}
