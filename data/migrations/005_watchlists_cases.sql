-- 005 watchlists and cases (plan v2.2 workstreams F/G): post-purchase monitoring, notifications, and the reviewable
-- case lifecycle. investigations already exists; it gains lifecycle columns.

CREATE TABLE IF NOT EXISTS watchlists (
    id           TEXT PRIMARY KEY,                    -- WL-...
    tenant_id    TEXT NOT NULL,
    owner_ref    TEXT NOT NULL,                       -- hashed shopper id, never raw identity
    product_id   TEXT,
    query        JSONB NOT NULL,                      -- brand, model, batch, market
    last_outcome TEXT,
    last_snapshot_id TEXT,
    notify       BOOLEAN NOT NULL DEFAULT true,       -- opt-in
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at   TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS watchlists_tenant_owner ON watchlists (tenant_id, owner_ref) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS notification_events (
    id            TEXT PRIMARY KEY,                   -- NE-...
    tenant_id     TEXT NOT NULL,
    watchlist_id  TEXT,
    kind          TEXT NOT NULL,                      -- new_concern | worsened | correction | retraction
    dedupe_key    TEXT NOT NULL,
    body          JSONB NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS notification_events_dedupe ON notification_events (tenant_id, dedupe_key);

ALTER TABLE investigations ADD COLUMN IF NOT EXISTS lifecycle TEXT;   -- candidate .. resolved / reopened
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS product_id TEXT;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS opened_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

CREATE TABLE IF NOT EXISTS case_reviews (
    id            BIGSERIAL PRIMARY KEY,
    case_id       TEXT NOT NULL,
    from_state    TEXT,
    to_state      TEXT NOT NULL,
    reviewer_ref  TEXT NOT NULL,
    rationale     TEXT,
    at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS case_actions (
    id            BIGSERIAL PRIMARY KEY,
    case_id       TEXT NOT NULL,
    action        TEXT NOT NULL,                      -- prefill_regulator_form | notify_owners | publish_correction ...
    status        TEXT NOT NULL DEFAULT 'pending',    -- pending | confirmed_by_user | done | cancelled
    payload       JSONB,
    actor_ref     TEXT,
    at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS case_evidence_links (
    case_id       TEXT NOT NULL,
    claim_id      TEXT,
    evidence_id   TEXT,
    role          TEXT,                               -- supports | contradicts | context
    PRIMARY KEY (case_id, claim_id, evidence_id)
);
CREATE TABLE IF NOT EXISTS reviewer_decisions (
    id            BIGSERIAL PRIMARY KEY,
    subject_type  TEXT NOT NULL,                      -- product_match | hazard_inference | report | cross_border
    subject_id    TEXT NOT NULL,
    decision      TEXT NOT NULL,                      -- approve | correct | reject
    correction    JSONB,
    reviewer_ref  TEXT NOT NULL,
    second_reviewer_ref TEXT,
    rationale     TEXT,
    at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
