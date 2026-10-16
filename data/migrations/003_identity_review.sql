-- 003 identity review (plan v2.2 workstream C): adjudication fields on relationships, negative edges, and the
-- reviewed pair gold set. Existing relationship rows keep their values; new columns are nullable.

ALTER TABLE product_relationships ADD COLUMN IF NOT EXISTS adjudicated_by TEXT;
ALTER TABLE product_relationships ADD COLUMN IF NOT EXISTS adjudicated_at TIMESTAMPTZ;
ALTER TABLE product_relationships ADD COLUMN IF NOT EXISTS identity_policy_version TEXT;
ALTER TABLE product_relationships ADD COLUMN IF NOT EXISTS affected_batch_scope TEXT;
ALTER TABLE product_relationships ADD COLUMN IF NOT EXISTS contradiction_evidence_ids TEXT[];

-- New edge kinds: a regional variant, an unverified rebrand, and the negative edge "distinct_product" (reviewed: not
-- the same product). The CHECK is widened, never narrowed.
ALTER TABLE product_relationships DROP CONSTRAINT IF EXISTS product_relationships_relationship_type_check;
ALTER TABLE product_relationships ADD CONSTRAINT product_relationships_relationship_type_check CHECK (
    relationship_type IN ('exact_model', 'rebranded_equivalent', 'model_variant', 'visually_similar',
                          'shared_component', 'regional_variant', 'unverified_rebrand', 'distinct_product'));

CREATE TABLE IF NOT EXISTS identity_pairs (           -- the identity gold set: one row per annotator decision
    pair_id        TEXT NOT NULL,                     -- sorted "SS-P-a|SS-P-b"
    source_id      TEXT NOT NULL,
    target_id      TEXT NOT NULL,
    label          TEXT NOT NULL CHECK (label IN ('exact', 'rebrand', 'regional_variant', 'lookalike',
                                                  'counterfeit_suspect', 'distinct', 'unresolvable')),
    annotator      TEXT NOT NULL,                     -- hashed reviewer id
    rationale      TEXT,
    market         TEXT,
    guideline_version TEXT,
    at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (pair_id, annotator)
);
