"""Source authenticity and claim support (plan v2.2 J1, J3 step 2).

Authenticity: the record has a stable ID and its link is on one of the issuing authority's official domains. A real
URL alone is not claim verification: the claim's excerpt must also appear in the record's own text. A forged or
look-alike regulator domain ("cpsc-gov.recalls.example") is "unofficial_domain" and can't support anything.
"""
import re

from engine import locales
from engine.sources import policy, registry

# Official domains by authority, for stored rows whose source id is the multi-country store.
AUTHORITY_DOMAINS = {
    "CPSC": ["cpsc.gov", "saferproducts.gov"], "ACCC": ["productsafety.gov.au", "recalls.gov.au", "accc.gov.au"],
    "CAA": ["caa.go.jp"], "METI": ["meti.go.jp"], "NITE": ["nite.go.jp"], "KATS": ["safetykorea.kr", "kats.go.kr"],
    "CPSO": ["consumerproductsafety.gov.sg", "enterprisesg.gov.sg"], "BSMI": ["bsmi.gov.tw"],
    "CCPA": ["pib.gov.in", "doca.gov.in"], "BIS": ["pib.gov.in", "bis.gov.in"], "MBIE": ["productsafety.govt.nz"],
    "OECD": ["oecd.org"], "EU Safety Gate": ["ec.europa.eu"],
}
# OECD stores the notice link of the national regulator; ASEAN members' regulators publish on their own domains.
OECD_EXTRA = ["oecd.org", "productsafety.gov.au", "recalls.gov.au", "caa.go.jp", "go.kr", "gov.sg", "gov.tw",
              "go.id", "gov.my", "go.th", "gov.ph", "gov.vn", "asean.org"]


def official_domains(source_id: str, authority: str | None) -> list[str]:
    try:
        domains = list(registry.source(source_id).get("domains") or [])
    except KeyError:
        domains = []
    domains += AUTHORITY_DOMAINS.get(authority or "", [])
    if source_id in ("oecd_globalrecalls", "stored_notices") and (authority in ("ACCC", "CAA", "KATS", "CPSO", "BSMI",
                                                                                "ASEAN") or source_id ==
                                                                   "oecd_globalrecalls"):
        domains += OECD_EXTRA
    return list(dict.fromkeys(d.removeprefix("www.") for d in domains))


def authenticity(record: dict) -> tuple[str, str]:
    """(status, reason) for one source record (SourceRecord.to_dict() shape)."""
    if not record.get("record_id"):
        return "missing_reference", "no stable record ID"
    url = record.get("source_url") or ""
    if not url:
        return "missing_reference", "no link to the official record"
    ok, why = policy.allowed_url(url, official_domains(record.get("source", ""), record.get("authority")))
    if not ok:
        return "unofficial_domain", why
    if record.get("mode") == "live" and record.get("source") not in ("research_fallback", "eu_safety_gate",
                                                                    "nz_product_safety"):
        return "authentic", "read live from the official source by SafeShelf"
    return "official_domain", "official link and record ID; read from the stored copy or by browsing"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", locales.fold(text or "").lower()).strip()


def supports(excerpt: str, record: dict) -> str:
    """Does the record's own text contain the claim's excerpt? Exact containment after folding, in any of the record's
    parts or the title and text together: an LLM may propose a claim, but only text really in the record supports it."""
    if not excerpt:
        return "not_checked"
    parts = [str(record.get(k) or "") for k in ("title", "hazard", "remedy", "original_text")]
    haystacks = [_norm(p) for p in parts] + [_norm(f"{parts[0]} {parts[3]}"), _norm(" ".join(parts))]
    needle = _norm(excerpt)
    if needle and any(needle in h or needle[:120] in h for h in haystacks):
        return "supported"
    return "unsupported"
