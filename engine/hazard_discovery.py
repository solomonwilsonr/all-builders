"""Hazard discovery, evidence integrity and cause hypotheses (plan v2.2 workstream D). Code only.

    anomaly(dates, baseline_rate, reviews)  -> is the hazard-report rate above the category baseline, with an interval?
    integrity(reviews, labels)              -> copied complaints, recycled photos, suspicious bursts
    hypotheses(findings, reviews)           -> possible causes with supporting and contradicting evidence
    candidates(limit)                       -> products whose hazard signals rose above their category's baseline

Review counts are not sales: rates are per 1,000 reviews and say so. A high rate makes an "investigation_candidate",
never a confirmed defect, and a cause stays a hypothesis without physical or independent evidence.
"""
import math
import re
from collections import Counter, defaultdict
from datetime import date, timedelta

Z95 = 1.96
BURST_DAYS = 3
BURST_SHARE = 0.6


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """95% Wilson interval for a proportion k/n."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def anomaly(hazard_reports: int, reviews: int, baseline_per_1000: float, min_reviews: int = 20) -> dict:
    """Above baseline only if the lower end of the 95% interval clears the category's baseline rate."""
    low, high = wilson(hazard_reports, reviews)
    rate = 1000 * hazard_reports / reviews if reviews else 0.0
    above = reviews >= min_reviews and 1000 * low > baseline_per_1000
    return {"rate_per_1000_reviews": round(rate, 1), "interval_per_1000": [round(1000 * low, 1), round(1000 * high, 1)],
            "baseline_per_1000": round(baseline_per_1000, 1), "reviews": reviews, "hazard_reports": hazard_reports,
            "status": "investigation_candidate" if above else "within_baseline" if reviews >= min_reviews
            else "too_few_reviews",
            "note": "Per 1,000 reviews, not per unit sold; a candidate needs a person's investigation."}


def integrity(reviews: list[dict], image_hashes: dict[str, list[str]] | None = None) -> dict:
    """Evidence-integrity flags. They never dismiss a report: they say which reports may not be independent."""
    image_hashes = image_hashes or {}
    norm = [re.sub(r"\W+", " ", (r.get("text") or "").lower()).strip() for r in reviews]
    copies = [t for t, n in Counter(norm).items() if t and n > 1]
    photo_owners: dict[str, set[str]] = defaultdict(set)
    for rid, hashes in image_hashes.items():
        for h in hashes:
            photo_owners[h].add(rid)
    recycled = [sorted(owners) for owners in photo_owners.values() if len(owners) > 1]
    dates = sorted(d for d in (_date(r) for r in reviews) if d)
    burst = None
    if len(dates) >= 5:
        for i, start in enumerate(dates):
            window = [d for d in dates[i:] if d <= start + timedelta(days=BURST_DAYS)]
            if len(window) / len(dates) >= BURST_SHARE:
                burst = {"start": start.isoformat(), "days": BURST_DAYS, "share": round(len(window) / len(dates), 2)}
                break
    flags = (["copied_text"] if copies else []) + (["recycled_photos"] if recycled else []) + \
        (["burst"] if burst else [])
    return {"flags": flags, "copied_texts": len(copies), "recycled_photo_groups": recycled[:5], "burst": burst,
            "note": "Flags lower how much these reports count as independent; they never delete a report."}


def _date(review: dict) -> date | None:
    try:
        return date.fromisoformat(str(review.get("date") or "")[:10])
    except ValueError:
        return None


CAUSES = {
    "faulty_cell_or_charger": (r"\b(battery|cell|swell\w*|charg\w*|overheat\w*|melt\w*)\b",
                               "Teardown or lab test of returned units; batch/date codes of affected units"),
    "incompatible_cable_or_adapter": (r"\b(third[- ]party|other (?:cable|charger)|non[- ]original|wrong adapter)\b",
                                      "Reproduce with the original accessory; check the manual's rating"),
    "environment": (r"\b(hot car|sun|humid\w*|rain|water|wet)\b", "Ask owners about storage and use conditions"),
    "user_misuse": (r"\b(dropped|modified|opened it|left (?:it )?charging for days)\b",
                    "Compare with reports that describe normal use"),
}


def hypotheses(findings: list[dict], review_texts: list[str]) -> list[dict]:
    """Possible causes, each with how many reports mention it and what would test it. Always 'hypothesis'."""
    text = " ".join(review_texts).lower()
    out = []
    for cause, (pattern, test) in CAUSES.items():
        support = len(re.findall(pattern, text, re.IGNORECASE))
        if support:
            out.append({"cause": cause, "status": "hypothesis", "supporting_mentions": support,
                        "contradicting": "reports describing normal use" if cause == "user_misuse" else
                        "reports that name a different trigger", "verification_test": test})
    return sorted(out, key=lambda h: -h["supporting_mentions"]) or (
        [{"cause": "unknown", "status": "hypothesis", "supporting_mentions": 0, "verification_test":
          "Collect the model, batch and conditions of each incident"}] if findings else [])


def candidates(limit: int = 20) -> dict:
    """Products whose stored hazard signals clear their category's baseline (from the database)."""
    from engine import store
    rows = store.conn().execute(
        """WITH rev AS (SELECT regexp_replace(source_ref, ':[^:]*$', '') AS pid, count(*) AS reviews FROM evidence
                        WHERE source_type = 'review' GROUP BY 1),
                sig AS (SELECT product_id, count(*) FILTER (WHERE severity IN ('medium', 'high')) AS signals
                        FROM hazard_signals GROUP BY 1)
           SELECT p.id, p.brand, p.model, p.category, rev.reviews, sig.signals
           FROM sig JOIN products p ON p.id = sig.product_id JOIN rev ON rev.pid = p.id
           ORDER BY sig.signals DESC, rev.reviews DESC LIMIT 500""").fetchall()
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cat[r["category"] or "other"].append(r)
    out = []
    for category, items in by_cat.items():
        total_reviews = sum(i["reviews"] for i in items)
        baseline = 1000 * sum(i["signals"] for i in items) / total_reviews if total_reviews else 0
        for i in items:
            result = anomaly(i["signals"], i["reviews"], baseline)
            if result["status"] == "investigation_candidate":
                out.append({"product_id": i["id"], "brand": i["brand"], "model": i["model"], "category": category,
                            **result})
    out.sort(key=lambda c: -c["interval_per_1000"][0])
    return {"candidates": out[:limit], "method": "Wilson 95% interval of hazard signals per review vs. the category "
                                                 "baseline; counts are signals, not units sold"}
