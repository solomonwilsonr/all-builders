"""M2 backtest + SafeShelfBench: would each method have warned before the official recall? (BACKTEST.md)

    make bench        # downloads the reviews if needed, labels (cached), writes bench/results.json + README table

Units: each recall is replayed as one product family (all its recalled listings pooled: twin pooling) and as
single listings (no pooling). Controls are the same brands' never-recalled products, cut off at the same date.
Honesty rules: only reviews dated before the recall; reviews mentioning "recall" removed; copies counted once
(SafeShelf only - the baselines don't dedupe); every recall reported, including misses.

Methods (same reviews in, same lead-time maths out):
- keyword_rules: a hazard keyword means a hazard; alarm at 3 in 90 days.
- gemini_alone:  one plain Gemini question per review; same alarm rule. No engine, dedupe, rates or pooling.
- safeshelf:     Safety Radar labels (own experience, severity), dedupe, rate-aware alarm tuned on half the
                 recalls and reported on the other half, twin pooling.
Both Gemini methods only read reviews that pass a broad pre-filter (PREFILTER), to keep cost and time down.
"""
import hashlib
import json
import re
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REVIEWS = RAW / "amazon_reviews"
CACHE = RAW / "bench_cache"
OUT = Path(__file__).parent / "results.json"

KEYWORDS = re.compile(r"\b(fire|flames?|smok\w*|melt\w*|burn\w*|scorch\w*|overheat\w*|too hot|very hot|extremely hot|"
                      r"spark\w*|explod\w*|swell\w*|swollen|bulg\w*|caught fire|shock\w*)\b", re.IGNORECASE)
PREFILTER = re.compile(KEYWORDS.pattern[:-3] + r"|hot|heat\w*|smell\w*|electrocut\w*|toxic|leak\w*|char(?:red)?|"
                       r"black(?:ened)?|blew|blown|pop(?:ped)?)\b", re.IGNORECASE)
RECALL_WORD = re.compile(r"\brecall", re.IGNORECASE)
WINDOW = timedelta(days=90)
FIXED_K = 3
SEVERITY = {"low": 0, "medium": 1, "high": 2}
SAFESHELF_GRID = [{"k": k, "min_severity": s, "min_rate": r}
                  for k in (2, 3, 4) for s in ("low", "medium") for r in (0.0, 2.0, 5.0)]

GEMINI_ALONE_SCHEMA = {
    "type": "object",
    "properties": {"reviews": {"type": "array", "items": {
        "type": "object", "properties": {"id": {"type": "string"}, "hazard": {"type": "boolean"}},
        "required": ["id", "hazard"]}}},
    "required": ["reviews"],
}
GEMINI_ALONE_PROMPT = """Does each review report a safety hazard with the product? Answer hazard true or false.
<reviews>
{reviews}
</reviews>"""


# ---------- pure logic (unit-tested) ----------

def review_day(review: dict) -> date:
    return datetime.fromtimestamp(review["timestamp"] / 1000, tz=UTC).date()


def rid(review: dict) -> str:
    return hashlib.sha1(f"{review.get('user_id')}|{review.get('timestamp')}|{review.get('parent_asin')}".encode()
                        ).hexdigest()[:12]


def usable(reviews: list[dict], cutoff: date) -> list[dict]:
    """Reviews strictly before the cutoff, without any that mention a recall, in date order."""
    keep = [r for r in reviews if review_day(r) < cutoff
            and not RECALL_WORD.search(f"{r.get('title') or ''} {r.get('text') or ''}")]
    return sorted(keep, key=review_day)


def first_alarm(hits: list[date], k: int = FIXED_K) -> date | None:
    """First day with k hazard reports inside a 90-day window."""
    hits = sorted(hits)
    for i in range(k - 1, len(hits)):
        if hits[i] - hits[i - k + 1] <= WINDOW:
            return hits[i]
    return None


