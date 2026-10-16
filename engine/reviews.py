"""Human adjudication (plan v2.2 workstreams G and J1): the reviewer queue, decisions with rationale, second review
for high-impact cases, and the effect of each decision. Reviewer-only, tenant-scoped, audited.

Cross-border matches need two different reviewers before they count ("second_review"); a reviewer can approve,
correct or reject a product match, a hazard inference, a cross-border propagation or a shopper's report. Nothing is
published or sent to a regulator from here: a decision changes SafeShelf's own records.
"""
from psycopg.types.json import Jsonb

from engine import store, webhooks

DECISIONS = ("approve", "correct", "reject", "escalate")
SECOND_REVIEW = {"cross_border"}
REPORT_OUTCOMES = {"approve": "substantiated", "reject": "unsubstantiated", "correct": "inconclusive",
                   "escalate": "investigating"}


def queue(tenant_id: str, state: str = "open", limit: int = 50) -> dict:
    states = ("open", "assigned", "second_review") if state == "open" else (state,)
    rows = store.conn().execute(
        """SELECT id, case_id, kind, subject, reasons, state, assigned_to, priority, created_at FROM review_queue
           WHERE tenant_id = ANY(%s) AND state = ANY(%s) ORDER BY priority, created_at LIMIT %s""",
        ([tenant_id, "public"] if tenant_id == "internal" else [tenant_id], list(states), limit)).fetchall()
    return {"items": [{**r, "queue_id": r.pop("id"), "created_at": r["created_at"].isoformat()} for r in rows],
            "state": state}


def _audit(entity_id: str, entity_type: str, actor: str, before, after) -> None:
    store.conn().execute(
        """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, before, after)
           VALUES (%s, %s, 'review', %s, %s, %s)""", (entity_id, entity_type, actor, Jsonb(before), Jsonb(after)))


def decide(tenant_id: str, reviewer_ref: str, case_id: str, body: dict) -> dict:
    """Decide the open queue items of a case (or one item: body.queue_id)."""
    decision = body.get("decision")
    rationale = (body.get("rationale") or "").strip()
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of {DECISIONS}")
    if len(rationale) < 10:
        raise ValueError("give a rationale (at least a sentence): decisions are audited")
    sql = """SELECT * FROM review_queue WHERE case_id = %s AND state <> 'decided' AND tenant_id = ANY(%s)"""
    params: list = [case_id, [tenant_id, "public"] if tenant_id == "internal" else [tenant_id]]
    if body.get("queue_id"):
        sql += " AND id = %s"
        params.append(body["queue_id"])
    items = store.conn().execute(sql, params).fetchall()
    if not items:
        raise KeyError(case_id)
    out = []
    for item in items:
        earlier = store.conn().execute(
            "SELECT reviewer_ref, decision FROM review_decisions WHERE queue_id = %s ORDER BY at", (item["id"],)
        ).fetchall()
        if any(e["reviewer_ref"] == reviewer_ref for e in earlier):
            raise ValueError("this reviewer already decided this item; a second review needs another person")
        second = item["kind"] in SECOND_REVIEW and decision == "approve" and not earlier
        store.conn().execute(
            """INSERT INTO review_decisions (queue_id, reviewer_ref, decision, correction, rationale, second_review)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (item["id"], reviewer_ref, decision, Jsonb(body.get("correction")), rationale, bool(earlier)))
        state = "second_review" if second else "decided"
        store.conn().execute("UPDATE review_queue SET state = %s, decided_at = CASE WHEN %s = 'decided' THEN now() "
                             "END WHERE id = %s", (state, state, item["id"]))
        if state == "decided":
            apply(item, decision, reviewer_ref, body.get("correction"))
        _audit(item["id"], "review_queue", reviewer_ref, {"state": item["state"]},
               {"state": state, "decision": decision, "rationale": rationale})
        out.append({"queue_id": item["id"], "kind": item["kind"], "decision": decision, "state": state,
                    "needs_second_reviewer": second})
    webhooks.emit(tenant_id, "review.decided", {"case_id": case_id, "items": out})
    return {"case_id": case_id, "decided": out}


def apply(item: dict, decision: str, reviewer_ref: str, correction: dict | None) -> None:
    """What a final decision changes: scope reviews, identity edges, the case lifecycle."""
    subject = item["subject"] or {}
    lead = subject.get("lead_record") or {}
    product = subject.get("product") or {}
    store.conn().execute(
        """INSERT INTO identity_scope_reviews (product_key, source_record_id, tier, scope, local, reasons,
                                               reviewer_ref, decision)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (product.get("key") or "", lead.get("record_id") or "", (correction or {}).get("tier") or lead.get("tier")
         or "", lead.get("scope") or "", lead.get("local"), Jsonb(item.get("reasons")), reviewer_ref, decision))
    store.conn().execute(
        """INSERT INTO reviewer_decisions (subject_type, subject_id, decision, correction, reviewer_ref, rationale)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (item["kind"], item["case_id"], decision, Jsonb(correction), reviewer_ref, "see review_decisions"))
    lifecycle = {"approve": "substantiated", "reject": "unsubstantiated", "correct": "inconclusive",
                 "escalate": "investigating"}[decision]
    store.conn().execute("UPDATE investigations SET lifecycle = %s, updated_at = now() WHERE id = %s",
                         (lifecycle, item["case_id"]))


def review_report(tenant_id: str, reviewer_ref: str, report_id: str, body: dict) -> dict:
    decision = body.get("decision")
    rationale = (body.get("rationale") or "").strip()
    if decision not in DECISIONS or len(rationale) < 10:
        raise ValueError(f"give a decision ({', '.join(DECISIONS)}) and a rationale")
    row = store.conn().execute("SELECT id, status FROM reports WHERE id = %s", (report_id,)).fetchone()
    if not row:
        raise KeyError(report_id)
    status = REPORT_OUTCOMES[decision]
    store.conn().execute("UPDATE reports SET status = %s WHERE id = %s", (status, report_id))
    store.conn().execute(
        """INSERT INTO reviewer_decisions (subject_type, subject_id, decision, correction, reviewer_ref, rationale)
           VALUES ('report', %s, %s, %s, %s, %s)""",
        (report_id, decision, Jsonb(body.get("correction")), reviewer_ref, rationale))
    _audit(report_id, "report", reviewer_ref, {"status": row["status"]}, {"status": status, "rationale": rationale})
    return {"report_id": report_id, "status": status, "previous_status": row["status"], "decision": decision,
            "note": "A shopper's report is an allegation until a reviewer substantiates it; nothing is published."}
