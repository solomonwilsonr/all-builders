"""Case file for GET /v1/products/{id}/case-file: one exportable record of why SafeShelf flagged a product.

Built from the regulator evidence pack (engine.agents.copilot.evidence_pack), so every claim carries the evidence
IDs and exact review quotes behind it. The verdict and the rule that set it come from code, never from Gemini.
A case file is never sent anywhere: it waits for a person to review it (review_gate) and file it themselves.
"""
import logging
from datetime import UTC, datetime

from engine import radar
from engine.agents.copilot import REGULATORS, evidence_pack, region

log = logging.getLogger(__name__)
EVIDENCE_FIELDS = ("investigation_id", "snapshot_id", "outcome", "basis", "headline", "safety_concern",
                   "evidence_strength", "identity_confidence", "matches", "claims", "contradictions", "limitations",
                   "what_would_change", "review_required", "review_reasons", "policy_version", "source_mode",
                   "retrieved_at")

LABEL = "AI findings for review by a person - not a regulatory determination"
VERDICT_WORDS = {"red": "Red: officially recalled", "amber": "Amber: hazard reports worth a person's review",
                 "green": "Green: checked, nothing found", "not_enough_evidence": "Not enough evidence"}


def verdict_rule(verdict: str, recall_ids: list[str], reviews_checked: int) -> str:
    """The code rule (engine.radar.verdict) that produced this verdict, in plain words."""
    if verdict == "red":
        return f"Red because this exact model is on an official recall list ({', '.join(recall_ids)})."
    if verdict == "amber":
        return ("Amber because at least one medium- or high-severity hazard has two or more independent first-hand "
                "reports, or one with a photo. Not recalled.")
    if verdict == "green":
        return f"Green because {reviews_checked} reviews were read and no hazard reached the amber rule."
    return f"Not enough evidence: fewer than {radar.MIN_REVIEWS} reviews to read."


def _findings(pack: dict) -> list[dict]:
    quotes = {q["evidence_id"]: q for q in pack["review_quotes"]}
    return [{**f, "quotes": [quotes[i] for i in f.get("evidence_ids", []) if i in quotes][:4]}
            for f in pack["hazard_findings"]]


def _ids(ids: list[str], shown: int = 10) -> str:
    more = f" and {len(ids) - shown} more (full list in the JSON)" if len(ids) > shown else ""
    return ", ".join(ids[:shown]) + more


def _trim(quote: str, limit: int = 300) -> str:
    return quote if len(quote) <= limit else quote[:limit].rsplit(" ", 1)[0] + " …"


def markdown(case: dict) -> str:
    """The same case as a printable page (the screens offer it as a download)."""
    p = case["product"]
    category = (p["category"] or "").replace("_", " ")
    lines = [f"# SafeShelf case file {case['case_file_id']}", "",
             f"**Product:** {p['brand']} {p['model']} ({category}) · `{case['product_id']}`",
             f"**Created:** {case['created_at']}",
             f"**Verdict:** {VERDICT_WORDS.get(case['verdict'], case['verdict'])}",
             f"**Why (rule set by code):** {case['decided_by']['rule']}",
             "**Status:** awaiting review by a person. Nothing has been sent to anyone.", ""]
    if case["linked_recalls"]:
        lines += ["## Official recalls", ""]
        lines += [f"- {r['recall_id']} ({r['notice_date']}, {r['match']}): {r['title']} {r['url'] or ''}"
                  for r in case["linked_recalls"]]
        lines.append("")
    lines += ["## Hazard findings", ""]
    if not case["findings"]:
        lines += ["None.", ""]
    for f in case["findings"]:
        lines += [f"### {f['hazard_type'].replace('_', ' ')}: {f['mechanism']}",
                  (f"{f['independent_reports']} independent report(s), {f['with_photos']} with photos, severity "
                  f"{f['severity']}, first seen {f['first_seen']}, trend {f.get('trend', 'n/a')}."),
                  f"Evidence: {_ids(f.get('evidence_ids', []))}", ""]
        lines += [f"> \"{_trim(q['quote'])}\" ({q['evidence_id']}, {q.get('date') or 'date unknown'})"
                  for q in f["quotes"]]
        lines.append("")
    if case["same_hardware"]:
        lines += ["## Same hardware sold under other listings", ""]
        lines += [f"- {r['target_id']}: {r['relationship'].replace('_', ' ')} ({r['status']})"
                  for r in case["same_hardware"]]
        lines.append("")
    ev = case.get("evidence") or {}
    if ev:
        lines += ["## Verified evidence (plan v2.2)", "",
                  f"**Outcome (set by code):** {ev.get('outcome', '').replace('_', ' ')} · {ev.get('headline', '')}",
                  f"**Coverage:** {ev.get('coverage_summary') or 'n/a'}",
                  (f"**Evidence strength:** {ev.get('evidence_strength')} · **Identity:** "
                   f"{ev.get('identity_confidence')} · **Policy:** {ev.get('policy_version')}"), ""]
        for m in ev.get("matches", [])[:8]:
            lines.append(f"- {m['authority']} {m['record_id']} ({m.get('published') or 'undated'}): {m['tier']}, "
                         f"{m['scope'].replace('_', ' ')}, {'local' if m['local'] else 'foreign'}, source "
                         f"{m['authenticity'].replace('_', ' ')}, text {m['support']} {m.get('url') or ''}")
        for c in ev.get("contradictions", [])[:5]:
            lines.append(f"- Contradiction ({c['kind'].replace('_', ' ')}, {c['effect']}): {c['text']}")
        for limit in ev.get("limitations", []):
            lines.append(f"- Limitation: {limit}")
        lines.append("")
    lines += ["## Where to file it", "", f"{case['regulator']['name']}: {case['regulator']['url']}", "",
              "Reviewer names and contact details are not included.", "", f"_{LABEL}_"]
    return "\n".join(lines)


