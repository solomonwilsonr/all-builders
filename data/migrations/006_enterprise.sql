-- 006 enterprise (plan v2.2 workstream I): tenants, hashed API keys with scopes, usage metering, a shared rate
-- limit, idempotency, signed webhooks, and durable investigation jobs.

CREATE TABLE IF NOT EXISTS tenants (
    id          TEXT PRIMARY KEY,                     -- TN-...
    name        TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'pilot',
    retention_days INT NOT NULL DEFAULT 90,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash    TEXT PRIMARY KEY,                     -- sha256 of the key; the key itself is shown once and never stored
    tenant_id   TEXT NOT NULL REFERENCES tenants(id),
    scopes      TEXT[] NOT NULL,                      -- consumer | developer | reviewer | admin
    label       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS usage_events (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    operation   TEXT NOT NULL,
    status      INT,
    at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS usage_events_tenant_time ON usage_events (tenant_id, at DESC);
CREATE TABLE IF NOT EXISTS rate_limit_buckets (       -- shared across API instances (the in-process limiter is not)
    bucket      TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    hits        INT NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket, window_start)
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    tenant_id   TEXT NOT NULL,
    key         TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, key)
);
CREATE TABLE IF NOT EXISTS webhooks (
    id          TEXT PRIMARY KEY,                     -- WH-...
    tenant_id   TEXT NOT NULL,
    url         TEXT NOT NULL,
    secret_hash TEXT NOT NULL,                        -- the signing secret is shown once; deliveries are HMAC-SHA256
    events      TEXT[] NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id          BIGSERIAL PRIMARY KEY,
    webhook_id  TEXT NOT NULL,
    event       TEXT NOT NULL,
    status      INT,
    attempts    INT NOT NULL DEFAULT 0,
    payload_hash TEXT,
    at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS investigation_jobs (
    id          TEXT PRIMARY KEY,                     -- INV-...
    tenant_id   TEXT NOT NULL,
    status      TEXT NOT NULL,                        -- queued | running | complete | failed
    request     JSONB NOT NULL,
    snapshot_id TEXT,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS investigation_jobs_tenant ON investigation_jobs (tenant_id, created_at DESC);
