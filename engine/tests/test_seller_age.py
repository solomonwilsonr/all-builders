"""sellerAge: the age band from a seller's public rating counts. Plain code: no Gemini, no network, no database."""
from engine import seller_age as sa


def ask(m30, m90, m12, life, seller="Example Traders"):
    return sa.assess({"seller": seller, "feedback": {"last_30_days": m30, "last_90_days": m90, "last_12_months": m12, "lifetime": life}})


def test_all_ratings_in_the_last_30_days_is_a_very_new_seller():
    out = ask(48, 48, 48, 48)
    assert out["verdict"] == "new" and out["headline"] == "Very new seller" and out["tone"] == "warn"
    assert out["age_days"] == {"min": 0, "max": 30} and out["basis"] == "rating_history"
    assert out["text"] == "All 48 of this seller's ratings are from the last 30 days, so they are likely under a month old here."
    assert out["reasons"] == ["All 48 ratings are from the last 30 days", "Ratings: 48 in 30 days, 48 in 90 days, 48 in 12 months, 48 in total"]
    assert out["ratings"] == {"last_30_days": 48, "last_90_days": 48, "last_12_months": 48, "lifetime": 48}
    assert out["seller"] == "Example Traders" and "does not publish when a seller joined" in out["label"]


def test_the_other_bands():
    recent = ask(10, 60, 60, 60)                      # 50 ratings are 30-90 days old, none older than 90 days
    assert (recent["verdict"], recent["age_days"]) == ("recent", {"min": 30, "max": 90}) and recent["tone"] == "warn"
    year = ask(10, 40, 200, 200)                      # 160 are 3-12 months old, none older than a year
    assert (year["verdict"], year["age_days"], year["tone"]) == ("under_a_year", {"min": 90, "max": 365}, "none")
    old = ask(30, 90, 300, 1200)                      # 900 ratings older than a year
    assert (old["verdict"], old["age_days"], old["tone"], old["headline"]) == ("established", {"min": 365, "max": None}, "ok", "Established seller")
    assert old["reasons"][0] == "900 of 1,200 ratings are older than a year"


def test_a_stray_rating_does_not_move_a_seller_up_a_band():
    assert ask(48, 49, 50, 50)["verdict"] == "new"                      # 2 older ratings: under the gap of 3
    assert ask(48, 51, 51, 51)["verdict"] == "recent"                   # 3 are 30-90 days old: a real gap
    big = ask(500, 1000, 4_995, 5_000)                                  # 5 older than a year of 5,000: under 1% (50)
    assert big["verdict"] != "established" and big["verdict"] == "under_a_year"
    assert ask(500, 1000, 4_900, 5_000)["verdict"] == "established"     # 100 of 5,000 older than a year


def test_very_few_ratings_cannot_place_the_age_and_say_so():
    out = ask(3, 3, 3, 3)
    assert out["verdict"] == "few_ratings" and out["tone"] == "warn" and out["age_days"] is None
    assert out["text"] == "Only 3 ratings in total: too few to tell how long this seller has been active, and little track record."
    assert ask(0, 0, 0, 0)["text"].startswith("Only 0 ratings in total")
    assert ask(1, 1, 1, 1)["text"].startswith("Only 1 rating in total")
    assert ask(9, 9, 9, 9)["verdict"] == "few_ratings" and ask(10, 10, 10, 10)["verdict"] == "new"


def test_unreadable_counts_say_nothing_rather_than_guess():
    for feedback in (None, {}, "x", {"last_30_days": 1}, {"last_30_days": 5, "last_90_days": 3, "last_12_months": 9, "lifetime": 9},
                     {"last_30_days": 1.5, "last_90_days": 2, "last_12_months": 3, "lifetime": 4},
                     {"last_30_days": -1, "last_90_days": 2, "last_12_months": 3, "lifetime": 4},
                     {"last_30_days": True, "last_90_days": 2, "last_12_months": 3, "lifetime": 4},
                     {"last_30_days": "5", "last_90_days": 5, "last_12_months": 5, "lifetime": 5}):
        out = sa.assess({"seller": "x", "feedback": feedback})
        assert out["verdict"] == "unknown" and out["age_days"] is None and out["ratings"] is None
    assert sa.assess({})["seller"] is None
