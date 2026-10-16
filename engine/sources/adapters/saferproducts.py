"""SaferProducts.gov public incident reports (CPSC's OData service, which needs a free application key).

Runs only when SAFERPRODUCTS_API_KEY is set (registry access_status key_required). The service root answers 401
without credentials (checked 16 Oct 2026); confirm the exact auth scheme when the key is issued. Incident reports are
consumer allegations: they become "incident_report" records and can at most support a potential concern.
"""
import os

from engine.sources import normalizer, policy
from engine.sources.adapters._http import Base
from engine.sources.base import NOT_CONFIGURED, SourceFailure, SourceQuery, SourceRecord, now, payload_hash

API = "https://www.saferproducts.gov/webapi/Cpsc.Cpsrms.Web.Api.svc/IncidentReports"


def to_record(raw: dict, retrieved_at) -> SourceRecord:
    text = " ".join(str(raw.get(k) or "") for k in ("ProductDescription", "IncidentDescription"))
    ids = normalizer.identifiers([raw.get("ProductBrandName") or ""], text,
                                 models=[raw["ProductModelName"]] if raw.get("ProductModelName") else [])
    return SourceRecord(
        source="saferproducts", record_id=f"saferproducts:{raw.get('IncidentReportNumber') or raw.get('Id')}",
        source_url=f"https://www.saferproducts.gov/PublicSearch/Detail?ReportId={raw.get('IncidentReportId', '')}",
        record_type="incident_report", raw_payload_hash=payload_hash(raw),
        event_at=normalizer.to_datetime(raw.get("IncidentDate")),
        source_published_at=normalizer.to_datetime(raw.get("IncidentReportPublicationDate")),
        source_updated_at=None, retrieved_at=retrieved_at, product_identifiers=ids,
        claims=[{"claim_type": "incident_report", "text": normalizer.excerpt(text, width=300),
                 "excerpt": normalizer.excerpt(text)}],
        title=(raw.get("ProductDescription") or "")[:120], jurisdiction="US", affected_markets=["US"],
        original_text=normalizer.excerpt(text, width=1200), legal_scope="consumer incident report (allegation)",
        authority="CPSC", attribution="Source: SaferProducts.gov public incident reports")


class Adapter(Base):
    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        key = os.environ.get(self.entry.get("key_env") or "SAFERPRODUCTS_API_KEY")
        if not key:
            raise SourceFailure(NOT_CONFIGURED, "needs a SaferProducts.gov application key")
        model, brand = policy.clean_term(query.model), policy.clean_term(query.brand)
        term = (model or brand).replace("'", "''")
        if not term:
            return []
        field = "ProductModelName" if model else "ProductBrandName"
        body = await self.json(API, {"$filter": f"substringof('{term}',{field})", "$top": "25",
                                     "$format": "json", "api_key": key})
        rows = body.get("value") or body.get("d", {}).get("results") or []
        retrieved = now()
        return [to_record(r, retrieved) for r in rows]