def case_file(product_id: str) -> dict:
    pack = evidence_pack(product_id)  # KeyError for an unknown product
    status = pack["official_status"] or {}
    case = {
        "case_file_id": pack["evidence_pack_id"],
        "product_id": product_id,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "product": pack["product"],
        "listings": pack["listings"],
        "verdict": pack["verdict"],
        "decided_by": {"verdict": "code",
                       "rule": verdict_rule(pack["verdict"], status.get("recall_ids", []), pack["reviews_checked"]),
                       "ai_role": "Gemini read the reviews and photos; it did not set the verdict"},
        "official_status": status,
        "findings": _findings(pack),
        "linked_recalls": pack["linked_recalls"],
        "same_hardware": pack["same_hardware"],
        "reviews_checked": pack["reviews_checked"],
        "review_gate": {"status": "awaiting_human_review", "requires_human_approval": True, "submitted": False,
                        "next_step": "A person checks each finding against its evidence, then files the report "
                                     "on the regulator's own site."},
        "regulator": REGULATORS[region({"listings": pack["listings"]})],
        "privacy": "No reviewer names or contact details are included.",
        "label": LABEL,
    }
    case["evidence"] = verified_evidence(product_id)
    if case["evidence"].get("review_required"):
        case["review_gate"]["reviewer_status"] = "queued: " + "; ".join(case["evidence"].get("review_reasons", []))
    case["markdown"] = markdown(case)
    return case


def verified_evidence(product_id: str) -> dict:
    """The live investigation for this product (official sources, scope checks, contradictions, the code's outcome),
    with an evidence timeline and how earlier assessments differed. Empty if the sources could not be consulted."""
    try:
        from engine import assessments, investigation
        answer = investigation.investigate({"product_id": product_id})
    except Exception as error:  # noqa: BLE001  the case file stands on the evidence pack without it
        log.warning("case file without verified evidence: %s", type(error).__name__)
        return {}
    timeline = sorted(
        [{"date": m.get("published"), "event": f"{m['authority']} published {m['record_id']}: {m['title'][:120]}",
          "record_id": m["record_id"]} for m in answer.get("matches", []) if m.get("published")]
        + [{"date": h.get("first_seen"), "event": f"first {h['hazard_type'].replace('_', ' ')} report from a buyer"}
           for h in answer.get("hazards", []) if h.get("first_seen")],
        key=lambda e: e["date"] or "")
    try:
        history = [{"snapshot_id": r["id"], "outcome": r["outcome"], "at": r["created_at"].isoformat(),
                    "policy_version": r["policy_version"], "source_mode": r["source_mode"]}
                   for r in assessments.product_snapshots(product_id)]
    except Exception:  # noqa: BLE001
        history = []
    out = {k: answer.get(k) for k in EVIDENCE_FIELDS}
    return {**out, "coverage_summary": answer.get("coverage", {}).get("summary"),
            "coverage": answer.get("coverage", {}).get("countries", []), "timeline": timeline,
            "assessment_history": history,
            "why_it_changed": "Each row in assessment_history is a stored snapshot; compare two to see which sources, "
                              "claims or policy version changed the outcome."}
