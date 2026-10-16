"""Evidence-quality benchmark (plan v2.2 J6): synthetic red-team fixtures through the real verification code.

    cd engine && PYTHONPATH=.. uv run python ../bench/evidence_eval.py      (make bench-evidence)

Measures: unsupported-confirmation rate, lookalike propagation, copied-report inflation, contradiction recall,
appropriate abstention, exact-scope match precision and outcome agreement, with sample sizes. Fixtures are invented
hard cases (bench/fixtures/evidence/), so these numbers show the policy behaves as designed, not real-world accuracy.
"""
import json
from pathlib import Path

from bench import runlog
from engine import investigation
from engine.evidence_verification import adjudicator, contradictions

FIXTURES = Path(__file__).parent / "fixtures" / "evidence" / "redteam.json"
OUT = Path(__file__).parent / "evidence_results.json"


def run_case(case: dict) -> dict:
    market = case["market"]
    product = case["product"]
    records = case.get("records", [])
    found = contradictions.find(product, records)
    matches = investigation.verify(product, records, market, found)
    rows = [{"country": market, "name": market, "is_market": True, "state": case.get("market_state",
                                                                                     "no_matching_notice_found"),
             "notes": []}]
    decision = adjudicator.decide(market, market, product, matches, case.get("hazards", []), rows, 30, 20)
    exp = case["expected"]
    ok = (exp.get("outcome") in (None, decision["outcome"]) and exp.get("basis") in (None, decision["basis"])
          and decision["outcome"] != exp.get("not_outcome"))
    return {"id": case["id"], "category": case["category"], "outcome": decision["outcome"], "basis": decision["basis"],
            "expected": exp, "pass": ok, "contradictions": [c["kind"] for c in found],
            "review_required": decision["review_required"], "tiers": [m["tier"] for m in matches],
            "hard_negative": bool(case.get("hard_negative")),
            "contradiction_expected": bool(case.get("contradiction_expected"))}


def main() -> None:
    cases = json.loads(FIXTURES.read_text())["cases"]
    results = [run_case(c) for c in cases]
    negatives = [r for r in results if r["hard_negative"]]
    wanted = [r for r in results if r["contradiction_expected"]]
    exact = [r for r in results if "exact" in r["tiers"]]
    abstain = [r for r in results if r["expected"].get("outcome") == "insufficient_evidence"]
    metrics = {
        "cases": len(results), "passed": sum(r["pass"] for r in results),
        "unsupported_confirmation_rate": round(sum(r["outcome"] == "confirmed_recall" for r in negatives)
                                               / max(len(negatives), 1), 3),
        "lookalike_propagation": sum(r["category"] == "identical_wrong_model"
                                     and r["outcome"] != "no_matching_notice_found" for r in results),
        "copied_report_inflation": sum(r["category"] == "syndicated_complaint" and r["outcome"] ==
                                       "substantiated_hazard_signal" for r in results),
        "contradiction_recall": round(sum(bool(r["contradictions"]) for r in wanted) / max(len(wanted), 1), 3),
        "appropriate_abstention": round(sum(r["outcome"] == "insufficient_evidence" for r in abstain)
                                        / max(len(abstain), 1), 3),
        "exact_scope_precision": round(sum(r["pass"] for r in exact) / max(len(exact), 1), 3),
        "hard_negatives": len(negatives),
    }
    body = {"metrics": metrics, "cases": results,
            "note": "Synthetic red-team fixtures (bench/fixtures/evidence/redteam.json): they test that the policy "
                    "behaves as designed on hard cases. They are not a real-world accuracy estimate."}
    path = runlog.save("evidence", f"{metrics['passed']}/{metrics['cases']} red-team cases as designed; "
                                   f"unsupported confirmations {metrics['unsupported_confirmation_rate']}", body)
    body["run_id"] = path.stem
    OUT.write_text(json.dumps(body, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(metrics, indent=1))
    for r in results:
        if not r["pass"]:
            print("FAIL", r["id"], r["category"], r["outcome"], r["basis"], r["expected"])


if __name__ == "__main__":
    main()
