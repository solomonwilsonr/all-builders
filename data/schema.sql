-- SafeShelf database (Postgres 16 + pgvector). Design: SAFESHELF.md section 10.
-- Rules: evidence is never deleted; conclusions are versioned; personal data stays out of public tables.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS manufacturers (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    country         TEXT,
    registry_ids    JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS product_families (
    id              TEXT PRIMARY KEY,
    family_name     TEXT,
    manufacturer_id TEXT REFERENCES manufacturers(id)
);

CREATE TABLE IF NOT EXISTS products (
    id              TEXT PRIMARY KEY,               -- e.g. SS-P-10291
    brand           TEXT,
    model           TEXT,
    category        TEXT,
    gtin            TEXT,
    family_id       TEXT REFERENCES product_families(id),
    identity_status TEXT NOT NULL DEFAULT 'provisional'
                    CHECK (identity_status IN ('provisional', 'verified', 'unknown')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sellers (
    id                   TEXT PRIMARY KEY,
    marketplace          TEXT,
    seller_ref           TEXT,
    domain               TEXT,
    domain_registered_at DATE,
    is_authorised        BOOLEAN,
    first_seen           TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS listings (
    id           TEXT PRIMARY KEY,                  -- e.g. SS-L-0001, or amazon:<parent_asin>
    product_id   TEXT REFERENCES products(id),
    seller_id    TEXT REFERENCES sellers(id),
    marketplace  TEXT,
    url          TEXT,
    title        TEXT,
    raw          JSONB,                             -- extracted fields only, never full marketplace pages
    captured_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS price_observations (
    product_id  TEXT REFERENCES products(id),
    listing_id  TEXT REFERENCES listings(id),
    price       NUMERIC,
    currency    TEXT,
    observed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS product_fingerprints (
    product_id      TEXT REFERENCES products(id),
    version         INT NOT NULL DEFAULT 1,
    text_vector     vector(768),
    image_vector    vector(1408),                   -- Vertex multimodal embedding size
    attributes_json JSONB,
    PRIMARY KEY (product_id, version)
);

CREATE TABLE IF NOT EXISTS product_attributes (
    product_id TEXT REFERENCES products(id),
    attribute  TEXT,
    value      TEXT,
    unit       TEXT,
    source     TEXT,
    verified   BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS evidence (
    id           TEXT PRIMARY KEY,                  -- e.g. EV-201
    source_type  TEXT NOT NULL,                     -- review, review_photo, recall, registry, report, page_snapshot
    source_ref   TEXT,                              -- review id, URL, registry number
    storage_uri  TEXT,                              -- gs://... for photos and snapshots
    content      TEXT,
    observed_at  TIMESTAMPTZ,                       -- when it happened (review date)
    captured_at  TIMESTAMPTZ NOT NULL DEFAULT now(),-- when we collected it
    hash         TEXT,                              -- duplicates count once
    pii_status   TEXT NOT NULL DEFAULT 'none'
);

CREATE TABLE IF NOT EXISTS product_relationships (
    source_id         TEXT REFERENCES products(id),
    target_id         TEXT REFERENCES products(id),
    relationship_type TEXT NOT NULL CHECK (relationship_type IN
        ('exact_model', 'rebranded_equivalent', 'model_variant', 'visually_similar', 'shared_component')),
    confidence        REAL,
    status            TEXT NOT NULL DEFAULT 'unverified' CHECK (status IN ('verified', 'unverified', 'rejected')),
    evidence_ids      TEXT[],
    would_change_if   TEXT[],
    version           INT NOT NULL DEFAULT 1,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source_id, target_id, version)
);

CREATE TABLE IF NOT EXISTS hazard_signals (
    id          TEXT PRIMARY KEY,
    product_id  TEXT REFERENCES products(id),
    hazard_type TEXT,
    mechanism   TEXT,
    severity    TEXT,
    status      TEXT NOT NULL DEFAULT 'under_review',
    first_seen  DATE,
    last_seen   DATE
);

CREATE TABLE IF NOT EXISTS certifications (
    product_id        TEXT REFERENCES products(id),
    authority         TEXT NOT NULL,
    number            TEXT,
    claimed_value     TEXT,
    registry_value    TEXT,
    validation_status TEXT CHECK (validation_status IN ('verified', 'mismatch', 'unknown')),
    mismatch_field    TEXT,
    checked_at        TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS recalls (
    id          TEXT PRIMARY KEY,                   -- e.g. cpsc:23240
    authority   TEXT NOT NULL,                      -- CPSC, ACCC, ...
    notice_date DATE,
    title       TEXT,
    hazard      TEXT,
    scope_json  JSONB,                              -- products, models, retailers, images
    url         TEXT
);

-- Official energy-rating registry (Australia), used by the safety-mark check.
CREATE TABLE IF NOT EXISTS registry_energy_rating (
    registration_number TEXT,
    appliance_type      TEXT,                       -- tv, rf, ac, ...
    brand               TEXT,
    model               TEXT,
    star_rating         REAL,
    status              TEXT,
    raw                 JSONB,
    PRIMARY KEY (appliance_type, brand, model)
);

CREATE TABLE IF NOT EXISTS trust_checks (
    listing_id            TEXT REFERENCES listings(id),
    copied_photo_match    BOOLEAN,
    matched_product_id    TEXT REFERENCES products(id),
    price_ratio_to_floor  REAL,
    domain_age_days       INT,
    result                JSONB,
    checked_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS investigations (
    id                TEXT PRIMARY KEY,
    product_family_id TEXT REFERENCES product_families(id),
    status            TEXT,
    assigned_reviewer TEXT,
    decision          TEXT,
    decided_at        TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reports (
    id           TEXT PRIMARY KEY,
    reporter_ref TEXT,                              -- hashed, never raw identity
    product_id   TEXT REFERENCES products(id),
    description  TEXT,
    evidence_ids TEXT[],
    status       TEXT NOT NULL DEFAULT 'received'
);

CREATE TABLE IF NOT EXISTS audit_events (
    entity_id   TEXT,
    entity_type TEXT,
    change_type TEXT,
    actor       TEXT,
    before      JSONB,
    after       JSONB,
    at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per traced API call of an investigation (engine/trace.py), shown in the Lab.
CREATE TABLE IF NOT EXISTS investigation_steps (
    investigation_id TEXT NOT NULL,
    n                INT NOT NULL,
    tool             TEXT NOT NULL,
    models           TEXT[],
    seconds          REAL,
    input_tokens     INT,
    output_tokens    INT,
    cost_usd         REAL,
    summary          TEXT,
    at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (investigation_id, n)
);

-- Join tables
CREATE TABLE IF NOT EXISTS evidence_claims        (evidence_id TEXT REFERENCES evidence(id), claim_type TEXT, claim_id TEXT);
CREATE TABLE IF NOT EXISTS recall_products        (recall_id TEXT REFERENCES recalls(id), product_id TEXT REFERENCES products(id), match_class TEXT);
CREATE TABLE IF NOT EXISTS investigation_evidence (investigation_id TEXT REFERENCES investigations(id), evidence_id TEXT REFERENCES evidence(id));
CREATE TABLE IF NOT EXISTS product_components     (product_id TEXT REFERENCES products(id), component TEXT, source TEXT);

CREATE INDEX IF NOT EXISTS recalls_notice_date ON recalls (notice_date);
CREATE INDEX IF NOT EXISTS evidence_observed_at ON evidence (observed_at);
CREATE INDEX IF NOT EXISTS registry_model ON registry_energy_rating (lower(model));