def safeshelf_alarm(reviews: list[dict], labels: dict[str, dict], params: dict) -> date | None:
    """Rate-aware alarm: k independent own-experience reports at or above min_severity within 90 days, and the
    running hazard rate per 1000 reviews at least min_rate on that day. Copies count once."""
    seen, hits, total = set(), [], 0
    for review in reviews:
        total += 1
        label = labels.get(rid(review))
        if not label or not (label.get("hazard") and label.get("experience") == "own_experience"):
            continue
        if SEVERITY.get(label.get("severity") or "low", 0) < SEVERITY[params["min_severity"]]:
            continue
        key = re.sub(r"\W+", " ", (review.get("text") or "").lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        hits.append(review_day(review))
        alarm = first_alarm(hits, params["k"])
        if alarm and 1000 * len(hits) / total >= params["min_rate"]:
            return alarm
    return None


def summarise(units: list[dict], method: str) -> dict:
    """units: {"kind": "recall"|"control", "cutoff": date, "alarm": {method: date|None}}."""
    recalls = [u for u in units if u["kind"] == "recall"]
    controls = [u for u in units if u["kind"] == "control"]
    leads = [(u["cutoff"] - u["alarm"][method]).days for u in recalls if u["alarm"][method]]
    false = sum(bool(u["alarm"][method]) for u in controls)
    return {
        "recalls_flagged": f"{len(leads)}/{len(recalls)}",
        "median_lead_weeks": round(statistics.median(leads) / 7, 1) if leads else None,
        "false_alarm_rate": round(false / len(controls), 2) if controls else None,
        "false_alarms": f"{false}/{len(controls)}",
    }


def split(recall_id: str) -> str:
    """Stable half/half split for tuning (train) and reporting (test)."""
    return "train" if int(hashlib.sha1(recall_id.encode()).hexdigest(), 16) % 2 == 0 else "test"


def tune(units: list[dict], score) -> dict:
    """Pick SafeShelf params on the train half: most recalls flagged, each false alarm costs two."""
    train = [u for u in units if split(u["recall_id"]) == "train"]

    def value(params: dict) -> tuple:
        flagged = sum(bool(score(u, params)) for u in train if u["kind"] == "recall")
        false = sum(bool(score(u, params)) for u in train if u["kind"] == "control")
        return (flagged - 2 * false, -params["k"])

    return max(SAFESHELF_GRID, key=value)


# ---------- data and labelling ----------

def load_reviews(asins: set[str]) -> dict[str, list[dict]]:
    by_asin: dict[str, list[dict]] = {a: [] for a in asins}
    for path in sorted(REVIEWS.glob("reviews_*.jsonl")):
        for line in path.read_text().splitlines():
            review = json.loads(line)
            if review.get("parent_asin") in by_asin:
                by_asin[review["parent_asin"]].append(review)
    return by_asin


def cached_batches(name: str, reviews: list[dict], size: int, run) -> dict[str, dict]:
    """Label reviews in batches through run(batch) -> {id: label}; each batch is cached on disk."""
    CACHE.mkdir(parents=True, exist_ok=True)
    batches = [reviews[i:i + size] for i in range(0, len(reviews), size)]

    def one(batch: list[dict]) -> dict[str, dict]:
        key = hashlib.sha1((name + "|".join(rid(r) for r in batch)).encode()).hexdigest()[:16]
        path = CACHE / f"{name}-{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        labels = run(batch)
        if labels:
            path.write_text(json.dumps(labels))
        return labels

    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for labels in pool.map(one, batches):
            out.update(labels)
    return out


def label_safeshelf(product: str, reviews: list[dict]) -> dict[str, dict]:
    from engine import radar

    def run(batch: list[dict]) -> dict[str, dict]:
        items = [{**r, "id": rid(r)} for r in batch]
        return radar.classify(product, items, timeout_s=120)

    return cached_batches("radar", reviews, radar.BATCH, run)


def label_gemini_alone(reviews: list[dict]) -> dict[str, dict]:
    from engine import gemini

    def run(batch: list[dict]) -> dict[str, dict]:
        items = [{"id": rid(r), "text": f"{r.get('title') or ''}. {(r.get('text') or '')[:1500]}"} for r in batch]
        try:
            result = gemini.structured(GEMINI_ALONE_PROMPT.format(reviews=json.dumps(items, ensure_ascii=False)),
                                       GEMINI_ALONE_SCHEMA, timeout_s=120)
        except RuntimeError:
            return {}
        return {row["id"]: row for row in result.get("reviews", [])}

    return cached_batches("alone", reviews, 25, run)


# ---------- the run ----------

def build_units(manifest: dict, by_asin: dict[str, list[dict]]) -> list[dict]:
    units = []
    for recall_id, entry in manifest.items():
        cutoff = date.fromisoformat(entry["recall"])
        family = usable([r for a in entry["recalled"] for r in by_asin.get(a, [])], cutoff)
        units.append({"kind": "recall", "recall_id": recall_id, "title": entry["title"], "cutoff": cutoff,
                      "asins": entry["recalled"], "reviews": family,
                      "singles": [usable(by_asin.get(a, []), cutoff) for a in entry["recalled"]]})
        for asin in entry["controls"]:
            units.append({"kind": "control", "recall_id": recall_id, "title": f"control {asin}", "cutoff": cutoff,
                          "asins": [asin], "reviews": usable(by_asin.get(asin, []), cutoff), "singles": []})
    return units


def main() -> None:
    manifest = json.loads((RAW / "backtest_manifest.json").read_text())
    asins = {a for e in manifest.values() for a in e["recalled"] + e["controls"]}
    by_asin = load_reviews(asins)
    units = build_units(manifest, by_asin)

    candidates = {rid(r): r for u in units for r in u["reviews"]
                  if PREFILTER.search(f"{r.get('title') or ''} {r.get('text') or ''}")}
    print(f"{sum(len(u['reviews']) for u in units)} usable reviews, {len(candidates)} pass the pre-filter")
    radar_labels: dict[str, dict] = {}
    for unit in units:  # Radar is told which product family it is reading
        todo = [r for r in unit["reviews"] if rid(r) in candidates and rid(r) not in radar_labels]
        if todo:
            radar_labels.update(label_safeshelf(unit["title"], todo))
    alone_labels = label_gemini_alone(list(candidates.values()))

    def keyword_hits(reviews: list[dict]) -> list[date]:
        return [review_day(r) for r in reviews if KEYWORDS.search(f"{r.get('title') or ''} {r.get('text') or ''}")]

    def alone_hits(reviews: list[dict]) -> list[date]:
        return [review_day(r) for r in reviews if alone_labels.get(rid(r), {}).get("hazard")]

    def score(unit: dict, params: dict) -> date | None:
        return safeshelf_alarm(unit["reviews"], radar_labels, params)

    params = tune(units, score)
    for unit in units:
        unit["alarm"] = {
            "keyword_rules": first_alarm(keyword_hits(unit["reviews"])),
            "gemini_alone": first_alarm(alone_hits(unit["reviews"])),
            "safeshelf": score(unit, params),
            # no pooling: the earliest alarm on any single listing
            "safeshelf_no_pooling": min((a for s in unit["singles"] if (a := safeshelf_alarm(s, radar_labels, params))),
                                        default=None) if unit["kind"] == "recall" else score(unit, params),
        }

    methods = ["keyword_rules", "gemini_alone", "safeshelf", "safeshelf_no_pooling"]
    test_units = [u for u in units if split(u["recall_id"]) == "test"]
    results = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "tasks": {"early_warning": {m: summarise(units, m) for m in methods}},
        "safeshelf_on_test_half": summarise(test_units, "safeshelf"),
        "safeshelf_params": params,
        "per_recall": [{"recall_id": u["recall_id"], "title": u["title"], "recall_date": u["cutoff"].isoformat(),
                        "listings": len(u["asins"]), "reviews_before_recall": len(u["reviews"]),
                        "split": split(u["recall_id"]),
                        **{f"{m}_lead_days": (u["cutoff"] - u["alarm"][m]).days if u["alarm"][m] else None
                           for m in methods}}
                       for u in units if u["kind"] == "recall"],
        "controls": [{"asin": u["asins"][0], "recall_id": u["recall_id"], "reviews": len(u["reviews"]),
                      **{f"{m}_false_alarm": bool(u["alarm"][m]) for m in methods}}
                     for u in units if u["kind"] == "control"],
        "caveats": [
            "Gemini methods only read reviews that pass a broad keyword pre-filter.",
            "Recalls whose notice lists no model numbers count every listing of the named product family.",
            "Controls are the same brands' other products; a control alarm may be a real, never-recalled hazard.",
            "SafeShelf alarm settings were tuned on the train half; safeshelf_on_test_half is the unbiased figure.",
        ],
    }
    OUT.write_text(json.dumps(results, indent=1))
    write_readme_table(results)
    for m in methods:
        print(f"{m:<22} {results['tasks']['early_warning'][m]}")
    print(f"safeshelf (test half)  {results['safeshelf_on_test_half']}  params {params}")


def write_readme_table(results: dict) -> None:
    readme = Path(__file__).parent / "README.md"
    rows = ["| Method | Recalls flagged early | Median lead (weeks) | False alarms |", "|---|---|---|---|"]
    for method, r in results["tasks"]["early_warning"].items():
        rows.append(f"| {method} | {r['recalls_flagged']} | {r['median_lead_weeks']} | {r['false_alarms']} |")
    table = "\n".join(["<!-- bench:start -->", f"Generated {results['generated_at']}.", "", *rows,
                       "<!-- bench:end -->"])
    text = readme.read_text()
    if "<!-- bench:start -->" in text:
        text = re.sub(r"<!-- bench:start -->.*<!-- bench:end -->", table, text, flags=re.DOTALL)
    else:
        text += "\n" + table + "\n"
    readme.write_text(text)


if __name__ == "__main__":
    main()
