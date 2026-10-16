"""OECD GlobalRecalls: the regulators' own notices (ACCC Australia, CAA Japan, KATS Korea, CPSO Singapore, BSMI Taiwan,
ASEAN) behind an open JSON service. The live path to Australian and Korean recalls, since productsafety.gov.au refuses
automated requests. Each record keeps its country as its jurisdiction, so the scope check can tell a local notice
from a foreign one. Singapore and ASEAN feeds stopped in 2022 (stated in the coverage list).
"""
import asyncio

from engine.sources import normalizer, policy
from engine.sources.adapters._http import Base
from engine.sources.base import SourceQuery, SourceRecord, now, payload_hash

API = "https://globalrecalls.oecd.org/ws"
AUTHORITIES = {"AU": "ACCC", "JP": "CAA", "KR": "KATS", "SG": "CPSO", "TW": "BSMI", "MY": "ASEAN", "ID": "ASEAN",
               "TH": "ASEAN", "PH": "ASEAN", "VN": "ASEAN"}
LINK_HOSTS = {"://preprod.productsafety.gov.au/": "://www.productsafety.gov.au/"}
MAX_DETAILS = 8


def notice_url(raw: dict) -> str:
    url = raw.get("extUrl") or raw.get("uri") or ""
    for old, new in LINK_HOSTS.items():
        url = url.replace(old, new)
    return url


def to_record(raw: dict, retrieved_at) -> SourceRecord:
    country = raw.get("countryId") or ""
    title = raw.get("product.name") or ""
    description = " ".join(x for x in (raw.get("product.modelAndVolume"), raw.get("product.desc")) if x)
    hazard, remedy = raw.get("hazard") or "", raw.get("action") or ""
    brands = [raw.get("manufacturer.name"), raw.get("distributor.name")]
    text = f"{title} {description}"
    ids = normalizer.identifiers([b for b in brands if b], text, title=title)
    if raw.get("gtin"):
        ids["gtins"] = list(dict.fromkeys(ids["gtins"] + [str(raw["gtin"])]))
    published = normalizer.to_datetime(raw.get("date"))
    return SourceRecord(
        source="oecd_globalrecalls", record_id=f"oecd:{country}:{raw.get('id')}", source_url=notice_url(raw),
        record_type="recall_notice", raw_payload_hash=payload_hash(raw), event_at=None,
        source_published_at=published, source_updated_at=None, retrieved_at=retrieved_at,
        product_identifiers=ids, claims=normalizer.recall_claims(title, hazard, remedy, ids["models"], "recall", text),
        title=title, hazard=hazard, remedy=remedy, jurisdiction=country, affected_markets=[country] if country else [],
        language=(raw.get("languageId") or "en").lower(), original_text=normalizer.excerpt(description, width=4000),
        legal_scope="recall", publication_timezone="", authority=AUTHORITIES.get(country, country),
        attribution="Source: OECD GlobalRecalls, from the national regulator's notice")


class Adapter(Base):
    def countries(self, query: SourceQuery) -> list[str]:
        """The query's own source country when given; otherwise every JAPAC country this portal carries."""
        if query.source_country:
            return [query.source_country] if query.source_country in AUTHORITIES else []
        return list(AUTHORITIES)

    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        terms = [t for t in (policy.clean_term(query.model), policy.clean_term(query.brand)) if t]
        countries = self.countries(query)
        if not terms or not countries:
            return []
        where = " OR ".join(f"country-were-recalled:{c}" for c in countries)
        results: list[dict] = []
        for term in terms:  # the model number first; the brand only if the model found nothing
            q = f"{term} ({where})"
            if query.as_of:
                q += f" AND date LE {query.as_of.date().isoformat()}"
            page = await self.json(f"{API}/search.xqy", {"q": q, "start": 0, "end": 20, "lang": "en", "uiLang": "en"})
            results = sorted(page.get("results") or [], key=lambda r: r.get("date") or "", reverse=True)[:MAX_DETAILS]
            if results:
                break

        async def detail(uri: str) -> dict:
            body = await self.json(f"{API}/getrecall.xqy", {"uri": uri, "uiLang": "en"})
            return body.get("recall") or {}

        details = await asyncio.gather(*(detail(r["uri"]) for r in results if r.get("uri")), return_exceptions=True)
        retrieved = now()
        records = [to_record(d, retrieved) for d in details if isinstance(d, dict) and d.get("id")]
        if query.as_of:
            records = [r for r in records if r.source_published_at and r.source_published_at <= query.as_of]
        return records
