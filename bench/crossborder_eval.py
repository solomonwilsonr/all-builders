"""Cross-border benchmark (plan v2.2 workstream H track 3 / checklist item 7): when a JAPAC regulator recalled a model,
had another country's regulator recalled the same model first, and by how many days?

    cd engine && PYTHONPATH=.. uv run python ../bench/crossborder_eval.py     (make bench-crossborder)

Pairs come from engine/crossborder.py (exact model code; generic words dropped; same company = tier exact). Every
pair is "for a person to check" until bench/fixtures/japac/crossborder_checked.json records a person's verdict, and
only checked pairs count as verified. Lead times get a bootstrap 95% interval; small samples are labelled as such.
Writes bench/crossborder_results.json and bench/recall_by_country.json.
"""
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from bench import runlog
from engine import crossborder, store

HERE = Path(__file__).parent
CHECKED = HERE / "fixtures" / "japac" / "crossborder_checked.json"


def bootstrap_median(values: list[int], n: int = 2000, seed: int = 7) -> list[float] | None:
    if len(values) < 5:
        return None
    rng = random.Random(seed)
    meds = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(n))
    return [meds[int(0.025 * n)], meds[int(0.975 * n)]]


def main() -> None:
    pairs = crossborder.candidates()
    checked = json.loads(CHECKED.read_text())["checked"] if CHECKED.exists() else {}
    for p in pairs:
        key = f"{p['first']['record_id']}|{p['later']['record_id']}"
        verdict = checked.get(key)
        p["person_check"] = verdict or "not_checked"
        p["status"] = "verified_affected_model" if verdict == "same_product" else \
            "rejected" if verdict == "different_product" else p["status"]
    leads = [p["lead_days"] for p in pairs if p["tier"] == "exact" and (p["lead_days"] or 0) > 0]
    verified = [p for p in pairs if p["status"] == "verified_affected_model"]
    by_country = Counter(p["later"]["country"] for p in pairs if p["tier"] == "exact")
    results = {
        "pairs": len(pairs), "same_company_pairs": sum(p["tier"] == "exact" for p in pairs),
        "person_checked": sum(p["person_check"] != "not_checked" for p in pairs), "verified": len(verified),
        "rejected": sum(p["status"] == "rejected" for p in pairs),
        "later_country": dict(by_country), "first_country": dict(Counter(p["first"]["country"] for p in pairs)),
        "lead_days": {"n": len(leads), "median": statistics.median(leads) if leads else None,
                      "median_95ci": bootstrap_median(leads), "min": min(leads, default=None),
                      "max": max(leads, default=None)},
        "small_sample": len(leads) < 30,
        "candidates": pairs,
        "method": "Same model code (letters and digits, at least 4 characters; generic words removed) in notices from "
                  "two countries; same company named = exact tier. Lead = days between the two publication dates.",
        "limits": "Stored notices since 2019 only; model codes written in a notice's free text can be missed, so this "
                  "undercounts. A pair is a lead until a person confirms it is the same product.",
    }
    recall_rows = store.conn().execute(
        "SELECT authority, count(*) AS n, min(notice_date) AS oldest, max(notice_date) AS newest FROM recalls "
        "GROUP BY authority ORDER BY n DESC").fetchall()
    (HERE / "recall_by_country.json").write_text(json.dumps(
        {"authorities": [{**r, "oldest": str(r["oldest"]), "newest": str(r["newest"])} for r in recall_rows]},
        indent=1) + "\n")
    path = runlog.save("crossborder", f"{results['pairs']} pairs ({results['same_company_pairs']} same company), "
                                      f"{results['verified']} verified by a person; median lead "
                                      f"{results['lead_days']['median']} days (n={len(leads)})", results)
    (HERE / "crossborder_results.json").write_text(json.dumps({**results, "run_id": path.stem}, indent=1,
                                                              ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: v for k, v in results.items() if k != "candidates"}, indent=1, default=str))


if __name__ == "__main__":
    main()
