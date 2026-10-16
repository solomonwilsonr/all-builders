"""Cross-border intelligence (plan v2.2 workstream E): an official notice in one country -> its affected models,
GTINs and batches -> the same model in another JAPAC country's notices or catalogue -> a verified scope tier.

    candidates(...)  -> pairs of notices from different countries naming the same model of the same brand
    for_product(pid) -> foreign notices that may concern a stored product in its own market

A candidate is "potential_cross_border_match" until the scope check says exact and in scope, then
"verified_affected_model" only for the exact model; owners are told only after a reviewer approves (reviews.py).
Generic words ("5-drawer", "2-burner", "USB-C") are never model numbers.
"""
import re
from datetime import date

from engine import locales, store
from engine.normalize import norm_brand
from engine.sources import normalizer
from engine.sources.adapters.stored_notices import jurisdiction

JAPAC = ("AU", "JP", "KR", "SG", "TW", "MY", "ID", "TH", "PH", "VN", "IN", "NZ")
GENERIC = re.compile(r"^(\d+(-|\s)?(drawer|burner|piece|pack|port|in-?1|seater|tier|light|blade|speed|layer|door|"
                     r"inch|ft|cm|mm|v|w|mah|l)s?|usb-?c|type-?c|led|lcd|hdmi|qi|ac|dc)$", re.IGNORECASE)


def notice_models(row: dict, read: dict[str, list[str]]) -> set[str]:
    scope = row["scope_json"] or {}
    products = scope.get("Products") or []
    text = " ".join([row["title"] or "", scope.get("Description") or "",
                     *[f"{p.get('Name') or ''} {p.get('Model') or ''} {p.get('Description') or ''}" for p in products]])
    found = {m for p in products for m in re.split(r"[,;/]|\band\b", p.get("Model") or "") if m.strip()}
    found |= set(normalizer.models_in(text)) | set(read.get(row["id"], []))
    codes = {locales.comparable_model(m) for m in found if not GENERIC.match(m.strip())}
    return {c for c in codes if len(c) >= 4 and re.search(r"\d", c) and re.search(r"[A-Z]", c)}


CORPORATE = re.compile(r"\b(pty|ltd|limited|inc|llc|co|corp\w*|company|gmbh|k\.?k|japan|australia|america|"
                       r"north|usa|us|international|group|trading|holdings|recalls?)\b\.?", re.IGNORECASE)


def brand_words(row: dict) -> set[str]:
    """Distinctive words of the companies a notice names, plus its title's first word ("Chervon", "EGO", "Baseus")."""
    scope = row["scope_json"] or {}
    names = [m.get("Name") or "" for m in (scope.get("Manufacturers") or []) + (scope.get("Importers") or [])
             + (scope.get("Distributors") or [])]
    names.append((row["title"] or "").split()[0] if row["title"] else "")
    words = {norm_brand(w) for n in names for w in CORPORATE.sub(" ", n).split()}
    return {w for w in words if len(w) >= 3}


def brand_of(row: dict) -> str:
    return " ".join(sorted(brand_words(row)))


def same_brand(a: dict, b: dict) -> bool:
    """Shared company word, or one notice's company named in the other's title."""
    if a["brand_words"] & b["brand_words"]:
        return True
    title_a, title_b = norm_brand(a["title"] or ""), norm_brand(b["title"] or "")
    return any(w in title_b for w in a["brand_words"] if len(w) >= 4) or \
        any(w in title_a for w in b["brand_words"] if len(w) >= 4)


def load_notices(since: str = "2019-01-01") -> list[dict]:
    rows = store.conn().execute(
        "SELECT id, authority, notice_date, title, scope_json, url FROM recalls WHERE notice_date >= %s",
        (since,)).fetchall()
    read = {r["source_ref"]: __import__("json").loads(r["content"]).get("models") or []
            for r in store.conn().execute(
                "SELECT source_ref, content FROM evidence WHERE source_type = 'recall_models'").fetchall()}
    for row in rows:
        row["country"] = jurisdiction(row)
        row["models"] = notice_models(row, read)
        row["brand_words"] = brand_words(row)
        row["brand"] = brand_of(row)
    return [r for r in rows if r["models"]]


def candidates(since: str = "2019-01-01", to_countries: tuple[str, ...] = JAPAC) -> list[dict]:
    """Every pair (earlier notice, later notice in a JAPAC country) sharing a model code. Same brand -> tier
    exact; different brand -> suspected_rebrand (needs a person). Each carries the lead time in days."""
    notices = load_notices(since)
    by_model: dict[str, list[dict]] = {}
    for n in notices:
        for code in n["models"]:
            by_model.setdefault(code, []).append(n)
    out, seen = [], set()
    for code, group in by_model.items():
        if len({n["country"] for n in group}) < 2:
            continue
        group = sorted(group, key=lambda n: n["notice_date"] or date.max)
        first = group[0]
        for later in group[1:]:
            if later["country"] == first["country"] or later["country"] not in to_countries:
                continue
            key = (first["id"], later["id"])
            if key in seen:
                continue
            seen.add(key)
            shared = same_brand(first, later)
            lead = (later["notice_date"] - first["notice_date"]).days if first["notice_date"] and \
                later["notice_date"] else None
            out.append({"model": code, "tier": "exact" if shared else "suspected_rebrand",
                        "status": "potential_cross_border_match",
                        "first": {"record_id": first["id"], "country": first["country"], "authority":
                                  first["authority"], "date": str(first["notice_date"]), "title": first["title"],
                                  "url": first["url"]},
                        "later": {"record_id": later["id"], "country": later["country"], "authority":
                                  later["authority"], "date": str(later["notice_date"]), "title": later["title"],
                                  "url": later["url"]},
                        "lead_days": lead, "needs_person": True})
    return sorted(out, key=lambda c: -(c["lead_days"] or 0))


def for_product(product_id: str) -> list[dict]:
    """Foreign notices naming a stored product's exact model (cross-border signals for its own market)."""
    from engine import investigation, safety
    fp = store.latest_fingerprint(product_id)
    if fp is None:
        raise KeyError(product_id)
    market = safety.market_of_product(product_id)
    product = {"product_id": product_id, "brand": fp["brand"], "model": fp["model"], "gtin": fp.get("gtin"),
               "category": fp.get("category"), "market": market}
    collected = investigation.collect(product, market)
    return [{**m, "status": "verified_affected_model" if m["tier"] == "exact" and m["scope"] == "in_scope"
             else "potential_cross_border_match"}
            for m in collected["matches"] if not m["local"] and m["tier"] in ("exact", "variant", "suspected_rebrand")]
