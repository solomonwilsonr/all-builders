"""Tenants, scoped API keys, usage metering, a shared rate limit and idempotency (plan v2.2 workstream I).

    caller(headers)                -> Caller(tenant_id, scopes, owner_ref)   who is calling, from X-API-Key
    require(caller, scope)         -> raises PermissionError when the key lacks the scope
    allow(caller, operation)       -> None, or the reason for a 429 (shared across API instances, in Postgres)
    meter(caller, operation, code) -> one usage_events row
    idempotent(caller, key, body)  -> a stored answer for a repeated Idempotency-Key, or None

Keys are random, shown once, and stored only as a SHA-256 hash. No key = the public tenant with the "consumer" scope
(the extension, judges' page and WhatsApp bot), which can't see any other tenant's watchlists, cases or usage.

    cd engine && PYTHONPATH=.. uv run python -m engine.tenancy create --name "Pilot retailer" --scopes developer
"""
import argparse
import hashlib
import json
import os
import secrets
from dataclasses import dataclass, field

from psycopg.types.json import Jsonb

from engine import store

PUBLIC = "public"
SCOPES = ("consumer", "developer", "reviewer", "admin")
PER_MINUTE = {"pilot": 120, "public": 60, "internal": 600}


@dataclass
class Caller:
    tenant_id: str = PUBLIC
    scopes: list[str] = field(default_factory=lambda: ["consumer"])
    owner_ref: str | None = None   # hashed id of the shopper behind the call (screens send X-Owner-Ref)
    plan: str = "public"

    @property
    def is_admin(self) -> bool:
        return "admin" in self.scopes


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def owner_hash(raw: str | None) -> str | None:
    """The screens send a Firebase uid or a WhatsApp number; only a salted hash is ever stored."""
    if not raw:
        return None
    salt = os.environ.get("SAFESHELF_OWNER_SALT", "safeshelf-owner")
    return "OW-" + hashlib.sha256(f"{salt}|{raw}".encode()).hexdigest()[:24]


def caller(headers) -> Caller:
    key = headers.get("x-api-key")
    owner = owner_hash(headers.get("x-owner-ref") or headers.get("x-reporter-ref"))
    if not key:
        return Caller(owner_ref=owner)
    if os.environ.get("API_KEY") and secrets.compare_digest(key, os.environ["API_KEY"]):
        return Caller(tenant_id="internal", scopes=list(SCOPES), owner_ref=owner, plan="internal")
    row = store.conn().execute(
        """SELECT k.tenant_id, k.scopes, t.plan FROM api_keys k JOIN tenants t ON t.id = k.tenant_id
           WHERE k.key_hash = %s AND k.revoked_at IS NULL""", (hash_key(key),)).fetchone()
    if not row:
        raise PermissionError("unknown or revoked API key")
    return Caller(tenant_id=row["tenant_id"], scopes=list(row["scopes"]), owner_ref=owner, plan=row["plan"])


def require(who: Caller, scope: str) -> None:
    if scope not in who.scopes and not who.is_admin:
        raise PermissionError(f"this API key lacks the '{scope}' scope")


def allow(who: Caller, operation: str) -> str | None:
    """A per-tenant per-minute limit kept in Postgres, so every API instance shares it. Public callers keep the
    in-process limiter in api/app/main.py as well."""
    limit = PER_MINUTE.get(who.plan, PER_MINUTE["pilot"])
    bucket = f"{who.tenant_id}:{operation if who.tenant_id == PUBLIC else 'all'}"
    try:
        row = store.conn().execute(
            """INSERT INTO rate_limit_buckets (bucket, window_start, hits) VALUES (%s, date_trunc('minute', now()), 1)
               ON CONFLICT (bucket, window_start) DO UPDATE SET hits = rate_limit_buckets.hits + 1
               RETURNING hits""", (bucket,)).fetchone()
    except Exception:  # noqa: BLE001  no shared store: the in-process limiter still applies
        return None
    if row["hits"] > limit:
        return f"Too many requests for this API key: at most {limit} a minute."
    return None


