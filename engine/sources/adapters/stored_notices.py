"""SafeShelf's stored copy of official notices (the recalls table: CPSC, ACCC, CAA, KATS, CPSO, BSMI, ASEAN, and India's
CCPA orders and BIS raids), loaded by data/load_*.py from the regulators' own sources. Answers are "checked_cache"
with each authority's newest notice date as its freshness, so a shopper sees how current the copy is.
"""
import asyncio
import json
import re

from engine.normalize import norm_brand
from engine.sources import normalizer, policy
from engine.sources.adapters._http import Base
from engine.sources.base import SourceQuery, SourceRecord, now, payload_hash

JURISDICTION = {"CPSC": "US", "ACCC": "AU", "CAA": "JP", "KATS": "KR", "CPSO": "SG", "BSMI": "TW", "CCPA": "IN",
                "BIS": "IN"}
ASEAN = {"Indonesia": "ID", "Malaysia": "MY", "Philippines": "PH", "Thailand": "TH", "Viet Nam": "VN"}
RECORD_TYPE = {"recall_order": "recall_notice", "seizure": "seizure", "safety_notice": "safety_notice",
               "penalty": "safety_notice", "other": "safety_notice"}
MAX_ROWS = 40


def jurisdiction(row: dict) -> str:
    if row["authority"] == "ASEAN":
        return ASEAN.get((row["scope_json"] or {}).get("Country") or "", "ASEAN")
    return JURISDICTION.get(row["authority"], row["authority"])


def to_record(row: dict, retrieved_at, source_id: str, read_models: list[str] | None = None) -> SourceRecord:
    """read_models: model numbers read earlier from the notice (photo captions, or Gemini's cached reading in
    engine/recalls.py), for stored CPSC rows whose Model fields are empty."""
    scope = row["scope_json"] or {}
    products = scope.get("Products") or []
    text = " ".join([row["title"] or "", scope.get("Description") or "", scope.get("Summary") or "",
                     *[f"{p.get('Name') or ''} {p.get('Model') or ''} {p.get('Description') or ''}" for p in products]])
    named = [p.get("Model") for p in products if p.get("Model")] + list(read_models or [])
    brands = [m.get("Name") for m in scope.get("Manufacturers") or []] + \
             [m.get("Name") for m in scope.get("Importers") or []]
    ids = normalizer.identifiers(brands, text, models=named)
    kind = RECORD_TYPE.get(scope.get("Kind") or "", "recall_notice")
    hazard = row.get("hazard") or ""
    remedy = scope.get("Action") or ""
    published = normalizer.to_datetime(scope.get("Posted") or row["notice_date"])
    where = jurisdiction(row)
    return SourceRecord(
        source=source_id, record_id=row["id"], source_url=row["url"] or "", record_type=kind,
        raw_payload_hash=payload_hash({"id": row["id"], "title": row["title"], "scope": scope}),
        event_at=normalizer.to_datetime(row["notice_date"]) if scope.get("Posted") else None,
        source_published_at=published, source_updated_at=None, retrieved_at=retrieved_at, product_identifiers=ids,
        claims=normalizer.recall_claims(row["title"] or "", hazard, remedy, ids["models"],
                                        "recall" if kind == "recall_notice" else kind, text),
        title=row["title"] or "", hazard=hazard, remedy=remedy, jurisdiction=where, affected_markets=[where],
        language="en", original_text=normalizer.excerpt(text, width=4000),
        legal_scope=scope.get("Kind") or "recall", authority=row["authority"], mode="cache",
        attribution=f"Stored copy of the {row['authority']} notice")


def query_rows(query: SourceQuery, authorities: list[str] | None) -> tuple[list[dict], dict]:
    """Notices naming the model (anywhere) or the brand (title, or scope for longer names); newest first."""
    from engine import recalls, store

    model, brand = policy.clean_term(query.model), policy.clean_term(query.brand)
    where, params = [], []
    if model and len(re.sub(r"\W", "", model)) >= 3:
        where.append("(title ILIKE %s OR scope_json::text ILIKE %s)")
        params += [f"%{model}%", f"%{model}%"]
    if brand and len(norm_brand(brand)) >= 3:
        where.append("(title ILIKE %s OR scope_json::text ILIKE %s)")
        params += [f"%{brand}%", f"%{brand}%"]
    elif brand and len(norm_brand(brand)) == 2:  # LG, HP: whole word in the title only
        where.append("title ~ %s")
        params.append(r"\m" + re.escape(brand) + r"\M")
    if not where:
        return [], {}
    sql = f"SELECT id, authority, notice_date, title, hazard, scope_json, url FROM recalls WHERE ({' OR '.join(where)})"
    if authorities:
        sql += " AND authority = ANY(%s)"
        params.append(authorities)
    if query.as_of:
        sql += " AND notice_date <= %s"
        params.append(query.as_of.date())
    sql += f" ORDER BY notice_date DESC NULLS LAST LIMIT {MAX_ROWS}"
    rows = store.conn().execute(sql, params).fetchall()
    fresh = store.conn().execute(
        "SELECT authority, max(notice_date) AS newest FROM recalls" +
        (" WHERE authority = ANY(%s)" if authorities else "") + " GROUP BY authority",
        [authorities] if authorities else []).fetchall()
    read = store.conn().execute(
        "SELECT source_ref, content FROM evidence WHERE source_type = 'recall_models' AND source_ref = ANY(%s)",
        ([r["id"] for r in rows],)).fetchall() if rows else []
    models = {r["source_ref"]: json.loads(r["content"]).get("models") or [] for r in read}
    for row in rows:
        row["read_models"] = sorted(set(models.get(row["id"], [])) | recalls.caption_models(row["scope_json"] or {}))
    return rows, {r["authority"]: r["newest"].isoformat() if r["newest"] else None for r in fresh}


class Adapter(Base):
    authorities: tuple[str, ...] | None = None

    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        rows, fresh = await asyncio.to_thread(query_rows, query, list(self.authorities or []) or None)
        self.freshness = fresh
        retrieved = now()
        return [to_record(r, retrieved, self.id, r.get("read_models")) for r in rows]
