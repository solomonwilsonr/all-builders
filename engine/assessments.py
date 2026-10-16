"""Persistence for live investigations (plan v2.2 workstreams B and J5): assessment snapshots, the claim passport,
coverage checks, observation groups, contradictions, scope decisions, the review queue, investigation jobs and the
prospective prediction log. Everything here is additive and versioned: a snapshot is never edited, a later answer is
a new snapshot, and the difference between two dates can be shown from the rows.

Every function tolerates a missing database (local runs without Postgres): it logs and returns None.
"""
import hashlib
import json
import logging
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from engine import store

log = logging.getLogger(__name__)


def _safe(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as error:  # noqa: BLE001  storage must never break an answer
            log.warning("%s not stored: %s", fn.__name__, type(error).__name__)
            return None
    wrapper.__name__ = fn.__name__
    return wrapper


def snapshot_id(investigation_id: str, outcome: str) -> str:
    return store.short_id("AS-", investigation_id, outcome, datetime.now(UTC).isoformat())


@_safe
def save_snapshot(answer: dict) -> str:
    sid = snapshot_id(answer["investigation_id"], answer["outcome"])
    citations = [{"record_id": m["record_id"], "url": m.get("url"), "published": m.get("published")}
                 for m in answer.get("matches", [])]
    conn = store.conn()
    conn.execute(
        """INSERT INTO assessment_snapshots (id, investigation_id, product_id, market, input_ids, query,
                                             model_versions, policy_version, source_cutoff, outcome, output,
                                             citations, source_mode)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (sid, answer["investigation_id"], answer.get("product", {}).get("product_id"), answer.get("market"),
         Jsonb({"records": [m["record_id"] for m in answer.get("matches", [])],
                "claims": [c["claim_id"] for c in answer.get("claims", [])]}),
         Jsonb(answer.get("query") or {}), Jsonb(answer.get("model_versions") or {}), answer["policy_version"],
         answer.get("as_of"), answer["outcome"], Jsonb(answer), Jsonb(citations), answer.get("source_mode")))
    conn.execute("""INSERT INTO investigations (id, status, lifecycle, product_id, tenant_id)
                    VALUES (%s, 'open', %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET updated_at = now(),
                        lifecycle = coalesce(investigations.lifecycle, EXCLUDED.lifecycle)""",
                 (answer["investigation_id"], "candidate" if answer.get("review_required") else "resolved",
                  answer.get("product", {}).get("product_id"), answer.get("tenant_id") or "public"))
    for row in answer.get("coverage", {}).get("sources", []):
        conn.execute(
            """INSERT INTO coverage_checks (investigation_id, source_id, country, state, mode, checked_at, freshness,
                                            detail) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (answer["investigation_id"], row["source"], row["jurisdiction"], row["state"], row["mode"],
             row["checked_at"], row["freshness"], (row["detail"] or "")[:300]))
    for claim in answer.get("claims", []):
        save_claim(claim, answer["investigation_id"])
    for group in answer.get("observation_groups", []):
        for member in group["members"]:
            conn.execute("""INSERT INTO observation_groups (group_id, member_id, reason, investigation_id)
                            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                         (group["group_id"], member, group["reason"], answer["investigation_id"]))
    for c in answer.get("contradictions", []):
        conn.execute("""INSERT INTO claim_contradictions (investigation_id, kind, record_id, text, effect)
                        VALUES (%s, %s, %s, %s, %s)""",
                     (answer["investigation_id"], c["kind"], c["record_id"], c["text"], c["effect"]))
    product_key = answer.get("product", {}).get("key") or ""
    for m in answer.get("matches", []):
        conn.execute("""INSERT INTO identity_scope_reviews (product_key, source_record_id, tier, scope, local, reasons)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                     (product_key, m["record_id"], m["tier"], m["scope"], m["local"], Jsonb(m.get("reasons") or [])))
    if answer.get("review_required"):
        queue_review(answer)
    log_prediction(sid, product_key, answer["outcome"])
    return sid


@_safe
def save_claim(claim: dict, investigation_id: str) -> None:
    before = store.conn().execute(
        "SELECT verification_state FROM evidence_claims WHERE claim_id = %s AND revision = 1 "
        "AND source_record_id IS NOT NULL", (claim["claim_id"],)).fetchone()
    if before and before["verification_state"] != claim.get("verification_status"):
        store.conn().execute(  # why a claim's standing changed between two dates (plan v2.2 workstream B)
            """INSERT INTO evidence_revisions (entity_type, entity_id, previous_hash, new_hash, reason, actor)
               VALUES ('claim', %s, %s, %s, %s, 'engine.investigation')""",
            (claim["claim_id"], before["verification_state"], claim.get("verification_status"),
             f"re-checked in {investigation_id}: {before['verification_state']} -> {claim.get('verification_status')}"))
    store.conn().execute(
        """INSERT INTO evidence_claims (claim_id, claim_type, claim_text, product_id, model, variant, batch_scope,
               jurisdiction, source_registry_id, source_record_id, source_url, source_type, source_document_hash,
               source_excerpt, source_language, license_policy_id, event_at, source_published_at, source_updated_at,
               retrieved_at, extraction_method, model_version, tool_version, prompt_version, verification_state,
               revision, investigation_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                   %s, 1, %s)
           ON CONFLICT (claim_id, revision) WHERE source_record_id IS NOT NULL DO UPDATE
               SET verification_state = EXCLUDED.verification_state, retrieved_at = EXCLUDED.retrieved_at""",
        (claim["claim_id"], claim["claim_type"], claim["claim_text"], claim.get("product_id"), claim.get("model"),
         claim.get("variant"), claim.get("batch_scope") or [], claim.get("jurisdiction"),
         claim["source_registry_id"], claim["source_record_id"], claim.get("source_url"), claim.get("source_type"),
         claim.get("source_document_hash"), claim.get("source_excerpt"), claim.get("source_language"),
         claim.get("license_policy_id"), claim.get("event_at"), claim.get("source_published_at"),
         claim.get("source_updated_at"), claim.get("retrieved_at"), claim.get("extraction_method"),
         claim.get("model_version"), claim.get("tool_version"), claim.get("prompt_version"),
         claim.get("verification_status"), investigation_id))
    store.conn().execute(
        """INSERT INTO claim_source_support (claim_id, source_registry_id, source_record_id, authenticity, support)
           VALUES (%s, %s, %s, %s, %s) ON CONFLICT (claim_id, source_record_id) DO UPDATE
               SET authenticity = EXCLUDED.authenticity, support = EXCLUDED.support, checked_at = now()""",
        (claim["claim_id"], claim["source_registry_id"], claim["source_record_id"],
         claim["source_authenticity_status"], claim["claim_support_status"]))


@_safe
def queue_review(answer: dict) -> None:
    for i, reason in enumerate(answer.get("review_reasons", [])):
        qid = store.short_id("RQ-", answer["investigation_id"], str(i), reason)
        kind = "cross_border" if reason.startswith("Cross-border") else "possible_match"
        store.conn().execute(
            """INSERT INTO review_queue (id, case_id, tenant_id, kind, subject, reasons, priority)
               VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""",
            (qid, answer["investigation_id"], answer.get("tenant_id") or "public", kind,
             Jsonb({"product": answer.get("product"), "lead_record": answer.get("lead_record")}),
             Jsonb([reason]), 1 if kind == "cross_border" else 2))


@_safe
def log_prediction(snapshot: str, product_key: str, outcome: str) -> None:
    """Append-only, hash-chained: each entry's hash covers the previous one, so a later edit is detectable."""
    conn = store.conn()
    prev = conn.execute("SELECT entry_hash FROM prediction_log ORDER BY id DESC LIMIT 1").fetchone()
    previous = prev["entry_hash"] if prev else ""
    now = datetime.now(UTC).isoformat()
    entry = hashlib.sha256(f"{previous}|{snapshot}|{product_key}|{outcome}|{now}".encode()).hexdigest()
    conn.execute("""INSERT INTO prediction_log (snapshot_id, product_key, outcome, predicted_at, previous_hash,
                                                entry_hash) VALUES (%s, %s, %s, %s, %s, %s)""",
                 (snapshot, product_key, outcome, now, previous, entry))


def snapshots(investigation_id: str) -> list[dict]:
    return store.conn().execute(
        "SELECT id, outcome, output, created_at FROM assessment_snapshots WHERE investigation_id = %s "
        "ORDER BY created_at DESC", (investigation_id,)).fetchall()


def product_snapshots(product_id: str, limit: int = 10) -> list[dict]:
    return store.conn().execute(
        "SELECT id, outcome, policy_version, source_mode, created_at, output->'coverage'->'summary' AS coverage "
        "FROM assessment_snapshots WHERE product_id = %s ORDER BY created_at DESC LIMIT %s",
        (product_id, limit)).fetchall()


def coverage_for(investigation_id: str) -> list[dict]:
    return store.conn().execute(
        "SELECT source_id, country, state, mode, checked_at, freshness, detail FROM coverage_checks "
        "WHERE investigation_id = %s ORDER BY id", (investigation_id,)).fetchall()


def fetches_for(query_keys: list[str]) -> list[dict]:
    return store.conn().execute(
        "SELECT adapter, fetched_at, status, latency_ms, raw_hash, mode, detail FROM source_fetches "
        "WHERE query_hash = ANY(%s) ORDER BY fetched_at DESC LIMIT 50", (query_keys,)).fetchall()


# --- jobs ------------------------------------------------------------------------------------------------------

@_safe
def create_job(job_id: str, tenant_id: str, request: dict) -> None:
    store.conn().execute(
        "INSERT INTO investigation_jobs (id, tenant_id, status, request) VALUES (%s, %s, 'queued', %s) "
        "ON CONFLICT (id) DO NOTHING", (job_id, tenant_id, Jsonb(request)))


@_safe
def update_job(job_id: str, status: str, snapshot: str | None = None, error: str | None = None) -> None:
    store.conn().execute(
        "UPDATE investigation_jobs SET status = %s, snapshot_id = coalesce(%s, snapshot_id), error = %s, "
        "updated_at = now() WHERE id = %s", (status, snapshot, error, job_id))


def job(job_id: str) -> dict | None:
    row = store.conn().execute(
        """SELECT j.*, s.output FROM investigation_jobs j LEFT JOIN assessment_snapshots s ON s.id = j.snapshot_id
           WHERE j.id = %s""", (job_id,)).fetchone()
    if row and row["status"] in ("queued", "running") and \
            (datetime.now(UTC) - row["updated_at"]).total_seconds() > 600:
        update_job(job_id, "failed", error="interrupted (the server restarted); start the investigation again")
        row = {**row, "status": "failed", "error": "interrupted (the server restarted); start the investigation again"}
    return row


def json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def dumps(value) -> str:
    return json.dumps(value, default=json_default, ensure_ascii=False)
