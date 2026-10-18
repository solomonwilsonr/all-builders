"""'Is it any good?' from reviews: code rules on the star summary and Gemini's labels (no database, no Gemini)."""
from engine import radar
from engine import review_verdict as rv

SUMMARY = {"average": 4.1, "count": 3412, "distribution": {"5": 58, "4": 18, "3": 8, "2": 5, "1": 11}}


def label(*aspects, liked="", problem=""):
    return {"hazard": False, "experience": "not_a_hazard", "liked": liked, "problem": problem,
            "aspects": [{"aspect": a, "sentiment": s} for a, s in aspects]}


def reviews_and_labels(rows):
    """rows: (rating, text, label) -> stored-review shapes and labels by review id."""
    reviews, labels = [], {}
    for i, (rating, text, lab) in enumerate(rows):
        review = {"id": f"r{i}", "evidence_id": f"EV-{i}", "text": text, "rating": rating, "date": "2026-09-01"}
        reviews.append(review)
        if lab is not None:
            labels[review["id"]] = lab
    return reviews, labels


def test_summary_needs_all_five_stars_adding_up():
    assert rv.rating_summary(SUMMARY)["shares"][5] == 0.58
    assert rv.rating_summary({"count": "3,412 ratings", "distribution": {"5": 58, "4": 18}})["shares"] is None
    assert rv.rating_summary({"distribution": {"5": 90, "4": 90, "3": 90, "2": 90, "1": 90}}) is None
    assert rv.rating_summary("4.1") is None


def per_star(complaining):
    """Ten reviews per star level; complaining[star] of them mention "stopped working after 2 months"."""
    rows = []
    for star in range(1, 6):
        for i in range(10):
            hit = i < complaining.get(star, 0)
            lab = label(("durability", "neg"), problem="stopped working after 2 months") if hit else \
                label(("value", "pos"), liked="good value")
            rows.append((star, f"{'Died after 8 weeks' if hit else 'Great value'} {star}-{i}", lab))
    return rows


def test_rare_complaint_is_good():
    reviews, labels = reviews_and_labels(per_star({1: 2, 2: 1}))
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    # .11 * .2 + .05 * .1 = 2.7% of buyers: below the 10% that stops "good"
    assert out["verdict"] == "good" and out["headline"] == "Mostly good"
    assert out["complaints"][0]["share_estimate"] == 0.027
    assert out["liked"][0]["phrase"] == "good value"
    assert out["rating"] == {"average": 4.1, "count": 3412, "source": "page_summary", "positive_share": 0.76}
    assert out["confidence"] == "high" and out["reviews_read"] == 50


def test_a_complaint_weighted_by_each_stars_real_size_makes_it_mixed():
    reviews, labels = reviews_and_labels(per_star({1: 8, 2: 6, 3: 3, 4: 1}))
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    # .11 * .8 + .05 * .6 + .08 * .3 + .18 * .1 = 16% of buyers
    assert out["verdict"] == "mixed" and out["complaints"][0]["share_estimate"] == 0.16
    assert out["complaints"][0]["quote"].startswith("Died after 8 weeks") and out["complaints"][0]["evidence_ids"][0] == "EV-0"
    counted = out["complaints"][0]["reviews"]  # every review behind the complaint, lowest stars first, in the answer itself
    assert len(counted) == out["complaints"][0]["mentions"] == 18 and counted[0]["rating"] == 1
    assert [r["rating"] for r in counted] == sorted(r["rating"] for r in counted)
    assert set(counted[0]) == {"rating", "date", "title", "text"}
    assert out["reasons"] == ['76% of 3,412 ratings are 4 or 5 stars, but about 16% of buyers hit "stopped working after 2 months"']


def test_a_big_complaint_caps_at_mixed_only_the_stars_make_it_poor():
    reviews, labels = reviews_and_labels(per_star({1: 10, 2: 10, 3: 10, 4: 5, 5: 2}))
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert out["rating"]["positive_share"] == 0.76 and out["verdict"] == "mixed"  # about 45% of buyers, still not poor
    low = rv.rating_summary({"count": 500, "distribution": {"5": 30, "4": 10, "3": 10, "2": 15, "1": 35}})
    assert rv.decide(low, reviews, labels, [])["verdict"] == "poor"


