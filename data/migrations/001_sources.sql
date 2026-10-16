-- 001 sources (plan v2.2 workstream A/B): the source registry, every fetch, and what each investigation checked.
-- Forward-only and additive: nothing existing is dropped or renamed.

CREATE TABLE IF NOT EXISTS source_registry (
    id              TEXT PRIMARY KEY,               -- cpsc, jp_caa, oecd_globalrecalls ...
    name            TEXT NOT NULL,
    authority       TEXT,
    jurisdiction    TEXT,
    access_method   TEXT,
    access_status   TEXT,                           -- verified | key_required | blocked | browser_only | unverified | not_available
    terms           TEXT,
    regions         TEXT[],
    refresh_ttl_s   INT,
    checked_at      DATE,
    health          JSONB DEFAULT '{}',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_fetches (
    id          BIGSERIAL PRIMARY KEY,
    query_hash  TEXT NOT NULL,
    adapter     TEXT NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL,
    status      TEXT NOT NULL,                      -- ok | timeout | blocked | rate_limited | error | ...
    latency_ms  INT,
    etag        TEXT,
    raw_hash    TEXT,
    storage_uri TEXT,                               -- only when the source's licence allows keeping the raw answer
    record_ids  JSONB,
    mode        TEXT,                               -- live | cache
    detail      TEXT
);
CREATE INDEX IF NOT EXISTS source_fetches_adapter_time ON source_fetches (adapter, fetched_at DESC);
CREATE INDEX IF NOT EXISTS source_fetches_query ON source_fetches (query_hash);

CREATE TABLE IF NOT EXISTS coverage_checks (
    id               BIGSERIAL PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    source_id        TEXT NOT NULL,
    country          TEXT,
    state            TEXT NOT NULL,                 -- checked_live | checked_cache | source_unavailable | not_supported | no_matching_notice_found
    mode             TEXT,
    checked_at       TIMESTAMPTZ,
    freshness        TEXT,
    detail           TEXT
);
CREATE INDEX IF NOT EXISTS coverage_checks_investigation ON coverage_checks (investigation_id);
