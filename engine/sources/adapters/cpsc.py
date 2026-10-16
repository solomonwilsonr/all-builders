"""U.S. CPSC recalls, live from the documented REST API (saferproducts.gov/RestWebServices/Recall).

A global upstream signal for JAPAC shoppers: a CPSC recall of the same model is evidence to check, never a local
confirmed recall by itself. CPSC puts model numbers in the description more often than in the Model field, so the
model is searched in the description and the brand in the title, in parallel.
"""
import asyncio

from engine.sources import normalizer, policy
from engine.sources.adapters._http import Base
from engine.sources.base import SourceQuery, SourceRecord, now, payload_hash

API = "https://www.saferproducts.gov/RestWebServices/Recall"
MAX_RECORDS = 25


def to_record(raw: dict, retrieved_at) -> SourceRecord:
    products = raw.get("Products") or []
    title = raw.get("Title") or ""
    description = raw.get("Description") or ""
    hazard = "; ".join(h.get("Name") or "" for h in raw.get("Hazards") or [])
    remedy = "; ".join(r.get("Name") or "" for r in raw.get("Remedies") or [])
    named = [p.get("Model") or "" for p in products if p.get("Model")]
    text = " ".join([title, description, *[f"{p.get('Name') or ''} {p.get('Description') or ''}" for p in products]])
    brands = [m.get("Name") for m in raw.get("Manufacturers") or []] + [m.get("Name") for m in raw.get("Importers") or []]
    ids = normalizer.identifiers(brands, text, models=[m for p in named for m in normalizer.models_in(f"model {p}")]
                                 or named)
    ids["upcs"] = [u.get("UPC") for u in raw.get("ProductUPCs") or [] if u.get("UPC")]
    published = normalizer.to_datetime(raw.get("RecallDate"))
    return SourceRecord(
        source="cpsc", record_id=f"cpsc:{raw.get('RecallNumber') or raw.get('RecallID')}",
        source_url=raw.get("URL") or "", record_type="recall_notice", raw_payload_hash=payload_hash(raw),
        event_at=None, source_published_at=published,
        source_updated_at=normalizer.to_datetime(raw.get("LastPublishDate")), retrieved_at=retrieved_at,
        product_identifiers=ids,
        claims=normalizer.recall_claims(title, hazard, remedy, ids["models"], "recall", text),
        title=title, hazard=hazard, remedy=remedy, jurisdiction="US", affected_markets=["US"], language="en",
        original_text=normalizer.excerpt(description, width=4000), legal_scope="recall",
        publication_timezone="America/New_York", authority="CPSC",
        attribution="Source: U.S. CPSC recalls API")


class Adapter(Base):
    async def _search(self, params: dict) -> list[dict]:
        rows = await self.json(API, {"format": "json", **params})
        return [r for r in rows or [] if r.get("RecallNumber")]

    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        model, brand = policy.clean_term(query.model), policy.clean_term(query.brand)
        if not (model or brand):
            return []
        calls = []
        if model:
            calls.append(self._search({"RecallDescription": model}))
        if brand:
            calls.append(self._search({"RecallTitle": brand}))
        found: dict[str, dict] = {}
        for rows in await asyncio.gather(*calls):
            for row in rows:
                found.setdefault(str(row["RecallNumber"]), row)
        retrieved = now()
        rows = sorted(found.values(), key=lambda r: r.get("RecallDate") or "", reverse=True)[:MAX_RECORDS]
        records = [to_record(r, retrieved) for r in rows]
        if query.as_of:  # historical replay: only what was public by then
            records = [r for r in records if r.source_published_at and r.source_published_at <= query.as_of]
        return records