def test_complaints_are_counted_by_their_own_wording_not_their_category():
    """Gemini files battery, app and sound complaints all under "performance": they must not add up to one share."""
    rows = []
    for star in range(1, 6):
        for i in range(10):
            phrase = ("sound quality poor", "battery dies fast", "app keeps crashing")[i % 3] if star <= 3 else None
            rows.append((star, f"r{star}-{i}", label(("performance", "neg"), problem=phrase) if phrase
                         else label(("value", "pos"), liked="good value")))
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    shares = {c["phrase"]: c["share_estimate"] for c in out["complaints"]}
    assert set(shares) == {"sound quality poor", "battery dies fast", "app keeps crashing"}
    assert all(0.06 < v < 0.10 for v in shares.values()), shares  # a third of the 24% unhappy buyers each, never 24%


def test_two_complaints_in_one_phrase_count_separately_and_never_merge():
    rows = [(star, f"r{star}-{i}", label(("performance", "neg"), problem=phrase))
            for star in (1, 2, 3, 4, 5) for i, phrase in enumerate(
                ["poor network and seems used", "poor network", "seems used", "poor network"])]
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    by = {c["phrase"]: c for c in out["complaints"]}
    assert set(by) == {"poor network", "seems used"}
    assert by["poor network"]["mentions"] == 15 and by["seems used"]["mentions"] == 10
    assert by["poor network"]["share_estimate"] == 0.75 and by["seems used"]["share_estimate"] == 0.5


def test_no_percentage_when_the_stars_read_cover_too_little_of_the_ratings():
    # Only 1-3 star reviews were read: they cover 24% of ratings, so "58% of buyers" would be a lean estimate
    rows = [(star, f"x{star}-{i}", label(("performance", "neg"), problem="poor network")) for star in (1, 2, 3) for i in range(5)]
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert out["complaints"][0]["share_estimate"] is None and out["complaints"][0]["mentions"] == 15
    assert out["reasons"] == ["76% of 3,412 ratings are 4 or 5 stars (good is 75% or more) and no complaint is common"]
    assert out["verdict"] == "good"  # no share, so the complaint cannot lower it: the stars decide


def test_a_like_that_shares_its_subject_with_a_complaint_is_dropped():
    rows = [(1, "Sound is poor", label(("performance", "neg"), problem="sound quality poor"))] * 8 + \
           [(5, "Good sound", label(("performance", "pos"), liked="good sound"))] * 8 + \
           [(5, "Fits well", label(("size_fit", "pos"), liked="comfortable fit"))] * 8 + [(3, "ok", label())] * 4
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert [t["phrase"] for t in out["liked"]] == ["comfortable fit"]
    assert [t["phrase"] for t in out["complaints"]] == ["sound quality poor"]


def test_few_unhappy_reviews_cannot_lower_the_verdict():
    rows = [(5, "Great", label(("value", "pos"), liked="good value"))] * 10 + \
           [(1, "Died", label(("durability", "neg"), problem="stopped working"))] * 5
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert out["verdict"] == "good" and out["confidence"] == "low"  # only 5 critical reviews read: the stars decide
    assert out["reasons"] == ["76% of 3,412 ratings are 4 or 5 stars (good is 75% or more) and no complaint is common"]


def test_low_ratings_are_poor_and_never_red():
    summary = rv.rating_summary({"count": 500, "distribution": {"5": 30, "4": 10, "3": 10, "2": 15, "1": 35}})
    out = rv.decide(summary, [], {}, [])
    assert out["verdict"] == "poor" and out["reasons"] == ["Only 40% of 500 ratings are 4 or 5 stars (poor is under 55%)"]


def test_a_low_average_is_poor_but_a_four_star_product_is_not():
    redmi = rv.rating_summary({"average": 3.3, "count": 32, "distribution": {"5": 30, "4": 23, "3": 16, "2": 8, "1": 23}})
    out = rv.decide(redmi, [], {}, [])  # 53% 4-5 stars and 3.3 on average
    assert out["verdict"] == "poor" and out["reasons"] == [
        "Only 53% of 32 ratings are 4 or 5 stars (poor is under 55%)", "The average rating, 3.3, is under 3.5"]
    ptron = rv.rating_summary({"average": 4.0, "count": 176, "distribution": {"5": 55, "4": 17, "3": 12, "2": 4, "1": 12}})
    assert rv.decide(ptron, [], {}, [])["verdict"] == "mixed"  # 72% 4-5 stars: not good, and never poor


