"""Investigation trace for the Lab (M7, contract: GET /v1/investigations/{id}/trace).

A screen or agent sends X-Investigation-Id with its API calls; each real answer becomes one step: the tool, the
models that answered, time, tokens and a one-line summary. Cost is an estimate from PRICES (USD per 1M tokens),
left null for models without a listed price.
"""
import os
import re

from engine import store

# Gemini 3.5 Flash on Vertex: $1.50 in / $9.00 out per 1M tokens (third-party listings, Oct 2026; not an official
# Google page). Override with SAFESHELF_PRICES="model=in/out,model=in/out".
PRICES = {"gemini-3.5-flash": (1.50, 9.00)}
PRICES.update({m: tuple(float(x) for x in p.split("/")) for m, p in
               (item.split("=") for item in os.environ.get("SAFESHELF_PRICES", "").split(",") if "=" in item)})
VALID_ID = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
TOOLS = {"identifyProduct": "identify", "findDuplicates": "duplicates", "getRelationships": "relationships",
         "getSafety": "safety", "getCertifications": "certifications", "trustCheck": "trust-check",
         "getProduct": "product", "getHistory": "history", "getAlternatives": "alternatives",
         "createReport": "report", "getBenchResults": "bench", "listingSafetyCheck": "listing safety",
         "startAgentSession": "agent session", "getEvidence": "evidence", "catalogScan": "catalog scan"}

def cost(calls: list[dict]) -> float | None:
    if not calls:
        return 0.0
    if any(c["model"] not in PRICES for c in calls):
        return None
    return round(sum(c["input_tokens"] * PRICES[c["model"]][0] + c["output_tokens"] * PRICES[c["model"]][1]
                     for c in calls) / 1e6, 6)


def summarize(operation_id: str, body: dict) -> str:
    """One line a judge can read, from the answer itself."""
    if operation_id == "identifyProduct":
        name = " ".join(x for x in (body.get("brand"), body.get("model")) if x) or "the listing"
        return (f"Identified {name} as {body.get('product_id')} "
                f"({body.get('identity_status')}, confidence {body.get('confidence')})")
    if operation_id == "findDuplicates":
        kinds = [m["relationship"].replace("_", " ") for m in body.get("matches", [])]
        return f"{len(kinds)} related product(s): {', '.join(kinds)}" if kinds else "No related products found"
    if operation_id == "getSafety":
        found = ", ".join(f"{f['independent_reports']} {f['hazard_type'].replace('_', '/')}"
                          for f in body.get("ai_findings", []))
        return f"Verdict {body.get('verdict')} from {body.get('reviews_checked')} reviews" + (f": {found}" if found
                                                                                                else "")
    if operation_id == "getCertifications":
        return "; ".join(f"{c['authority']} {c['result']}" for c in body.get("checks", [])) or "No safety marks claimed"
    if operation_id == "trustCheck":
        return body.get("summary") or ""
    if operation_id == "getAlternatives":
        alts = body.get("alternatives", [])
        return f"{len(alts)} safer alternative(s)" + (f", best {alts[0]['brand']} {alts[0]['model']}" if alts else "")
    if operation_id == "getHistory":
        return f"{len(body.get('events', []))} history events, {len(body.get('recalls', []))} linked recall(s)"
    if operation_id == "getProduct":
        return f"Read the product: {body.get('brand')} {body.get('model')} ({body.get('category')})"
    if operation_id == "getEvidence":
        return f"Read {len(body.get('items', []))} evidence record(s) and their exact quotes"
    if operation_id == "getRelationships":
        kinds = [r["relationship"].replace("_", " ") for r in body.get("relationships", [])]
        return f"{len(kinds)} related product(s): {', '.join(kinds)}" if kinds else "No related products on file"
    return TOOLS.get(operation_id, operation_id)


