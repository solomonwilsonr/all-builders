-- 010 household products (the household inventory), reminders and the chat's memory: what a household owns, with
-- receipts' dates for the warranty and return tracker, service requests, and family sharing by invite (engine/household.py). Owners only as hashes;
-- a receipt photo is never stored, only its SHA-256.

CREATE TABLE IF NOT EXISTS household_items (
    id             TEXT PRIMARY KEY,                  -- HI-...
    tenant_id      TEXT NOT NULL,
    owner_ref      TEXT NOT NULL,                     -- hashed shopper id, never raw identity
    name           TEXT NOT NULL,
    brand          TEXT,
    model          TEXT,
    category       TEXT,                              -- charger, power bank, appliance, battery...
    product_id     TEXT,
    bought_from    TEXT,
    order_ref      TEXT,
    bought_on      DATE,
    price          NUMERIC,
    currency       TEXT,
    return_by      DATE,
    warranty_until DATE,
    receipt_sha256 TEXT,
    notes          TEXT,
    service        JSONB NOT NULL DEFAULT '[]',       -- [{opened_on, kind, status, ref, note}]
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS household_items_owner ON household_items (tenant_id, owner_ref) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS household_members (
    invite_code   TEXT PRIMARY KEY,                   -- HS-... the owner shares it; the member accepts it
    tenant_id     TEXT NOT NULL,
    owner_ref     TEXT NOT NULL,                      -- whose household
    member_ref    TEXT,                               -- set when accepted
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    accepted_at   TIMESTAMPTZ,
    revoked_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS household_members_member ON household_members (tenant_id, member_ref) WHERE revoked_at IS NULL;

-- Reminders for household products (return window or warranty about to end) go to the owner directly, so a
-- notification can belong to an owner instead of a watchlist.
ALTER TABLE notification_events ADD COLUMN IF NOT EXISTS owner_ref TEXT;
CREATE INDEX IF NOT EXISTS notification_events_owner ON notification_events (tenant_id, owner_ref, created_at DESC)
    WHERE owner_ref IS NOT NULL;

-- The chat's memory of one conversation (engine/chat_memory.py): the product it is about, the last turns and an
-- attached manual, so follow-ups work from any screen and any API instance. Kept per owner (hashed) and session;
-- rows older than a day are ignored and overwritten.
CREATE TABLE IF NOT EXISTS chat_memory (
    session_id   TEXT NOT NULL,
    owner_ref    TEXT NOT NULL,
    data         JSONB NOT NULL DEFAULT '{}',          -- product_id, link, market, history
    document     TEXT,                                 -- the manual as a PDF data URL, if one was sent
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, owner_ref)
);
