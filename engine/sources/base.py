"""The adapter contract every official source implements (plan v2.2 sections 2A and 3).

SourceQuery   what to look for, and for which market
SourceRecord  one official record, with its four timestamps kept apart and its original-language text
SourceResult  what one adapter returned for one query: records, or an honest failure state

Timestamps: event_at (when it happened), source_published_at (when the regulator published it), source_updated_at
(when the regulator last changed it) and retrieved_at (when SafeShelf read it) are never merged, so a historical replay
can refuse anything published after its cutoff.
"""
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Protocol

# Coverage states for one source (and, rolled up, one country). A failure is never "no_matching_notice_found".
CHECKED_LIVE = "checked_live"
CHECKED_CACHE = "checked_cache"
UNAVAILABLE = "source_unavailable"
NOT_SUPPORTED = "not_supported"
NO_MATCH = "no_matching_notice_found"
COVERAGE_STATES = (CHECKED_LIVE, CHECKED_CACHE, UNAVAILABLE, NOT_SUPPORTED, NO_MATCH)

# What an adapter call ended in.
OK = "ok"                      # the source answered (with or without records)
TIMEOUT = "timeout"
BLOCKED = "blocked"            # 403, captcha, robots refusal: SafeShelf stops, it never works around a block
RATE_LIMITED = "rate_limited"  # 429
ERROR = "error"                # 5xx, malformed answer, network error
NOT_CONFIGURED = "not_configured"  # needs a key or a service that is not set up here
DISABLED = "disabled"          # access not verified yet, or switched off by policy
CIRCUIT_OPEN = "circuit_open"  # too many recent failures: not called for a while
FAILURES = (TIMEOUT, BLOCKED, RATE_LIMITED, ERROR, NOT_CONFIGURED, DISABLED, CIRCUIT_OPEN)

RECORD_TYPES = ("recall_notice", "safety_notice", "seizure", "incident_report", "registry_record",
                "manufacturer_statement", "correction")


def now() -> datetime:
    return datetime.now(UTC)


def payload_hash(payload) -> str:
    if isinstance(payload, (bytes, str)):
        body = payload
    else:
        body = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(body.encode() if isinstance(body, str) else body).hexdigest()


@dataclass
class SourceQuery:
    brand: str | None = None
    model: str | None = None
    gtin: str | None = None
    category: str | None = None
    region: str | None = None             # kept for older callers; market_country wins
    as_of: datetime | None = None         # historical replay: nothing published after this counts
    market_country: str | None = None     # ISO 3166-1 alpha-2, upper case: IN, JP, AU, SG...
    source_country: str | None = None     # only this jurisdiction's sources, when set
    languages: list[str] = field(default_factory=list)
    local_identifiers: dict = field(default_factory=dict)  # {"jan": "4901234567894", "bis_r": "R-41012345"}
    marketplace: str | None = None
    batch: str | None = None              # lot, serial or date code, when the shopper gave one
    title: str | None = None

    def __post_init__(self):
        self.market_country = (self.market_country or self.region or "").upper() or None
        self.source_country = (self.source_country or "").upper() or None

    def key(self) -> str:
        """A stable hash for caching and the fetch log (no personal data goes into a query)."""
        parts = {k: v for k, v in asdict(self).items() if v not in (None, "", [], {})}
        return payload_hash(parts)[:24]

    def terms(self) -> list[str]:
        """What to type into a source's search: model number first, then brand, then the title's first words."""
        out = [t for t in (self.model, self.gtin, self.brand) if t]
        if not out and self.title:
            out.append(" ".join(self.title.split()[:4]))
        return out


@dataclass
class SourceRecord:
    source: str                       # registry id, e.g. "cpsc", "jp_caa"
    record_id: str                    # the regulator's own stable ID
    source_url: str
    record_type: str
    raw_payload_hash: str
    event_at: datetime | None
    source_published_at: datetime | None
    source_updated_at: datetime | None
    retrieved_at: datetime
    product_identifiers: dict         # {"brands": [...], "models": [...], "gtins": [...], "batches": [...]}
    claims: list[dict]                # [{"claim_type": "recall", "text": "...", "excerpt": "..."}]
    title: str = ""
    hazard: str = ""
    remedy: str = ""
    jurisdiction: str = ""            # ISO code of the regulator that issued it: US, AU, JP, IN, EU...
    affected_markets: list[str] = field(default_factory=list)
    language: str = "en"
    original_text: str = ""           # never replaced by a translation
    translated_fields: dict = field(default_factory=dict)  # {"title": {"text": ..., "machine": True, "lang": "en"}}
    original_text_hash: str = ""
    legal_scope: str = ""             # "recall" / "safety notice" / "seizure" ... as the regulator calls it
    publication_timezone: str = ""
    authority: str = ""               # CPSC, ACCC, CAA...
    mode: str = "live"                # live | cache
    attribution: str = ""             # credit line the source's licence asks for

    def __post_init__(self):
        if self.original_text and not self.original_text_hash:
            self.original_text_hash = payload_hash(self.original_text)

    def to_dict(self) -> dict:
        out = asdict(self)
        for k in ("event_at", "source_published_at", "source_updated_at", "retrieved_at"):
            out[k] = out[k].isoformat() if out[k] else None
        return out


@dataclass
class SourceResult:
    source: str
    status: str                       # OK or one of FAILURES
    records: list[SourceRecord] = field(default_factory=list)
    mode: str = "live"                # live | cache
    retrieved_at: datetime = field(default_factory=now)
    latency_ms: int = 0
    detail: str = ""                  # why it failed, in plain words
    query_key: str = ""
    raw_hash: str = ""
    freshness: str | None = None      # newest publication date the source holds (cache) or returned

    @property
    def ok(self) -> bool:
        return self.status == OK

    def coverage_state(self) -> str:
        if self.status in (NOT_CONFIGURED, DISABLED):
            return NOT_SUPPORTED
        if not self.ok:
            return UNAVAILABLE
        return CHECKED_LIVE if self.mode == "live" else CHECKED_CACHE

    def to_dict(self) -> dict:
        return {"source": self.source, "status": self.status, "mode": self.mode, "coverage": self.coverage_state(),
                "retrieved_at": self.retrieved_at.isoformat(), "latency_ms": self.latency_ms, "detail": self.detail,
                "freshness": self.freshness, "records": [r.to_dict() for r in self.records]}


class SourceAdapter(Protocol):
    id: str

    async def search(self, query: SourceQuery) -> list[SourceRecord]: ...

    async def health(self) -> dict: ...


class SourceFailure(Exception):
    """Raised by an adapter for an honest failure state (blocked, rate limited, not configured...)."""

    def __init__(self, status: str, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail
