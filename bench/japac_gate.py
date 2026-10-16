"""JAPAC acceptance gate (plan v2.2 section 2A), live: one product each from India, Australia, Japan and Singapore,
investigated with country scope and honest source states, plus one verified foreign-to-local match and one rejected
look-alike. Also writes bench/coverage_by_country.json.

    cd engine && PYTHONPATH=.. uv run python ../bench/japac_gate.py        (make bench-japac)

Test products are fixed in bench/fixtures/japac/gate.json with the outcome a person expects from the official notices
(checked by hand on 16 Oct 2026). Network is required: it runs the real adapters.
"""
import json
from pathlib import Path

from bench import runlog
from engine import investigation

HERE = Path(__file__).parent
GATE = HERE / "fixtures" / "japac" / "gate.json"


def main() -> None:
    cases = json.loads(GATE.read_text())["cases"]
    rows, coverage = [], {}
    for case in cases:
        answer = investigation.investigate({**case["request"], "skip_reviews": True})
        market_row = next((c for c in answer["coverage"]["countries"] if c["is_market"]), {})
        ok = answer["outcome"] == case["expected_outcome"] and \
            (not case.get("expected_basis") or answer["basis"] == case["expected_basis"])
        rows.append({"id": case["id"], "market": answer["market"], "outcome": answer["outcome"],
                     "basis": answer["basis"], "expected": case["expected_outcome"], "pass": ok,
                     "market_state": market_row.get("state"), "source_mode": answer["source_mode"],
                     "lead_record": answer.get("lead_record"), "seconds": answer["seconds"],
                     "coverage": answer["coverage"]["summary"]})
        coverage[case["id"]] = {"market": answer["market"], "countries": [
            {k: c[k] for k in ("country", "state", "checked_at", "matched")} | {
                "sources": [(s["source"], s["state"], s["mode"]) for s in c["sources"]]}
            for c in answer["coverage"]["countries"]]}
    markets = {r["market"] for r in rows}
    gate = {"each_market_investigated": {"IN", "AU", "JP", "SG"} <= markets,
            "foreign_to_local_match": any(r["basis"] == "recalled_abroad_same_model" and r["pass"] for r in rows),
            "lookalike_rejected": any(r["id"].startswith("lookalike") and r["pass"] for r in rows),
            "all_expected": all(r["pass"] for r in rows)}
    (HERE / "coverage_by_country.json").write_text(json.dumps(coverage, indent=1, default=str) + "\n")
    results = {"gate": gate, "cases": rows}
    path = runlog.save("japac_gate", f"{sum(r['pass'] for r in rows)}/{len(rows)} cases as expected; gate "
                                     f"{'passed' if all(gate.values()) else 'not passed'}", results)
    (HERE / "japac_gate_results.json").write_text(json.dumps({**results, "run_id": path.stem}, indent=1,
                                                             default=str) + "\n")
    for r in rows:
        print(("PASS " if r["pass"] else "FAIL ") + f"{r['id']:<22} {r['market']} {r['outcome']:<26} {r['basis']:<28} "
              f"{r['market_state']} {r['seconds']}s")
    print(json.dumps(gate))


if __name__ == "__main__":
    main()
