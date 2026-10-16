"""The Research Agent (a read-only headless browser, research/) as an adapter, for allowlisted official sites with no
API (EU Safety Gate, Product Safety New Zealand). Slower and costlier than an API, so it runs only when the Research
Agent is configured and the investigation asked for depth. What it finds is a lead "for a person to confirm".
"""
import asyncio

from engine.sources import normalizer
from engine.sources.adapters._http import Base
from engine.sources.base import BLOCKED, NOT_CONFIGURED, SourceFailure, SourceQuery, SourceRecord, now, payload_hash

SITE_KEYS = {"eu_safety_gate": "eu", "nz_product_safety": "nz", "au_accc": "accc", "sg_cps": "sg", "cpsc": "cpsc"}
JURISDICTION = {"eu": "EU", "nz": "NZ", "accc": "AU", "sg": "SG", "cpsc": "US"}


class Adapter(Base):
    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        from engine.agents import research

        if not research.RESEARCH_URL:
            raise SourceFailure(NOT_CONFIGURED, "the Research Agent is not configured here")
        site = SITE_KEYS.get(self.id, self.id)
        body = await asyncio.to_thread(research.check, query.brand or "", query.model or "", query.category or "",
                                       [site])
        retrieved, records = now(), []
        for s in body.get("sources", []):
            if s.get("status") in ("blocked", "captcha"):
                raise SourceFailure(BLOCKED, f"{s.get('site')} blocked the automated check; a person needs to look")
            for m in s.get("matches", []):
                if m.get("covers_this_model") not in ("yes", "maybe"):
                    continue
                text = " ".join([m.get("title") or "", " ".join(m.get("models_named") or []), m.get("hazard") or ""])
                records.append(SourceRecord(
                    source=self.id, record_id=f"{self.id}:{payload_hash(m.get('url') or text)[:12]}",
                    source_url=m.get("url") or s.get("start_url") or "", record_type="recall_notice",
                    raw_payload_hash=payload_hash(m), event_at=None,
                    source_published_at=normalizer.to_datetime(m.get("date")), source_updated_at=None,
                    retrieved_at=retrieved, product_identifiers=normalizer.identifiers(
                        [], text, models=m.get("models_named") or []),
                    claims=[{"claim_type": "recall", "text": m.get("title") or "", "excerpt": m.get("title") or "",
                             "extraction_method": "research_agent_gemini", "needs_person": True}],
                    title=m.get("title") or "", hazard=m.get("hazard") or "", jurisdiction=JURISDICTION.get(site, ""),
                    affected_markets=[JURISDICTION.get(site, "")], original_text=text,
                    legal_scope="recall (found by browsing; for a person to confirm)",
                    authority=s.get("site") or self.id, attribution=self.entry.get("attribution", "")))
        return records
