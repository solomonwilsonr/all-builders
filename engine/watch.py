"""Post-purchase monitoring (plan v2.2 workstream F): watchlists, scheduled rechecks, scoped alerts.

A watchlist item is a product (or brand + model + batch + market) a shopper saved, held under a hashed owner id
within one tenant. A recheck runs the live investigation again; an alert is raised only when the outcome gets worse
for that exact model/batch (new concern, worsened), or when an earlier concern is withdrawn (correction / retraction
alerts). The same alert is never sent twice (dedupe key), and deleting an item removes its query.
"""
import hashlib

from psycopg.types.json import Jsonb

from engine import store, webhooks

SEVERITY = {"no_matching_notice_found": 0, "insufficient_evidence": 0, "potential_concern": 1,
            "substantiated_hazard_signal": 2, "confirmed_recall": 3}
QUERY_FIELDS = ("product_id", "brand", "model", "gtin", "batch", "market", "title", "url")


def _id(*parts: str) -> str:
    return store.short_id("WL-", *parts)


def create(tenant_id: str, owner_ref: str | None, body: dict) -> dict:
    if not owner_ref:
        raise ValueError("send X-Owner-Ref (the screen's user id; SafeShelf stores only a hash)")
    query = {k: body.get(k) for k in QUERY_FIELDS if body.get(k)}
    if not (query.get("product_id") or query.get("model") or query.get("brand")):
        raise ValueError("give a product_id, or a brand and model")
    wid = _id(tenant_id, owner_ref, *(str(query.get(k) or "") for k in QUERY_FIELDS))
    store.conn().execute(
        """INSERT INTO watchlists (id, tenant_id, owner_ref, product_id, query, notify) VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (id) DO UPDATE SET deleted_at = NULL, notify = EXCLUDED.notify""",
        (wid, tenant_id, owner_ref, query.get("product_id"), Jsonb(query), bool(body.get("notify", True))))
    return {"watchlist_id": wid, "query": query, "notify": bool(body.get("notify", True)),
            "note": "SafeShelf re-checks saved products and alerts only for this exact model and batch."}


def items(tenant_id: str, owner_ref: str | None) -> dict:
    rows = store.conn().execute(
        """SELECT id, product_id, query, last_outcome, last_snapshot_id, notify, created_at FROM watchlists
           WHERE tenant_id = %s AND owner_ref = %s AND deleted_at IS NULL ORDER BY created_at DESC""",
        (tenant_id, owner_ref or "")).fetchall()
    return {"items": [{**r, "watchlist_id": r.pop("id"), "created_at": r["created_at"].isoformat()} for r in rows]}


def delete(tenant_id: str, owner_ref: str | None, watchlist_id: str) -> dict:
    row = store.conn().execute(
        """UPDATE watchlists SET deleted_at = now(), query = '{}'::jsonb, product_id = NULL, notify = false
           WHERE id = %s AND tenant_id = %s AND owner_ref = %s AND deleted_at IS NULL RETURNING id""",
        (watchlist_id, tenant_id, owner_ref or "")).fetchone()
    if not row:
        raise KeyError(watchlist_id)
    return {"watchlist_id": watchlist_id, "deleted": True, "note": "The saved product details were removed."}


def alert_for(previous: str | None, answer: dict) -> dict | None:
    """What changed, worth telling the owner? None if nothing worth a message."""
    now = answer["outcome"]
    before = SEVERITY.get(previous or "", 0)
    after = SEVERITY.get(now, 0)
    lead = answer.get("lead_record") or {}
    if after > before:
        kind = "new_concern" if before == 0 else "worsened"
    elif before > after and previous is not None:
        retracted = any(c.get("kind") == "retraction" for c in answer.get("contradictions", []))
        kind = "retraction" if retracted else "correction"
    else:
        return None
    return {"kind": kind, "outcome": now, "previous_outcome": previous, "headline": answer.get("headline"),
            "lead_record": lead, "coverage": answer.get("coverage", {}).get("summary"),
            "what_would_change": answer.get("what_would_change", [])[:2]}


def recheck(limit: int = 50) -> dict:
    """Re-investigate the oldest-checked watchlist items; raise deduplicated alerts and send them to webhooks."""
    from engine import investigation

    rows = store.conn().execute(
        """SELECT id, tenant_id, owner_ref, query, last_outcome FROM watchlists
           WHERE deleted_at IS NULL ORDER BY coalesce(last_snapshot_id, '') ASC, created_at ASC LIMIT %s""",
        (limit,)).fetchall()
    sent, checked = 0, 0
    for row in rows:
        answer = investigation.investigate({**row["query"], "skip_reviews": not row["query"].get("product_id")},
                                           tenant_id=row["tenant_id"])
        checked += 1
        alert = alert_for(row["last_outcome"], answer)
        store.conn().execute("UPDATE watchlists SET last_outcome = %s, last_snapshot_id = %s WHERE id = %s",
                             (answer["outcome"], answer.get("snapshot_id"), row["id"]))
        if not alert:
            continue
        lead = (alert["lead_record"] or {}).get("record_id") or ""
        dedupe = hashlib.sha1(f"{row['id']}|{alert['kind']}|{alert['outcome']}|{lead}".encode()).hexdigest()
        inserted = store.conn().execute(
            """INSERT INTO notification_events (id, tenant_id, watchlist_id, kind, dedupe_key, body)
               VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (tenant_id, dedupe_key) DO NOTHING RETURNING id""",
            (store.short_id("NE-", dedupe), row["tenant_id"], row["id"], alert["kind"], dedupe,
             Jsonb({**alert, "owner_ref": row["owner_ref"]}))).fetchone()
        if inserted:
            sent += 1
            webhooks.emit(row["tenant_id"], "watchlist.alert",
                          {"watchlist_id": row["id"], "owner_ref": row["owner_ref"], **alert})
    return {"checked": checked, "alerts": sent}


def notifications(tenant_id: str, owner_ref: str | None, limit: int = 20) -> list[dict]:
    rows = store.conn().execute(
        """SELECT n.id, n.kind, n.body, n.created_at FROM notification_events n
           LEFT JOIN watchlists w ON w.id = n.watchlist_id
           WHERE n.tenant_id = %s AND (w.owner_ref = %s OR n.owner_ref = %s)  -- recall alerts and household reminders
           ORDER BY n.created_at DESC LIMIT %s""",
        (tenant_id, owner_ref or "", owner_ref or "", limit)).fetchall()
    return [{**r, "created_at": r["created_at"].isoformat()} for r in rows]
