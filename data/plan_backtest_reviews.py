"""M2: which Amazon reviews the backtest needs, as one ASIN list per category for data/vm_review_scan.sh.

    python3 data/plan_backtest_reviews.py && gcloud storage cp -r data/raw/review_asins gs://safeshelf-data-03d8d835/jobs/

Recalled: listings labelled recalled_model that were on sale before the recall (raw/backtest_targets.json).
Controls: the same brand's other products that were never recalled (same_brand_other_product), up to 3 per recall
with the most ratings, so false alarms are measured on look-alike products, not random ones.
"""
import json
from collections import defaultdict
from pathlib import Path

RAW = Path(__file__).parent / "raw"
CONTROLS_PER_RECALL = 3
MIN_RATINGS = 20


def main() -> None:
    targets = json.loads((RAW / "backtest_targets.json").read_text())
    rows = [json.loads(line) for line in (RAW / "recall_listing_matches.jsonl").read_text().splitlines()]
    category = {r["asin"]: r["category"] for r in rows}
    manifest: dict[str, dict] = {}
    for recall_id, target in targets.items():
        if not target["asins"]:
            continue
        controls = sorted((r for r in rows if r["recall_id"] == recall_id and r["label"] == "same_brand_other_product"
                           and r["rating_number"] >= MIN_RATINGS), key=lambda r: -r["rating_number"])
        manifest[recall_id] = {"title": target["title"], "recall": target["recall"], "recalled": target["asins"],
                               "controls": [r["asin"] for r in controls[:CONTROLS_PER_RECALL]]}

    by_category: dict[str, set[str]] = defaultdict(set)
    for entry in manifest.values():
        for asin in entry["recalled"] + entry["controls"]:
            by_category[category[asin]].add(asin)
    out = RAW / "review_asins"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.txt"):
        old.unlink()
    for cat, asins in sorted(by_category.items()):
        (out / f"{cat}.txt").write_text("\n".join(sorted(asins)) + "\n")
        print(f"{cat:<30} {len(asins):>4} ASINs")
    (RAW / "backtest_manifest.json").write_text(json.dumps(manifest, indent=1))
    recalled = sum(len(e["recalled"]) for e in manifest.values())
    controls = sum(len(e["controls"]) for e in manifest.values())
    print(f"{len(manifest)} recalls, {recalled} recalled listings, {controls} controls -> raw/review_asins/")


if __name__ == "__main__":
    main()
