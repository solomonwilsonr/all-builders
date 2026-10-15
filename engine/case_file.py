"""Case file for GET /v1/products/{id}/case-file: one exportable record of why SafeShelf flagged a product.

Built from the regulator evidence pack (engine.agents.copilot.evidence_pack), so every claim carries the evidence
IDs and exact review quotes behind it. The verdict and the rule that set it come from code, never from Gemini.
A case file is never sent anywhere: it waits for a person to review it (review_gate) and file it themselves.
"""
from datetime import UTC, datetime

from engine import radar
from engine.agents.copilot import REGULATORS, evidence_pack, region

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
    case["markdown"] = markdown(case)
    return case
