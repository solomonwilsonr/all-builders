import json
import os
from datetime import date
from pathlib import Path

import pytest

from engine import radar

CASES = json.loads((Path(__file__).parent / "radar_cases.json").read_text())


def review(i: int, text: str, day: str, images: list | None = None) -> dict:
    return {"id": f"r{i}", "text": text, "date": day, "images": images or []}


def label(hazard: bool, experience: str = "own_experience", kind: str = "fire_burn", severity: str = "high") -> dict:
    return {"hazard": hazard, "experience": experience, "hazard_type": kind, "severity": severity,
            "mechanism": "port melted while charging"}


def test_only_own_experience_hazards_become_findings():
    reviews = [review(1, "Melted on the first day", "2023-04-26"), review(2, "this charger is fire", "2023-04-27"),
               review(3, "no overheating at all", "2023-04-28"), review(4, "heard these explode", "2023-04-29")]
    labels = {"r1": label(True), "r2": label(False, "figurative_or_joke"), "r3": label(False, "negated_or_absent"),
              "r4": label(True, "hearsay")}
    [finding] = radar.findings(reviews, labels)
    assert finding["independent_reports"] == 1 and finding["evidence_ids"] == ["REV-r1"]
    assert finding["status"] == "under_review"
    assert "1 review says it does not overheat" in finding["counterevidence"]
    assert "1 report is second-hand" in finding["counterevidence"]


def test_copies_of_one_complaint_count_once():
    reviews = [review(1, "Melted on the first day!", "2023-04-26"), review(2, "melted on the first day", "2023-04-27")]
    [finding] = radar.findings(reviews, {"r1": label(True), "r2": label(True)})
    assert finding["independent_reports"] == 1


def test_rate_trend_and_photos():
    reviews = [review(i, f"text {i}", "2023-01-01") for i in range(96)]
    reviews += [review(100, "smoke", "2023-01-10"), review(101, "melted", "2023-05-01", ["https://img/1.jpg"]),
                review(102, "sparks", "2023-05-20"), review(103, "burned", "2023-06-01")]
    labels = {f"r{i}": label(True) for i in (100, 101, 102, 103)}
    photos = {"https://img/1.jpg": {"damage": True}}
    [finding] = radar.findings(reviews, labels, photos, as_of=date(2023, 6, 30))
    assert finding["rate_per_1000_reviews"] == 40.0
    assert finding["with_photos"] == 1
    assert finding["trend"] == "rising" and finding["first_seen"] == "2023-01-10"


def test_verdict_is_set_by_code():
    serious = [{"severity": "high", "independent_reports": 2, "with_photos": 0}]
    single_with_photo = [{"severity": "high", "independent_reports": 1, "with_photos": 1}]
    minor = [{"severity": "low", "independent_reports": 5, "with_photos": 0}]
    assert radar.verdict(True, 0, []) == "red"
    assert radar.verdict(False, 200, serious) == "amber"
    assert radar.verdict(False, 200, single_with_photo) == "amber"
    assert radar.verdict(False, 200, minor) == "green"
    assert radar.verdict(False, 5, []) == "not_enough_evidence"


@pytest.mark.skipif(not os.environ.get("RUN_LIVE"), reason="calls Gemini; set RUN_LIVE=1")
def test_live_gemini_matches_hand_labels():
    reviews = [{"id": c["id"], "text": c["text"]} for c in CASES["cases"]]
    labels = radar.classify(CASES["product"], reviews)
    wrong = [c["id"] for c in CASES["cases"] if radar.counts(labels.get(c["id"], {})) != c["hazard"]]
    assert {"c01", "c02", "c03"}.isdisjoint(wrong), f"done-when cases wrong: {wrong}"
    assert len(wrong) <= 1, f"misclassified: {wrong}"
