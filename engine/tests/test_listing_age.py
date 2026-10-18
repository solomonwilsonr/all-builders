"""sellerAge widget: the listing's age from "Date First Available". Plain code: no Gemini, no network, no database."""
from datetime import date

from engine import listing_age as la

TODAY = date(2026, 10, 17)


def ask(text, **extra):
    return la.assess({"first_available": text, **extra}, TODAY)


def test_a_listing_of_a_few_days_is_new():
    out = ask("12 October 2026")
    assert (out["verdict"], out["headline"], out["tone"], out["age_days"], out["listed_on"]) == ("new", "New listing", "warn", 5, "2026-10-12")
    assert out["text"] == "This product was first listed 5 days ago (12 October 2026). A brand-new listing has little track record."
    assert out["reasons"] == ["Date First Available: 12 October 2026 (5 days ago)",
                              "This is the listing's age, not the seller's: marketplaces do not publish when a seller joined"]
    assert out["basis"] == "date_first_available" and "not the seller's" in out["label"]


def test_the_other_bands_and_their_wording():
    recent = ask("1 September 2026")                                  # 46 days
    assert (recent["verdict"], recent["tone"], recent["text"]) == ("recent", "warn",
        "This product was first listed 46 days ago (1 September 2026), so it has a short track record.")
    year = ask("17 March 2026")                                       # 214 days
    assert (year["verdict"], year["tone"], year["text"]) == ("under_a_year", "none",
        "This product was first listed about 7 months ago (17 March 2026).")
    old = ask("3 February 2023")
    assert (old["verdict"], old["headline"], old["tone"], old["text"]) == ("established", "Long-listed product", "ok",
        "This product was first listed about 3 years ago (3 February 2023).")


def test_the_band_edges():
    assert ask("18 September 2026")["verdict"] == "new"               # 29 days
    assert ask("17 September 2026")["verdict"] == "recent"            # 30 days
    assert ask("19 July 2026")["verdict"] == "under_a_year"           # 90 days
    assert ask("20 July 2026")["verdict"] == "recent"                 # 89 days
    assert ask("17 October 2025")["verdict"] == "established"         # 365 days
    assert ask("18 October 2025")["verdict"] == "under_a_year"
    assert "today" in ask("17 October 2026")["text"] and "1 day ago" in ask("16 October 2026")["text"]


def test_dates_as_amazon_prints_them():
    for text in ("12 March 2026", "12 Mar 2026", "March 12, 2026", "Mar 12 2026", "12/03/2026", "2026-03-12", "\u200E12 March 2026",
                 "12 March 2026 (listed)"):
        assert la.parse_date(text) == date(2026, 3, 12), text
    assert la.parse_date("5 Sept 2025") == date(2025, 9, 5)
    for bad in (None, "", "soon", "31 Febtober 2026", "31 February 2026", "13/13/2026", 5):
        assert la.parse_date(bad) is None, bad


def test_the_date_falls_back_to_the_page_text():
    page = "Item Weight 450 g\nDate First Available : 7 August 2026\nManufacturer Example"
    out = la.assess({"page_text": page}, TODAY)
    assert out["verdict"] == "recent" and out["listed_on"] == "2026-08-07"
    assert la.assess({"first_available": "12 October 2026", "page_text": page}, TODAY)["listed_on"] == "2026-10-12"   # the page's own field wins
    assert la.assess({"first_available": "garbled", "page_text": page}, TODAY)["listed_on"] == "2026-08-07"


def test_no_date_a_future_date_or_an_absurd_one_says_nothing():
    for listing in ({}, {"first_available": ""}, {"page_text": "no date here"}, {"first_available": "1 January 2030"},
                    {"first_available": "1 January 1980"}, {"reviews_read": 12}, {"reviews_read": 0}):
        out = la.assess(listing, TODAY)
        assert out["verdict"] == "unknown" and out["age_days"] is None and out["listed_on"] is None, listing
    assert la.assess({}, TODAY)["text"] == "This page does not show when the product was first listed."


# ---- no date on the page: the first review, then "no reviews" ---------------------------------------------------------

def reviews(**extra):
    return la.assess({"reviews_read": 7, "ratings_total": 9, **extra}, TODAY)


def test_when_every_review_was_read_the_oldest_is_the_first_review():
    out = reviews(oldest_review="2026-10-02", reviews_complete=True)
    assert (out["verdict"], out["headline"], out["tone"], out["basis"], out["age_days"], out["listed_on"]) == (
        "new", "New listing", "warn", "first_review", 15, "2026-10-02")
    assert out["text"] == ("The first review of this product is from 15 days ago (2 October 2026), so it has been listed about "
                           "that long. A brand-new listing has little track record.")
    assert out["reasons"][0] == "No \"Date First Available\" on this page; the oldest of all its reviews is from 2 October 2026"
    assert reviews(oldest_review="2026-05-01", reviews_complete=True)["verdict"] == "under_a_year"
    assert reviews(oldest_review="2024-05-01", reviews_complete=True)["verdict"] == "established"