def test_few_ratings_are_not_enough():
    out = rv.decide(rv.rating_summary({"count": 12, "distribution": {"5": 100, "4": 0, "3": 0, "2": 0, "1": 0}}), [], {}, [])
    assert out["verdict"] == "not_enough_reviews" and out["confidence"] == "low"


def test_without_a_summary_the_reviews_read_are_used_with_low_confidence():
    reviews, labels = reviews_and_labels([(5, "Good", label())] * 30 + [(1, "Bad", label())] * 5)
    out = rv.decide(None, reviews, labels, [])
    assert out["verdict"] == "good" and out["rating"]["source"] == "reviews_read" and out["confidence"] == "low"


def test_old_labels_without_quality_fields_are_not_counted():
    reviews, labels = reviews_and_labels([(1, "Melted", {"hazard": True, "experience": "own_experience"})])
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert out["reviews_read"] == 1 and out["reviews_labelled"] == 0 and out["complaints"] == []


def test_signs_of_inflated_reviews():
    burst = [{"text": f"Amazing product number {i}", "rating": 5, "date": "2026-10-03"} for i in range(6)]
    copies = [{"text": "Very good product must buy it now friends", "rating": 5}] * 3
    unverified = [{"text": f"review {i}", "rating": 4, "verified_purchase": i < 2} for i in range(10)]
    kinds = {f["kind"]: f["detail"] for f in rv.trust_signals(burst + copies + unverified)}
    assert kinds["same_day_burst"] == "6 five-star reviews were posted on 3 Oct 2026"
    assert kinds["repeated_text"] == "3 reviews open with the same words"
    assert kinds["few_verified"] == "Only 2 of 10 reviews read are from verified buyers"
    assert rv.trust_signals([{"text": "Good", "rating": 5, "date": "2026-10-03"}]) == []


def test_up_to_ten_complaints_are_returned_most_common_first():
    phrases = ["weak network", "battery drains", "screen flickers", "camera blurry", "phone heats", "speaker crackles",
               "charger slow", "buttons stick", "software buggy", "case cracked", "box damaged", "bloatware apps"]
    rows = [(1, f"r{n}-{k}", label(("other", "neg"), problem=p)) for n, p in enumerate(phrases) for k in range(12 - n)]
    reviews, labels = reviews_and_labels(rows)
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])
    assert len(out["complaints"]) == 10
    assert [c["mentions"] for c in out["complaints"]] == sorted((c["mentions"] for c in out["complaints"]), reverse=True)


def test_flags_lower_confidence():
    reviews, labels = reviews_and_labels(per_star({}))
    flags = [{"kind": "same_day_burst", "detail": "x"}]
    assert rv.decide(rv.rating_summary(SUMMARY), reviews, labels, [])["confidence"] == "high"
    out = rv.decide(rv.rating_summary(SUMMARY), reviews, labels, flags)
    assert out["confidence"] == "low" and out["trust"]["may_be_inflated"] is True


def test_review_verdict_shares_the_safety_checks_stored_reviews(monkeypatch):
    stored = []

    def add_reviews(key, reviews):
        assert key == "listing:https://www.amazon.in/dp/X"
        stored.extend({**r, "id": radar.review_id(r), "evidence_id": f"EV-{len(stored) + i}"} for i, r in enumerate(reviews))

    monkeypatch.setattr(rv.safety, "add_reviews", add_reviews)
    monkeypatch.setattr(rv.safety, "product_reviews", lambda key: stored)
    monkeypatch.setattr(rv.safety, "label_reviews",
                        lambda view, reviews: {r["id"]: label(("durability", "neg"), problem="broke") for r in reviews})
    out = rv.review_verdict({"url": "https://www.amazon.in/dp/X", "title": "Kelvo charger", "rating_summary": SUMMARY,
                             "reviews": [{"text": "Broke in a week", "rating": 1, "verified_purchase": True}]})
    assert out["reviews_read"] == 1 and out["complaints"][0]["phrase"] == "broke"
    assert stored[0]["verified_purchase"] is True
