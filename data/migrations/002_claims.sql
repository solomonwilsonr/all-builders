-- 002 claims (plan v2.2 workstream B, J2): the claim-level evidence passport. evidence_claims already exists as a
-- three-column join table (evidence_id, claim_type, claim_id); it is extended in place, its rows untouched.

ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS claim_text TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS product_id TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS variant TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS batch_scope TEXT[];
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS jurisdiction TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_registry_id TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_record_id TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_type TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_document_hash TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_excerpt TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_language TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS license_policy_id TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS event_at TIMESTAMPTZ;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_published_at TIMESTAMPTZ;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS source_updated_at TIMESTAMPTZ;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS retrieved_at TIMESTAMPTZ;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS ingested_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS extraction_method TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS model_version TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS tool_version TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS prompt_version TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS verification_state TEXT;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS confidence REAL;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS revision INT DEFAULT 1;
ALTER TABLE evidence_claims ADD COLUMN IF NOT EXISTS investigation_id TEXT;
-- One row per claim per revision for passport rows (idempotent re-ingestion: source + record + claim + revision).
-- Older join rows (no source_record_id) reuse claim_id across evidence, so they are left out of the constraint.
CREATE UNIQUE INDEX IF NOT EXISTS evidence_claims_identity
    ON evidence_claims (claim_id, revision) WHERE source_record_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS evidence_revisions (
    id            BIGSERIAL PRIMARY KEY,
    entity_type   TEXT NOT NULL,                    -- claim | evidence | assessment
    entity_id     TEXT NOT NULL,
    previous_hash TEXT,
    new_hash      TEXT,
    reason        TEXT,
    actor         TEXT,
    version       INT NOT NULL DEFAULT 1,
    at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS evidence_revisions_entity ON evidence_revisions (entity_type, entity_id);
