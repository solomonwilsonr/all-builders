"""Base for sources SafeShelf may not query automatically (blocked, access unverified, or no automated access).

The planner never calls these while the registry says so; if one is called anyway it refuses with an honest status
and the manual lookup link, so a person can check it.
"""
from engine.sources.adapters._http import Base
from engine.sources.base import DISABLED, SourceFailure, SourceQuery, SourceRecord


class Unavailable(Base):
    reason = "automated access is not verified for this source"

    async def search(self, query: SourceQuery) -> list[SourceRecord]:
        link = self.entry.get("official_url") or "the regulator's site"
        raise SourceFailure(DISABLED, f"{self.reason}; a person can check it at {link}")