def meter(who: Caller, operation: str, status: int) -> None:
    if who.tenant_id == PUBLIC:
        return
    try:
        store.conn().execute("INSERT INTO usage_events (tenant_id, operation, status) VALUES (%s, %s, %s)",
                             (who.tenant_id, operation, status))
    except Exception:  # noqa: BLE001, S110  metering never fails a request
        pass


def usage(who: Caller, days: int = 30) -> dict:
    require(who, "developer")
    rows = store.conn().execute(
        """SELECT operation, count(*) AS calls, count(*) FILTER (WHERE status >= 400) AS errors,
                  min(at) AS first_call, max(at) AS last_call
           FROM usage_events WHERE tenant_id = %s AND at > now() - make_interval(days => %s)
           GROUP BY operation ORDER BY calls DESC""", (who.tenant_id, days)).fetchall()
    return {"tenant_id": who.tenant_id, "days": days,
            "operations": [{**r, "first_call": r["first_call"].isoformat(), "last_call": r["last_call"].isoformat()}
                           for r in rows],
            "total_calls": sum(r["calls"] for r in rows),
            "note": "Usage of this tenant only. Billing and pricing are separate commercial decisions."}


def idempotent(who: Caller, key: str | None, body: dict) -> dict | None:
    """The stored answer when this tenant already sent this Idempotency-Key with the same body."""
    if not key:
        return None
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
    row = store.conn().execute("SELECT request_hash, response FROM idempotency_keys WHERE tenant_id = %s AND key = %s",
                               (who.tenant_id, key)).fetchone()
    if row and row["request_hash"] != digest:
        raise ValueError("this Idempotency-Key was already used with a different request")
    return row["response"] if row else None


def remember(who: Caller, key: str | None, body: dict, response: dict) -> None:
    if not key:
        return
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
    store.conn().execute(
        """INSERT INTO idempotency_keys (tenant_id, key, request_hash, response) VALUES (%s, %s, %s, %s)
           ON CONFLICT (tenant_id, key) DO NOTHING""", (who.tenant_id, key, digest, Jsonb(response)))


def create_tenant(name: str, scopes: list[str], plan: str = "pilot") -> dict:
    bad = [s for s in scopes if s not in SCOPES]
    if bad:
        raise ValueError(f"unknown scopes {bad}; use {SCOPES}")
    tenant_id = store.short_id("TN-", name, secrets.token_hex(4))
    key = "ssk_" + secrets.token_urlsafe(32)
    store.conn().execute("INSERT INTO tenants (id, name, plan) VALUES (%s, %s, %s)", (tenant_id, name, plan))
    store.conn().execute("INSERT INTO api_keys (key_hash, tenant_id, scopes, label) VALUES (%s, %s, %s, %s)",
                         (hash_key(key), tenant_id, scopes, name))
    return {"tenant_id": tenant_id, "api_key": key, "scopes": scopes,
            "note": "Shown once. SafeShelf stores only its hash."}


def revoke(key: str) -> bool:
    row = store.conn().execute("UPDATE api_keys SET revoked_at = now() WHERE key_hash = %s AND revoked_at IS NULL "
                               "RETURNING tenant_id", (hash_key(key),)).fetchone()
    return bool(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a tenant and its API key, or revoke a key.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    make = sub.add_parser("create")
    make.add_argument("--name", required=True)
    make.add_argument("--scopes", default="developer")
    make.add_argument("--plan", default="pilot")
    gone = sub.add_parser("revoke")
    gone.add_argument("--key", required=True)
    args = parser.parse_args()
    if args.cmd == "create":
        print(json.dumps(create_tenant(args.name, args.scopes.split(","), args.plan), indent=1))
    else:
        print("revoked" if revoke(args.key) else "no such active key")


if __name__ == "__main__":
    main()
