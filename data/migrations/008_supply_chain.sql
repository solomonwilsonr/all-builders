-- 008 supply chain (plan v2.2 workstream E): manufacturer / importer / distributor / seller edges, each with its
-- citation and confidence. Never inferred from product appearance alone.

CREATE TABLE IF NOT EXISTS supply_chain_edges (
    id              BIGSERIAL PRIMARY KEY,
    product_key     TEXT NOT NULL,                    -- product id or brand|model
    party_name      TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('manufacturer', 'importer', 'distributor', 'seller', 'retailer',
                                                  'component_supplier')),
    country         TEXT,
    source_record_id TEXT NOT NULL,                   -- the official record that names this party
    source_url      TEXT,
    confidence      REAL NOT NULL,
    at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_key, party_name, role, source_record_id)
);
CREATE TABLE IF NOT EXISTS certification_checks (     -- claimed vs registry values, with scope and expiry
    id              BIGSERIAL PRIMARY KEY,
    product_id      TEXT,
    authority       TEXT NOT NULL,
    number          TEXT,
    claimed_value   TEXT,
    registry_value  TEXT,
    status          TEXT NOT NULL,                    -- verified | mismatch | not_verified (never "fake" for unchecked)
    scope           TEXT,
    expires_on      DATE,
    source          TEXT,
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
