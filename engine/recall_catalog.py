"""Recall Catalog: browse and search every official recall loaded (CPSC, ACCC, CAA, KATS, ...).

    search(params)    -> one page of recalls, newest first, with counts per regulator
    recall(recall_id) -> one recall with its SafeShelf product matches

Only official notices are listed. Safety Radar findings (hazard_signals) are not: they are under review, not recalls.
Database only, no Gemini, so the API does not count these calls against the AI-check limit.
"""
import re
from typing import Any

from engine import store

MAX_PER_PAGE = 50
MAX_QUERY = 100

# Hazard types (the Safety schema's enum) by keyword in the notice's hazard text. Postgres regex syntax (\y is a
# word boundary); hazard_types() converts it for Python. A notice can have several types; none matched = "other".
HAZARD_PATTERNS = {
    "fire_burn": r"fire|burn|overheat|flame|scald|ignit|melt|explo",
    "electric_shock": r"electric|shock|electrocut|creepage|insulation|live part",
    "choking": r"chok|swallow|ingest|aspirat|suffocat|strangul|small part",
    "chemical": r"chemical|toxi|poison|\ylead\y|cadmium|phthalate|formaldehyde|asbestos|carbon monoxide"
                r"|allergen|contamina|mercury",
    "mechanical_injury": r"\yfall|tip.?over|laceration|\ycut|pinch|entrap|crush|collapse|amputat|fractur"
                         r"|sharp edge|break",
}
HAZARD_TYPES = [*HAZARD_PATTERNS, "other"]
_PY_PATTERNS = {k: re.compile(p.replace(r"\y", r"\b"), re.IGNORECASE) for k, p in HAZARD_PATTERNS.items()}

# CPSC notices carry no Country field (OECD GlobalRecalls ones do).
COUNTRY = "coalesce(scope_json->>'Country', CASE WHEN authority = 'CPSC' THEN 'United States' END)"


def hazard_types(hazard: str) -> list[str]:
    found = [k for k, pattern in _PY_PATTERNS.items() if pattern.search(hazard or "")]
    return found or ["other"]


def card(row: dict) -> dict:
    """A recall as the catalog shows it: names and companies flattened, empty fields left out of lists."""
    scope = row["scope_json"] or {}

    def names(key: str) -> list[str]:
        return [n for n in (x.get("Name") for x in scope.get(key) or []) if n]

    return {
        "recall_id": row["id"],
        "authority": row["authority"],
        "country": row["country"],
        "notice_date": row["notice_date"].isoformat() if row["notice_date"] else None,
        "title": row["title"],
        "hazard": row["hazard"] or "",
        "hazard_types": hazard_types(row["hazard"]),
        "products": [{"name": p.get("Name") or "", "model": p.get("Model") or "",
                      "description": p.get("Description") or "", "units": p.get("NumberOfUnits") or ""}
                     for p in scope.get("Products") or []],
        "companies": names("Manufacturers") + names("Importers") + names("Distributors"),
        "images": [{"url": i["URL"], "caption": i.get("Caption") or ""} for i in scope.get("Images") or []
                   if i.get("URL")],
        "action": scope.get("Action") or "",
        "url": row["url"],
        "source": scope.get("Source") or row["authority"],
    }


def filters(params: dict[str, str]) -> tuple[str, list[Any]]:
    """WHERE clause and its arguments from the query string. Raises ValueError for a bad value."""
    where, args = ["TRUE"], []
    q = (params.get("q") or "").strip()
    if len(q) > MAX_QUERY:
        raise ValueError(f"q: at most {MAX_QUERY} characters")
    for word in q.split():
        like = "%" + word.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_") + "%"
        where.append("(title ILIKE %s OR hazard ILIKE %s OR scope_json::text ILIKE %s)")
        args += [like, like, like]
    if params.get("authority"):
        where.append("authority = ANY(%s)")
        args.append([a.strip().upper() for a in params["authority"].split(",") if a.strip()])
    if params.get("country"):
        where.append(f"{COUNTRY} ILIKE %s")
        args.append(params["country"].strip())
    if hazard := params.get("hazard_type"):
        if hazard not in HAZARD_TYPES:
            raise ValueError(f"hazard_type: one of {', '.join(HAZARD_TYPES)}")
        if hazard == "other":
            where.append("NOT coalesce(hazard, '') ~* %s")
            args.append("|".join(HAZARD_PATTERNS.values()))
        else:
            where.append("hazard ~* %s")
            args.append(HAZARD_PATTERNS[hazard])
    for key, op in (("from", ">="), ("to", "<=")):
        if params.get(key):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", params[key]):
                raise ValueError(f"{key}: a date like 2026-01-31")
            where.append(f"notice_date {op} %s")
            args.append(params[key])
    return " AND ".join(where), args


def page_numbers(params: dict[str, str]) -> tuple[int, int]:
    try:
        page, per_page = int(params.get("page") or 1), int(params.get("per_page") or 24)
    except ValueError:
        raise ValueError("page and per_page: whole numbers") from None
    if page < 1 or not 1 <= per_page <= MAX_PER_PAGE:
        raise ValueError(f"page from 1, per_page from 1 to {MAX_PER_PAGE}")
    return page, per_page


def search(params: dict[str, str]) -> dict:
    where, args = filters(params)
    page, per_page = page_numbers(params)
    db = store.conn()
    rows = db.execute(
        f"""SELECT id, authority, {COUNTRY} AS country, notice_date, title, hazard, scope_json, url,
                   count(*) OVER () AS total
            FROM recalls WHERE {where}
            ORDER BY notice_date DESC NULLS LAST, id LIMIT %s OFFSET %s""",
        [*args, per_page, (page - 1) * per_page]).fetchall()
    total = rows[0]["total"] if rows else db.execute(f"SELECT count(*) AS n FROM recalls WHERE {where}", args
                                                     ).fetchone()["n"]
    sources = db.execute(
        f"""SELECT authority, {COUNTRY} AS country, count(*) AS recalls, max(notice_date) AS latest
            FROM recalls GROUP BY 1, 2 ORDER BY 3 DESC""").fetchall()
    return {
        "total": total, "page": page, "per_page": per_page,
        "recalls": [card(r) for r in rows],
        "sources": [{"authority": s["authority"], "country": s["country"], "recalls": s["recalls"],
                     "latest": s["latest"].isoformat() if s["latest"] else None} for s in sources],
        "hazard_types": HAZARD_TYPES,
    }


def recall(recall_id: str) -> dict:
    """Raises KeyError for an unknown recall. Lists SafeShelf products only for an exact model match: a public
    page must not call a product recalled while the match awaits human review."""
    db = store.conn()
    row = db.execute(
        f"SELECT id, authority, {COUNTRY} AS country, notice_date, title, hazard, scope_json, url FROM recalls "
        "WHERE id = %s", (recall_id,)).fetchone()
    if not row:
        raise KeyError(recall_id)
    matches = db.execute(
        """SELECT DISTINCT rp.product_id, p.brand, p.model FROM recall_products rp
           LEFT JOIN products p ON p.id = rp.product_id
           WHERE rp.recall_id = %s AND rp.match_class = 'exact_model' ORDER BY rp.product_id""",
        (recall_id,)).fetchall()
    return {**card(row), "safeshelf_products": [dict(m) for m in matches]}
