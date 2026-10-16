"""ACCC Product Safety Australia recalls from its official RSS feed.

The parser is complete and tested on the feed's format, but productsafety.gov.au answers 403 to SafeShelf's network
(checked 16 Oct 2026), so the registry marks the source "blocked" and Australian notices come through OECD
GlobalRecalls. Flip access_status to "verified" once the feed answers from the deployment's egress.
"""
import xml.etree.ElementTree as ET

from engine.sources import normalizer, policy
from engine.sources.adapters._http import Base
from engine.sources.base import ERROR, SourceFailure, SourceQuery, SourceRecord, now, payload_hash

FEED = "https://www.productsafety.gov.au/rss/recalls"


def parse_feed(xml_text: str, retrieved_at) -> list[SourceRecord]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        raise SourceFailure(ERROR, "the feed was not valid XML") from None
    records = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        published = normalizer.to_datetime(item.findtext("pubDate"))
        ids = normalizer.identifiers([], f"{title} {description}", title=title)
        records.append(SourceRecord(
            source="au_accc", record_id=f"accc:{guid.rstrip('/').rsplit('/', 1)[-1]}", source_url=link,
            record_type="recall_notice", raw_payload_hash=payload_hash(f"{title}|{link}|{description}"),
            event_at=None, source_published_at=published, source_updated_at=None, retrieved_at=retrieved_at,
            product_identifiers=ids, claims=normalizer.recall_claims(title, "", "", ids["models"], "recall",
                                                                     description),
            title=title, jurisdiction="AU", affected_markets=["AU"], language="en",
            original_text=normalizer.excerpt(description, width=1200), legal_scope="recall",
            publication_timezone="Australia/Sydney", authority="ACCC",
            attribution="Source: ACCC Product Safety Australia"))
    return records


def matches(record: SourceRecord, query: SourceQuery) -> bool:
    text = f"{record.title} {record.original_text}".lower()
    terms = [t.lower() for t in (policy.clean_term(query.model), policy.clean_term(query.brand)) if t]
    return any(t in text for t in terms)


class Adapter(Base):
    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        response = await self.get(FEED)
        records = [r for r in parse_feed(response.text, now()) if matches(r, query)]
        if query.as_of:
            records = [r for r in records if r.source_published_at and r.source_published_at <= query.as_of]
        return records
