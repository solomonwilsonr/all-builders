"""'Is it safe?' from the page alone, with stand-ins for the database and Gemini."""
from engine import page_safety, radar


def test_page_reviews_keep_text_and_fix_dates():
    out = page_safety.page_reviews({"reviews": [
        {"text": " Got hot and melted ", "rating": 1, "date": "2026-08-03"},
        {"text": "", "rating": 5},
        {"text": "Fine", "date": "3 August 2025"}]})
    assert [r["text"] for r in out] == ["Got hot and melted", "Fine"]
    assert out[0]["date"] == "2026-08-03" and len(out[1]["date"]) == 10  # an unreadable date becomes today


def test_generic_first_words_are_not_searched_as_brands():
    assert page_safety.searchable_brand({"title": "Original 65W charger"}, "Original") == ""
    assert page_safety.searchable_brand({"title": "65W charger"}, "65W") == ""
    assert page_safety.searchable_brand({"title": "Anker 20W charger"}, "Anker") == "Anker"
    assert page_safety.searchable_brand({"title": "Super charger", "page_text": "Brand Super"}, "Super") == ""


def stand_ins(monkeypatch, labels, recalls=()):
    stored = []

    def add_reviews(key, reviews):
        for r in reviews:
            stored.append({**r, "id": radar.review_id(r), "evidence_id": f"EV-{len(stored) + 1}"})

    monkeypatch.setattr(page_safety.safety, "add_reviews", add_reviews)
    monkeypatch.setattr(page_safety.safety, "product_reviews", lambda key: stored)
    monkeypatch.setattr(page_safety.safety, "label_reviews",
                        lambda view, reviews: {r["id"]: labels[r["text"]] for r in reviews if r["text"] in labels})
    monkeypatch.setattr(page_safety.recalls, "brand_recalls", lambda brand: list(recalls))


FIRE = {"hazard": True, "experience": "own_experience", "hazard_type": "fire_burn", "severity": "high",
        "mechanism": "port melted while charging", "quote": "melted"}


def test_two_own_fire_reports_on_the_page_make_it_amber(monkeypatch):
    stand_ins(monkeypatch, {"Port melted while charging.": FIRE, "Smoke came out, it burned my desk.": FIRE})
    answer = page_safety.listing_safety({"url": "https://www.amazon.in/dp/X", "title": "Nexzvolt 20W charger",
                                         "reviews": [{"text": "Port melted while charging.", "rating": 1},
                                                     {"text": "Smoke came out, it burned my desk.", "rating": 1},
                                                     {"text": "Works fine.", "rating": 5}]})
    assert answer["verdict"] == "amber" and answer["reviews_checked"] == 3
    assert answer["ai_findings"][0]["evidence_ids"] == ["EV-1", "EV-2"]
    assert answer["brand"] == "Nexzvolt" and not answer["official_status"]["recalled"]


def test_few_clean_reviews_are_not_enough_evidence(monkeypatch):
    stand_ins(monkeypatch, {})
    answer = page_safety.listing_safety({"title": "JETech Case", "reviews": [{"text": "Fits well."}]})
    assert answer["verdict"] == "not_enough_evidence" and answer["ai_findings"] == []


def test_exact_model_recall_makes_it_red(monkeypatch):
    stand_ins(monkeypatch, {})
    notice = {"id": "CPSC-1", "title": "VRURC Recalls Chargers", "url": "https://cpsc.gov/x", "notice_date": "2023-07-06",
              "scope_json": {"Products": [{"Model": "OD-B7"}]}}
    answer = page_safety.listing_safety({"title": "VRURC OD-B7 wall charger", "reviews": [], "page_text": "Brand VRURC"},)
    assert not answer["official_status"]["recalled"]  # no notices for this brand in the stand-in yet
    stand_ins(monkeypatch, {}, [notice])
    answer = page_safety.listing_safety({"title": "VRURC OD-B7 wall charger", "page_text": "Brand VRURC"})
    assert answer["verdict"] == "red" and answer["official_status"]["recalls"][0]["recall_id"] == "CPSC-1"