def record(investigation_id: str, operation_id: str, seconds: float, calls: list[dict], body: dict,
           summary: str | None = None) -> None:
    """summary: the caller's own line (agent steps); otherwise it is written from the answer."""
    conn = store.conn()
    conn.execute("""INSERT INTO investigations (id, status) VALUES (%s, 'open') ON CONFLICT (id) DO NOTHING""",
                 (investigation_id,))
    conn.execute(
        """INSERT INTO investigation_steps (investigation_id, n, tool, models, seconds, input_tokens, output_tokens,
                                           cost_usd, summary)
           SELECT %s, coalesce(max(n), 0) + 1, %s, %s, %s, %s, %s, %s, %s
           FROM investigation_steps WHERE investigation_id = %s""",
        (investigation_id, TOOLS.get(operation_id, operation_id), sorted({c["model"] for c in calls}),
         round(seconds, 2), sum(c["input_tokens"] for c in calls), sum(c["output_tokens"] for c in calls),
         cost(calls), (summary or summarize(operation_id, body))[:300], investigation_id))


def evidence_trail(investigation_id: str) -> dict:
    """Plan v2.2 J5: what the investigation checked and decided: each source and its state, the fetches behind them,
    which reports were grouped as one observation, contradictions, the policy version, and the review trail."""
    conn = store.conn()

    def rows(sql: str) -> list[dict]:
        try:  # tables from `make migrate`; an older database has no trail
            return [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()}
                    for r in conn.execute(sql, (investigation_id,)).fetchall()]
        except Exception:  # noqa: BLE001
            return []

    snaps = rows("SELECT id, outcome, policy_version, source_mode, source_cutoff, created_at, query FROM "
                 "assessment_snapshots WHERE investigation_id = %s ORDER BY created_at")
    return {
        "assessments": snaps,
        "coverage_checks": rows("SELECT source_id, country, state, mode, checked_at, freshness, detail FROM "
                                "coverage_checks WHERE investigation_id = %s ORDER BY id"),
        "observation_groups": rows("SELECT group_id, member_id, reason FROM observation_groups WHERE "
                                   "investigation_id = %s ORDER BY group_id"),
        "contradictions": rows("SELECT kind, record_id, text, effect FROM claim_contradictions WHERE "
                               "investigation_id = %s"),
        "review_trail": rows("SELECT q.id AS queue_id, q.kind, q.state, d.decision, d.rationale, d.second_review, "
                             "d.at FROM review_queue q LEFT JOIN review_decisions d ON d.queue_id = q.id "
                             "WHERE q.case_id = %s ORDER BY d.at NULLS FIRST"),
        "case_history": rows("SELECT from_state, to_state, rationale, at FROM case_reviews WHERE case_id = %s "
                             "ORDER BY at"),
        "adjudication": "engine/evidence_verification/adjudicator.py (code); policy version per assessment above",
    }


def get_trace(investigation_id: str) -> dict:
    rows = store.conn().execute(
        "SELECT * FROM investigation_steps WHERE investigation_id = %s ORDER BY n", (investigation_id,)).fetchall()
    trail = evidence_trail(investigation_id)
    if not rows and trail["assessments"]:  # a live investigation (POST /v1/investigations) has no agent steps
        return {"investigation_id": investigation_id, "steps": [], "evidence_trail": trail,
                "totals": {"seconds": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0, "unpriced_models": [],
                           "cost_note": "no model calls: official sources and code only"}}
    if not rows:
        raise KeyError(investigation_id)
    steps = [{"n": r["n"], "tool": r["tool"], "model": ", ".join(r["models"]) or None, "seconds": r["seconds"],
              "input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"], "cost_usd": r["cost_usd"],
              "summary": r["summary"], "at": r["at"].isoformat()} for r in rows]
    unpriced = sorted({m for r in rows for m in r["models"] if m not in PRICES})
    return {
        "investigation_id": investigation_id,
        "steps": steps,
        "totals": {"seconds": round(sum(s["seconds"] or 0 for s in steps), 2),
                   "input_tokens": sum(s["input_tokens"] for s in steps),
                   "output_tokens": sum(s["output_tokens"] for s in steps),
                   "cost_usd": round(sum(s["cost_usd"] or 0 for s in steps), 6),
                   "unpriced_models": unpriced,
                   "cost_note": "estimate from listed per-token prices; calls to unpriced models are not included"},
        "evidence_trail": trail,
    }
