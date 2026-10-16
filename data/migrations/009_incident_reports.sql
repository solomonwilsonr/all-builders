-- 009 shopper incident reports: a photo of a melted charger and what happened, checked by Gemini, grouped by model.
-- Similar independent reports add up to an early warning before any official recall (engine/incidents.py).
-- The photo itself is never stored, only its hash; the reporter only as a hash.

CREATE TABLE IF NOT EXISTS incident_reports (
    id            TEXT PRIMARY KEY,                   -- IR-...
    reporter_ref  TEXT,                               -- hashed shopper id, never raw identity
    brand         TEXT,
    model         TEXT,
    model_key     TEXT NOT NULL,                      -- brand|comparable model, for grouping
    market        TEXT,
    description   TEXT NOT NULL,                      -- contact details removed
    summary       TEXT,
    hazard_type   TEXT,
    severity      TEXT,
    first_hand    BOOLEAN,
    injury        BOOLEAN,
    photo_sha256  TEXT,
    photo_damage  TEXT,                               -- heat_or_fire | swelling | impact | wear | none | unclear
    happened_on   DATE,
    model_version TEXT,
    status        TEXT NOT NULL DEFAULT 'received',   -- received | reviewed | rejected
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS incident_reports_model ON incident_reports (model_key, created_at DESC);
