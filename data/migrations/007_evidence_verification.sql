-- 007 evidence verification (plan v2.2 J5): claim support, independent observation groups, contradictions,
-- identity-scope reviews and the reviewer queue. Reuses evidence_claims, evidence_revisions, audit_events and
-- product_relationships rather than duplicating them.

CREATE TABLE IF NOT EXISTS claim_source_support (
    claim_id            TEXT NOT NULL,
    source_registry_id  TEXT NOT NULL,
    source_record_id    TEXT NOT NULL,
    authenticity        TEXT NOT NULL,                -- authentic | official_domain | unofficial_domain | missing_reference
    support             TEXT NOT NULL,                -- supported | unsupported | not_checked
    checked_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (claim_id, source_record_id)
);
CREATE TABLE IF NOT EXISTS observation_groups (
    group_id        TEXT NOT NULL,                    -- OG-...
    member_id       TEXT NOT NULL,                    -- claim, evidence or record id
    reason          TEXT,
    investigation_id TEXT,
    PRIMARY KEY (group_id, member_id)
);
CREATE TABLE IF NOT EXISTS claim_contradictions (
    id              BIGSERIAL PRIMARY KEY,
    investigation_id TEXT,
    kind            TEXT NOT NULL,                    -- retraction | correction | unaffected_model | unaffected_batch | alternative_cause
    record_id       TEXT,
    text            TEXT,
    effect          TEXT NOT NULL,                    -- retract | downgrade | note
    at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS identity_scope_reviews (
    id              BIGSERIAL PRIMARY KEY,
    product_key     TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    tier            TEXT NOT NULL,
    scope           TEXT NOT NULL,
    local           BOOLEAN,
    reasons         JSONB,
    reviewer_ref    TEXT,                             -- null = decided by code
    decision        TEXT,                             -- approve | correct | reject (by a reviewer)
    at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS review_queue (
    id              TEXT PRIMARY KEY,                 -- RQ-...
    case_id         TEXT NOT NULL,                    -- investigation or snapshot it belongs to
    tenant_id       TEXT NOT NULL DEFAULT 'public',
    kind            TEXT NOT NULL,                    -- cross_border | possible_match | hazard | report | identity
    subject         JSONB NOT NULL,
    reasons         JSONB,
    state           TEXT NOT NULL DEFAULT 'open',     -- open | assigned | decided | second_review
    assigned_to     TEXT,
    priority        INT NOT NULL DEFAULT 2,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at      TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS review_decisions (
    id              BIGSERIAL PRIMARY KEY,
    queue_id        TEXT NOT NULL,
    reviewer_ref    TEXT NOT NULL,
    decision        TEXT NOT NULL,                    -- approve | correct | reject | escalate
    correction      JSONB,
    rationale       TEXT NOT NULL,
    second_review   BOOLEAN NOT NULL DEFAULT false,
    at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_claims_source ON evidence_claims (source_registry_id, source_record_id);
CREATE INDEX IF NOT EXISTS evidence_claims_product_time ON evidence_claims (product_id, source_published_at);
CREATE INDEX IF NOT EXISTS observation_groups_group ON observation_groups (group_id);
CREATE INDEX IF NOT EXISTS review_queue_state ON review_queue (state, priority, created_at);
