"""Historical-replay leakage check (plan v2.2 workstream H): is every backtest cutoff the FIRST date the recall was
public anywhere, and was nothing dated after it used?

    cd engine && PYTHONPATH=.. uv run python ../bench/cutoff.py      (make bench-historical)

For each recall in data/raw/backtest_manifest.json: the cutoff the backtest used, the regulator's own publication
date (recalls.notice_date), and the earliest notice of the same model anywhere (engine/crossborder.py). A cutoff
later than an earlier public notice is reported as possible leakage (reviews in between could echo that notice).
Writes bench/cutoff_results.json.
"""
import json
from datetime import date
from pathlib import Path

from bench import runlog
from engine import crossborder, store

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "raw" / "backtest_manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    earliest: dict[str, tuple[str, str]] = {}
    for p in crossborder.candidates():
        earliest.setdefault(p["later"]["record_id"], (p["first"]["date"], p["first"]["record_id"]))
    rows = []
    for recall_id, entry in manifest.items():
        cutoff = entry.get("recall")
        db = store.conn().execute("SELECT notice_date FROM recalls WHERE id = %s", (recall_id,)).fetchone()
        published = str(db["notice_date"]) if db and db["notice_date"] else None
        first = earliest.get(recall_id)
        issues = []
        if not published:
            issues.append("publication date unknown: ineligible")
        elif cutoff and date.fromisoformat(cutoff) > date.fromisoformat(published):
            issues.append(f"cutoff {cutoff} is after the publication date {published}")
        if first and cutoff and date.fromisoformat(first[0]) < date.fromisoformat(cutoff):
            issues.append(f"the same model was public earlier: {first[1]} on {first[0]}")
        rows.append({"recall_id": recall_id, "cutoff": cutoff, "published": published,
                     "earliest_elsewhere": first[0] if first else None, "issues": issues})
    flagged = [r for r in rows if r["issues"]]
    results = {"recalls": len(rows), "flagged": len(flagged), "rows": rows,
               "rules": ["reviews strictly before the cutoff (bench/backtest.py usable())",
                         "reviews mentioning 'recall' removed",
                         "cutoff must not be later than the first public notice of the same model anywhere"]}
    path = runlog.save("historical_cutoff", f"{len(rows)} recalls checked, {len(flagged)} with a cutoff issue", results)
    (Path(__file__).parent / "cutoff_results.json").write_text(json.dumps({**results, "run_id": path.stem},
                                                                          indent=1) + "\n")
    print(f"{len(rows)} recalls; {len(flagged)} flagged")
    for r in flagged:
        print(" ", r["recall_id"], "; ".join(r["issues"]))


if __name__ == "__main__":
    main()
