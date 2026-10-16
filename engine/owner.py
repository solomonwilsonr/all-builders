"""Owner guidance for GET /v1/products/{id}/owner-guidance: "Already bought it?" (My Shelf, after purchase).

What to do now if you own this product: stop or take care, get the recall remedy, return it, report it, or
switch to a safer option. Every step comes from code rules on the safety answer (verdict, recalls, hazard
findings); no new Gemini text. Steps point at the same evidence IDs as the safety answer.
"""
from engine import passport, safety
from engine.agents.copilot import REGULATORS, region

LABEL = "Guidance from AI findings and official recalls - not a regulatory determination or legal advice"

# What an owner can check or do for each Safety Radar hazard type (engine.radar.HAZARDS).
PRECAUTIONS = {
    "fire_burn": "Don't use it unattended, overnight, or on a bed or sofa, and unplug it when you're not using it. "
                 "Stop using it if it gets very hot, smells of burning, swells or shows scorch marks.",
    "electric_shock": "Unplug it at the wall before you touch or inspect it. Stop using it if the casing is cracked, "
                      "the cable is damaged or you feel a tingle.",
    "choking": "Keep it away from children under 3 until you've checked it for loose or detachable small parts.",
    "chemical": "Stop using it if it leaks, smells strongly or irritates your skin. Keep it away from children "
                "and wash your hands after handling it.",
    "mechanical_injury": "Check for sharp edges and loose or broken parts before each use.",
    "other": "Check yours for the problem other buyers describe below.",
}
MAX_HAZARDS = 3  # the most serious, most reported problems; the full list is in the safety answer
DISPOSAL = ("Don't put it in household waste: products with batteries or mains wiring go to an e-waste "
            "collection point.")


def _step(title: str, detail: str, **extra) -> dict:
    return {"title": title, "detail": detail, **{k: v for k, v in extra.items() if v}}


def _recalled_steps(recalls: list[dict]) -> list[dict]:
    exact = [r for r in recalls if r["match"] == "matches a recall"]
    steps = [_step("Stop using it now", "This model is on an official recall list. Unplug it and put it away "
                                        "from children until you've followed the recall instructions.")]
    for r in exact:
        steps.append(_step(f"Get the recall remedy ({r['authority']} {r['recall_id']})",
                           "The notice says what you get (refund, repair or replacement) and how to claim it. "
                           "Keep the product and your receipt until then.", url=r["url"]))
    steps.append(_step("Dispose of it safely", DISPOSAL))
    return steps


def _check_recall_steps(found: dict) -> list[dict]:
    """A recall that may cover the owner's unit but isn't confirmed for it: abroad, or here for some batches only."""
    lead = found.get("lead_record") or {}
    where = lead.get("authority") or "a regulator"
    steps = [_step("Compare your label with the notice",
                   f"{where} recalled {lead.get('title') or 'a product with this model number'}. Check that the model "
                   "number on your label matches exactly, and look for the serial, lot or date code the notice lists.",
                   url=lead.get("url"))]
    if found.get("basis") == "recalled_abroad_same_model":
        steps.append(_step("Ask the seller whether your country's version is affected",
                           "A recall in another country can still apply to the same hardware sold here. Until you "
                           "know, stop charging it overnight or unattended."))
    else:
        steps.append(_step("If your unit is in the affected range, stop using it",
                           "Follow the notice's remedy (refund, repair or replacement)."))
    return steps


def _hazard_steps(findings: list[dict], recalls: list[dict]) -> list[dict]:
    steps = [_step(f"Check whether yours is covered by this recall ({r['authority']} {r['recall_id']})",
                   "The notice may cover your model, but SafeShelf could not confirm it from the model number. "
                   "Compare the model number on your label with the notice.", url=r["url"])
             for r in recalls if r["match"] != "matches a recall"]
    top = sorted(findings, key=lambda f: (("high", "medium", "low").index(f["severity"]), -f["independent_reports"]))
    for f in top[:MAX_HAZARDS]:
        photos = f", {f['with_photos']} with photos" if f["with_photos"] else ""
        steps.append(_step(f"Check yours for: {f['mechanism']}",
                           f"{f['independent_reports']} buyers reported this{photos}. "
                           + PRECAUTIONS.get(f["hazard_type"], PRECAUTIONS["other"]),
                           evidence_ids=f.get("evidence_ids", [])[:5]))
    steps.append(_step("If yours shows the same problem, stop using it and ask for a return",
                       "Contact the seller or marketplace while the return window is open, and describe what "
                       "you saw. A photo helps."))
    return steps


def owner_guidance(product_id: str) -> dict:
    found = safety.safety(product_id)  # KeyError for an unknown product
    recalls = passport.history(product_id)["recalls"]
    product = passport.product(product_id)
    findings = found["ai_findings"]
    verdict = found["verdict"]
    if verdict == "red":
        situation, headline, steps = "recalled", "This product is officially recalled. Stop using it.", \
            _recalled_steps(recalls)
    elif found.get("basis") in ("recalled_abroad_same_model", "local_recall_batch_unknown"):
        situation, headline, steps = "recall_to_check", found["headline"] + ".", _check_recall_steps(found)
        steps += _hazard_steps(findings, []) if findings else []
    elif findings:
        situation = "hazard_reports"
        headline = ("Not recalled, but other buyers report safety problems. Check yours." if verdict == "amber" else
                    "Not recalled. A few buyers mention a problem; keep an eye on yours.")
        steps = _hazard_steps(findings, recalls)
    else:
        situation = "no_known_issue" if verdict == "green" else "not_enough_evidence"
        headline = ("No recalls or safety reports found for this product." if verdict == "green" else
                    "Too few reviews to judge yet, and no recalls found.")
        steps = []
    regulator = REGULATORS[region(product)]
    if situation != "no_known_issue":
        steps.append(_step("Report what happened to you", "If it hurt someone, overheated, sparked or broke "
                           "dangerously, report it. SafeShelf can pre-fill the regulator's form from its case "
                           "file; you check it and submit it yourself.", url=regulator["url"]))
    steps.append(_step("Save it to My Shelf", "SafeShelf tells you if it is recalled later."))
    alternatives = passport.alternatives(product_id)["alternatives"] \
        if situation in ("recalled", "recall_to_check", "hazard_reports") else []
    return {
        "product_id": product_id,
        "verdict": verdict,
        "situation": situation,
        "headline": headline,
        "steps": [{"n": n, **s} for n, s in enumerate(steps, 1)],
        "recalls": recalls,
        "regulator": regulator,
        "outcome": found.get("outcome"),
        "coverage": (found.get("coverage") or {}).get("summary"),
        "limitations": found.get("limitations", []),
        "safer_alternatives": alternatives[:2],
        "label": LABEL,
    }
