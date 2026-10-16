-- 004 assessments (plan v2.2 workstream B/H): every answer as an immutable snapshot (inputs, versions, cutoff,
-- output, citations), and the prospective prediction log (hash-chained, append-only).

CREATE TABLE IF NOT EXISTS assessment_snapshots (
    id                TEXT PRIMARY KEY,               -- AS-...
    investigation_id  TEXT,
    product_id        TEXT,
    market            TEXT,
    input_ids         JSONB,                          -- record ids, evidence ids, claim ids used
    query             JSONB,                          -- what was asked (no personal data)
    model_versions    JSONB,
    policy_version    TEXT NOT NULL,
    source_cutoff     TIMESTAMPTZ,                    -- nothing published after this was used
    outcome           TEXT NOT NULL,
    output            JSONB NOT NULL,
    citations         JSONB,
    source_mode       TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS assessment_snapshots_product ON assessment_snapshots (product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS assessment_snapshots_investigation ON assessment_snapshots (investigation_id);

CREATE TABLE IF NOT EXISTS prediction_log (
    id             BIGSERIAL PRIMARY KEY,
    snapshot_id    TEXT NOT NULL,
    product_key    TEXT NOT NULL,                     -- brand|model|market (normalised)
    outcome        TEXT NOT NULL,
    predicted_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    previous_hash  TEXT,
    entry_hash     TEXT NOT NULL,                     -- sha256(previous_hash + row): edits break the chain
    resolved_outcome TEXT,                            -- filled later from a recall or incident, never edited above
    resolved_at    TIMESTAMPTZ,
    resolution_ref TEXT
);
CREATE INDEX IF NOT EXISTS prediction_log_product ON prediction_log (product_key);