def test_a_page_date_wins_over_the_reviews():
    out = reviews(first_available="3 February 2023", oldest_review="2026-10-02", reviews_complete=True)
    assert out["basis"] == "date_first_available" and out["verdict"] == "established"


def test_a_popular_product_only_gets_a_floor_never_a_new_listing():
    """Only some of a popular product's reviews were read: the oldest one read says nothing about how new it is."""
    out = reviews(oldest_review="2026-10-02", reviews_read=50, ratings_total=3107)     # reviews_complete missing
    assert (out["verdict"], out["tone"], out["basis"]) == ("listed_at_least", "none", "review_floor")
    assert out["headline"] == "Listed for at least 15 days"
    assert out["text"] == ("The oldest review we read is from 15 days ago (2 October 2026), so this product has been listed for at "
                           "least that long. We did not read every review, so it may be much older.")
    assert reviews(oldest_review="2026-10-02", reviews_complete=False)["verdict"] == "listed_at_least"
    assert reviews(oldest_review="2025-01-10")["headline"] == "Listed for at least about 22 months"


def test_no_reviews_is_said_only_when_the_reviews_were_really_read():
    out = la.assess({"reviews_read": 0, "reviews_complete": True}, TODAY)
    assert (out["verdict"], out["headline"], out["tone"], out["basis"]) == ("no_reviews", "No reviews yet", "warn", "no_reviews")
    assert out["text"] == "This product has no reviews yet: a very new or untested listing."
    assert la.assess({"ratings_total": 0}, TODAY)["verdict"] == "no_reviews"
    assert la.assess({"reviews_read": 0}, TODAY)["verdict"] == "unknown"                  # could not read them: no claim
    assert la.assess({"reviews_read": 0, "reviews_complete": False}, TODAY)["verdict"] == "unknown"
    assert la.assess({"reviews_read": 0, "reviews_complete": "yes"}, TODAY)["verdict"] == "unknown"
    assert la.assess({"reviews_read": -1, "reviews_complete": True}, TODAY)["verdict"] == "unknown"


def test_a_bad_review_date_is_ignored():
    for bad in ("soon", "2030-01-01", "1980-01-01", None, 5):
        assert reviews(oldest_review=bad, reviews_complete=True)["verdict"] == "unknown", bad


# ---- the brand card ("10+ years on Amazon") ---------------------------------------------------------------------------

PORTRONICS = ("About this item\nSimilar\nTop Brand\nPortronics\n84% positive ratings from 10K+ customers\n100K+ recent orders from "
              "this brand\n10+ years on Amazon\nRufus AI\nLooking for specific info?")
MAK = "Top Brand\nMAK\n77% positive ratings from 1K+ customers\n10K+ recent orders from this brand\n1+ year on Amazon\nProduct Description"


def test_the_brand_card_is_read_from_the_page_text():
    assert la.brand_card({"page_text": PORTRONICS}) == {"name": "Portronics", "years_on_amazon": "10+",
        "positive_ratings": {"percent": 84, "customers": "10K+"}, "recent_orders": "100K+"}
    assert la.brand_card({"page_text": MAK}) == {"name": "MAK", "years_on_amazon": "1+",
        "positive_ratings": {"percent": 77, "customers": "1K+"}, "recent_orders": "10K+"}
    assert la.brand_card({"brand_text": MAK, "page_text": "nothing"})["name"] == "MAK"       # the extension's own snippet counts too
    assert la.brand_card({"page_text": "7 years on Amazon"}) == {"name": None, "years_on_amazon": "7", "positive_ratings": None, "recent_orders": None}
    assert la.brand_card({"page_text": "Top Brand Acme 1,2 orders"}) is None
    assert la.brand_card({}) is None


def test_the_brand_card_sits_beside_the_age_and_never_changes_it():
    base = la.assess({"first_available": "2 April 2025"}, TODAY)
    with_brand = la.assess({"first_available": "2 April 2025", "page_text": PORTRONICS}, TODAY)
    assert base["brand"] is None and with_brand["brand"]["years_on_amazon"] == "10+"
    assert {k: v for k, v in with_brand.items() if k != "brand"} == {k: v for k, v in base.items() if k != "brand"}
    unknown = la.assess({"page_text": PORTRONICS}, TODAY)                    # no date and no reviews: the brand card still shows
    assert unknown["verdict"] == "unknown" and unknown["brand"]["name"] == "Portronics"


def test_the_portronics_torch_payload_from_the_real_page():
    out = la.assess({"first_available": None, "page_text": PORTRONICS, "oldest_review": "2026-03-24", "reviews_read": 53,
                     "reviews_complete": False, "ratings_total": 3111}, TODAY)
    assert (out["verdict"], out["headline"], out["basis"], out["age_days"]) == ("listed_at_least", "Listed for at least about 7 months", "review_floor", 207)
    assert out["brand"]["years_on_amazon"] == "10+"
