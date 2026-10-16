"""Safety case lifecycle (plan v2.2 workstream G): candidate -> triage -> investigating ->
substantiated / unsubstantiated / inconclusive -> action_pending -> resolved, and reopened from any closed state.

Every transition is a reviewer's, with a rationale, audited and reversible (reopen). Actions that reach outside
SafeShelf (a regulator form, an owner notice, a public correction) are prepared here but stay "pending" until the
shopper or a reviewer confirms them; a public-facing accusation is never published from weak evidence.
"""
from psycopg.types.json import Jsonb

from engine import store, webhooks

TRANSITIONS = {
    None: {"candidate", "triage"},
    "candidate": {"triage", "unsubstantiated"},
    "triage": {"investigating", "unsubstantiated", "inconclusive"},
    "investigating": {"substantiated", "unsubstantiated", "inconclusive"},
    "substantiated": {"action_pending", "resolved", "reopened"},
    "unsubstantiated": {"reopened", "resolved"},
    "inconclusive": {"investigating", "reopened", "resolved"},
    "action_pending": {"resolved", "reopened"},
    "resolved": {"reopened"},
    "reopened": {"triage", "investigating"},
}
ACTIONS = {"prefill_regulator_form": "the shopper reviews and submits it on the regulator's own site",
           "notify_owners": "sent only for the exact affected model and batch, after review",
           "publish_correction": "a correction or retraction of an earlier SafeShelf finding"}
NEEDS_SUBSTANTIATED = {"notify_owners"}


def state(case_id: str) -> str | None:
    row = store.conn().execute("SELECT lifecycle FROM investigations WHERE id = %s", (case_id,)).fetchone()
    if row is None:
        raise KeyError(case_id)
    return row["lifecycle"]


def transition(case_id: str, to_state: str, reviewer_ref: str, rationale: str, tenant_id: str = "public") -> dict:
    current = state(case_id)
    if to_state not in TRANSITIONS.get(current, set()):
        raise ValueError(f"a case can't go from {current or 'new'} to {to_state}; allowed: "
                         f"{sorted(TRANSITIONS.get(current, set()))}")
    if len((rationale or "").strip()) < 10:
        raise ValueError("give a rationale (at least a sentence)")
    store.conn().execute("UPDATE investigations SET lifecycle = %s, updated_at = now() WHERE id = %s",
                         (to_state, case_id))
    store.conn().execute(
        "INSERT INTO case_reviews (case_id, from_state, to_state, reviewer_ref, rationale) VALUES (%s, %s, %s, %s, %s)",
        (case_id, current, to_state, reviewer_ref, rationale))
    store.conn().execute(
        """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, before, after)
           VALUES (%s, 'case', 'transition', %s, %s, %s)""",
        (case_id, reviewer_ref, Jsonb({"lifecycle": current}), Jsonb({"lifecycle": to_state, "why": rationale})))
    webhooks.emit(tenant_id, "case.updated", {"case_id": case_id, "from": current, "to": to_state})
    return {"case_id": case_id, "from": current, "to": to_state, "history": history(case_id)}


def history(case_id: str) -> list[dict]:
    rows = store.conn().execute(
        "SELECT from_state, to_state, reviewer_ref, rationale, at FROM case_reviews WHERE case_id = %s ORDER BY at",
        (case_id,)).fetchall()
    return [{**r, "at": r["at"].isoformat()} for r in rows]


def prepare_action(case_id: str, action: str, actor_ref: str, payload: dict | None = None) -> dict:
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {sorted(ACTIONS)}")
    current = state(case_id)
    if action in NEEDS_SUBSTANTIATED and current not in ("substantiated", "action_pending"):
        raise ValueError("owners are notified only about a substantiated case")
    row = store.conn().execute(
        "INSERT INTO case_actions (case_id, action, status, payload, actor_ref) VALUES (%s, %s, 'pending', %s, %s) "
        "RETURNING id", (case_id, action, Jsonb(payload or {}), actor_ref)).fetchone()
    return {"case_id": case_id, "action_id": row["id"], "action": action, "status": "pending",
            "next_step": ACTIONS[action]}


def confirm_action(case_id: str, action_id: int, actor_ref: str) -> dict:
    row = store.conn().execute(
        "UPDATE case_actions SET status = 'confirmed_by_user', actor_ref = %s WHERE id = %s AND case_id = %s "
        "AND status = 'pending' RETURNING action", (actor_ref, action_id, case_id)).fetchone()
    if not row:
        raise KeyError(f"{case_id}/{action_id}")
    return {"case_id": case_id, "action_id": action_id, "action": row["action"], "status": "confirmed_by_user",
            "note": "Confirmed by a person. SafeShelf never submits to a regulator on its own."}


def case(case_id: str) -> dict:
    current = state(case_id)
    actions = store.conn().execute(
        "SELECT id, action, status, at FROM case_actions WHERE case_id = %s ORDER BY at", (case_id,)).fetchall()
    return {"case_id": case_id, "lifecycle": current, "allowed_next": sorted(TRANSITIONS.get(current, set())),
            "history": history(case_id),
            "actions": [{**a, "action_id": a.pop("id"), "at": a["at"].isoformat()} for a in actions]}
