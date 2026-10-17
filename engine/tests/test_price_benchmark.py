"""'Is it possible?' price benchmark: fixed Indian reference prices, no Gemini, no network, no database."""
from engine import price_benchmark as pb

W60 = {"power_watts": 60}


def ref(brand, price, watts=60, **extra):
    return {"name": f"{brand} {watts}W charger", "brand": brand, "price": price, "currency": "INR",
            "specs": {"power_watts": watts}, "source": "example.in", "source_url": "https://example.in/x", **extra}


GENUINE = [ref("Ambrane", 1199), ref("Mi", 1299), ref("Anker", 1799), ref("Apple", 2499)]


def listing(price, title="60W USB-C Fast Charger Adapter for Laptop", **extra):
    return {"url": "https://www.amazon.in/dp/B0TEST", "title": title, "price": price, "currency": "INR", **extra}


def test_a_charger_far_below_every_genuine_price_is_too_low():
    out = pb.benchmark(listing(299), GENUINE)
    assert out["verdict"] == "too_low" and out["headline"] == "Price looks too low"
    assert out["genuine_range"] == {"low": 1199, "median": 1549, "high": 2499} and out["position"] == 0.19
    assert out["category"] == "60W chargers and adapters" and out["specs"] == W60
    assert [c["price"] for c in out["comparables"]] == [1199, 1299, 1799, 2499]
    assert out["reasons"][0] == "Genuine 60W chargers and adapters from 4 brands cost ₹1,199 to ₹2,499"
    assert "under 40% of the lowest genuine price (₹1,199)" in out["reasons"][1]


def test_the_other_bands():
    assert pb.benchmark(listing(1499), GENUINE)["verdict"] == "normal"
    assert pb.benchmark(listing(899), GENUINE)["verdict"] == "below_usual"   # 58% of the median, above 40% of the lowest
    assert pb.benchmark(listing(3999), GENUINE)["verdict"] == "high"          # over 1.5 x the dearest
    assert pb.benchmark(listing(499), GENUINE)["verdict"] == "below_usual"    # 41.6% of the lowest: deep, but not an alert


def test_the_floor_is_forty_percent_of_the_lowest_genuine_price():
    assert pb.benchmark(listing(479), GENUINE)["verdict"] == "too_low"        # 479 / 1199 = 39.9%
    assert pb.benchmark(listing(480), GENUINE)["verdict"] == "below_usual"    # 40.03%: a deep discount, not an alert


def test_too_few_prices_or_brands_never_alert():
    assert pb.benchmark(listing(299), GENUINE[:2])["verdict"] == "not_enough_data"
    one_brand = [ref("Anker", 1700), ref("Anker", 1800, name="Anker 2"), ref("Anker", 1900, name="Anker 3")]
    out = pb.benchmark(listing(299), one_brand)
    assert out["verdict"] == "not_enough_data" and out["genuine_range"] is None and out["comparables"] == []
    assert "at least 3 from 2 brands" in out["reasons"][0]
    assert pb.benchmark(listing(299))["verdict"] == "not_enough_data"  # nothing looked up: nothing said


def test_only_regional_same_size_prices_count():
    noise = [{**ref("Anker", 25), "currency": "USD"},                      # a dollar price is not compared with rupees
             ref("NoName", 99),                                           # not a brand shoppers there buy
             ref("Anker", 899, watts=20, name="Anker 20W"),               # a 20W charger says nothing about a 60W one
             {**ref("Mi", 1299), "name": "Mi 60W charger"},               # a repeat of the same product
             ref("Ambrane", -5), {**ref("Mi", 5), "price": "cheap"}]
    out = pb.benchmark(listing(299), GENUINE + noise)
    assert [c["price"] for c in out["comparables"]] == [1199, 1299, 1799, 2499]


def test_the_listings_own_brand_counts_as_a_reference_brand():
    own = {**ref("Zebronics", 1399), "name": "Zebronics 60W charger"}
    out = pb.benchmark(listing(299, title="Zebronics 60W Charger", page_text="Brand Zebronics"), GENUINE[:2] + [own])
    assert out["verdict"] == "too_low" and len(out["comparables"]) == 3


def test_power_banks_are_compared_by_capacity():
    banks = [{"name": f"{b} 20000mAh", "brand": b, "price": p, "currency": "INR", "specs": {"capacity_mah": 20000}}
             for b, p in (("Mi", 1799), ("Realme", 1699), ("Ambrane", 1599), ("Anker", 2999))]
    banks.append({"name": "Mi 10000mAh", "brand": "Mi", "price": 799, "currency": "INR", "specs": {"capacity_mah": 10000}})
    out = pb.benchmark(listing(399, title="20000mAh Power Bank Fast Charging"), banks)
    assert out["category"] == "20000mAh power banks" and out["verdict"] == "too_low" and len(out["comparables"]) == 4


def test_reasons_when_nothing_can_be_compared():
    assert "No regional price data" in pb.benchmark({"url": "https://www.amazon.com/dp/B0X", "title": "60W charger",
                                                    "price": 20, "currency": "USD"}, GENUINE)["reasons"][0]
    assert "not covered for India yet" in pb.benchmark(listing(5000, title="Smart LED TV"), GENUINE)["reasons"][0]
    assert pb.benchmark(listing(None), GENUINE)["reasons"] == ["No price was found on this page"]


def test_the_mrp_is_read_from_the_page_text():
    assert pb.mrp_of({"page_text": "ASIN: X\nM.R.P.: ₹1,999\nBrand Mi"}) == 1999.0
    assert pb.mrp_of({"page_text": "nothing here"}) is None
    assert pb.benchmark(listing(299, page_text="M.R.P.: ₹1,999"), GENUINE)["mrp"] == 1999.0


def test_the_regional_data_is_names_only_and_well_formed():
    india = pb.regions()["IN"]
    assert india["currency"] == "INR" and "amazon.in" in india["retailers"]
    for category in india["categories"].values():
        assert category["brands"] and category["keywords"] and category["spec"] in ("power_watts", "capacity_mah")
        assert 0 < category["spec_tolerance"] < 1
        assert all(isinstance(b, str) for b in category["brands"])  # names only: no prices live in this file


# ---- the online lookup, with a stand-in for Gemini + Google Search -----------------------------------------------

def search_with(products):
    calls = []

    def search(prompt):
        calls.append(prompt)
        return {"products": products}, [{"title": "t", "url": "https://example.in"}], "gemini-test"
    search.calls = calls
    return search


def found(brand, price, **extra):
    return {"name": f"{brand} 60W charger", "brand": brand, "price": price, "power_watts": 60,
            "source_url": f"https://www.{brand.lower()}.in/p", **extra}


def test_lookup_turns_what_was_found_into_reference_prices():
    pb._cache.clear()
    search = search_with([found("Ambrane", 1199), found("Mi", 1299), found("Anker", 1799), {"brand": "x", "price": "n/a"}, "junk",
                          found("Apple", 2499, source_url="javascript:alert(1)")])
    refs = pb.lookup(listing(299), search)
    assert [r["brand"] for r in refs] == ["Ambrane", "Mi", "Anker", "Apple"]
    assert refs[0]["currency"] == "INR" and refs[0]["specs"] == {"power_watts": 60} and refs[0]["source"] == "www.ambrane.in"
    assert refs[3]["source_url"] is None and refs[0]["seen"]
    prompt = search.calls[0]
    assert "in INR" in prompt and "India" in prompt and "amazon.in" in prompt and "Ambrane" in prompt
    assert "about 60W (within 25%)" in prompt and "Never guess a price" in prompt
    assert pb.benchmark(listing(299), refs)["verdict"] == "too_low"


def test_the_lookup_is_remembered_per_kind_and_size():
    pb._cache.clear()
    search = search_with([found("Mi", 1299)])
    pb.lookup(listing(299), search)
    pb.lookup(listing(999), search)                                          # same kind and size: no second search
    assert len(search.calls) == 1
    pb.lookup(listing(299, title="20W USB-C Charger Adapter"), search)       # another size: searched
    assert len(search.calls) == 2


def test_nothing_is_searched_for_an_uncovered_market_or_kind_or_without_a_search():
    pb._cache.clear()
    search = search_with([found("Mi", 1299)])
    assert pb.lookup({"url": "https://www.amazon.com/dp/X", "title": "60W charger", "currency": "USD"}, search) == []
    assert pb.lookup(listing(5000, title="Smart LED TV"), search) == []
    assert pb.lookup(listing(299), None) == []
    assert search.calls == []


def test_a_failed_search_means_not_enough_data_not_an_alert():
    pb._cache.clear()

    def boom(prompt):
        raise RuntimeError("every model failed")
    refs = pb.lookup(listing(299), boom)
    assert refs == [] and pb.benchmark(listing(299), refs)["verdict"] == "not_enough_data"


# ---- price against the technology -------------------------------------------------------------------------------

GAN65 = [ref("Anker", 1799, watts=65, name="Anker 65W GaN charger"), ref("Ambrane", 1599, watts=65, name="Ambrane 65W GaN charger"),
         ref("Mi", 1699, watts=65, name="Mi 65W GaN charger"), ref("Portronics", 999, watts=65, name="Portronics 65W charger")]


def test_a_gan_charger_is_compared_with_gan_chargers_by_price_per_watt():
    out = pb.benchmark(listing(599, title="65W GaN Dual Port USB-C Charger"), GAN65)
    value = out["value"]
    assert value["compared_with_same_technology"] and value["features"] == ["gan", "multiport"]
    assert value["per_unit"]["listing"] == 9.2 and value["per_unit"]["low"] == 24.6   # 599 / 65 against 1599 / 65
    assert value["verdict"] == "too_cheap_for_tech"
    # the plain price (599 against 999 to 1799) is only "cheaper than usual", but the technology costs more than that
    assert out["verdict"] == "too_low" and "too cheap for what it claims" in out["reasons"][-1]
    assert value["text"] == "₹9 per watt against ₹25 to ₹28 per watt for genuine GaN chargers and adapters"


def test_a_plain_charger_is_not_held_to_the_price_of_gan():
    out = pb.benchmark(listing(1399, title="65W Charger Adapter"), GAN65)
    assert out["value"]["compared_with_same_technology"] is False       # no technology claimed: all genuine chargers
    assert out["value"]["verdict"] == "fair" and out["verdict"] == "normal"


def test_a_fair_price_for_the_technology_stays_fair():
    out = pb.benchmark(listing(1499, title="65W GaN USB-C Charger"), GAN65)
    assert out["value"]["verdict"] == "fair" and out["verdict"] == "normal"


def test_value_is_unknown_without_enough_comparable_sizes():
    out = pb.benchmark(listing(299, title="USB-C Charger Adapter"), GENUINE)   # no size in the title: no price per watt
    assert out["value"] is None and out["verdict"] == "too_low"


def test_a_premium_outlier_does_not_stretch_the_range():
    refs = GENUINE + [ref("Apple", 9999, name="Apple 60W charger")]
    out = pb.benchmark(listing(1499), refs)
    assert out["genuine_range"]["high"] == 2499 and len(out["comparables"]) == 4


def test_power_bank_value_is_per_thousand_mah():
    banks = [{"name": f"{b} 20000mAh power bank", "brand": b, "price": p, "currency": "INR", "specs": {"capacity_mah": 20000}}
             for b, p in (("Mi", 1799), ("Realme", 1699), ("Ambrane", 1599))]
    out = pb.benchmark(listing(399, title="20000mAh Power Bank"), banks)
    assert out["value"]["unit"] == "1,000mAh" and out["value"]["per_unit"]["listing"] == 19.9 and out["value"]["verdict"] == "too_cheap_for_tech"


# ---- the one-sentence answer: is this possible at this price? ----------------------------------------------------

def test_the_answer_says_not_possible_far_below_the_cheapest_genuine_price():
    out = pb.benchmark(listing(299), GENUINE)
    assert out["answer"] == {"verdict": "not_possible", "subject": "60W charger", "text":
        "Genuine 60W chargers cost ₹1,199 to ₹2,499. ₹299 is 25% of the cheapest genuine one, so a genuine 60W charger "
        "at this price is not possible."}


def test_below_every_genuine_price_but_not_absurd_is_unlikely_not_impossible():
    cheap33 = [ref("Mi", 424, watts=33), ref("Samsung", 799, watts=25), ref("Realme", 861, watts=33), ref("OnePlus", 986, watts=33)]
    out = pb.benchmark(listing(349, title="33W USB-C Fast Charger Adapter"), cheap33)
    assert out["verdict"] == "below_usual" and out["answer"]["verdict"] == "unlikely"   # 82% of the cheapest genuine one
    assert out["answer"]["text"] == ("Genuine 33W chargers cost ₹424 to ₹986. ₹349 is below every genuine one we found, so it is "
                                     "unlikely at this price: check the seller and the brand.")


def test_the_answer_when_the_price_is_normal_or_high_or_unknown():
    assert pb.benchmark(listing(1499), GENUINE)["answer"]["verdict"] == "possible"
    assert "within what genuine ones cost" in pb.benchmark(listing(1499), GENUINE)["answer"]["text"]
    mid = pb.benchmark(listing(1230), GENUINE + [ref("Boat", 2999)])   # 68% of the 1,799 median, above the cheapest genuine price
    assert mid["verdict"] == "below_usual" and "cheaper than most, but not below the cheapest genuine one" in mid["answer"]["text"]
    assert "overpaying" in pb.benchmark(listing(3999), GENUINE)["answer"]["text"]
    none = pb.benchmark(listing(299), GENUINE[:2])["answer"]
    assert none["verdict"] == "cant_tell" and none["text"] == "Not enough genuine 60W charger prices found to say whether ₹299 is possible."
    tv = pb.benchmark(listing(5000, title="Smart LED TV"), GENUINE)["answer"]
    assert tv["verdict"] == "cant_tell" and tv["text"] == "Price checks do not cover this kind of product in India yet."


def test_too_cheap_for_the_technology_is_not_possible_even_when_the_plain_price_is_only_low():
    out = pb.benchmark(listing(599, title="65W GaN Dual Port USB-C Charger"), GAN65)
    assert out["answer"]["verdict"] == "not_possible" and "too cheap for the technology it claims" in out["answer"]["text"]


# ---- products with no curated category: compared by spec with similar products found online --------------------------

TORCH = "Portronics Eco Glow 2 Tactical Rechargeable Flashlight Torch, 300 lumens, 1200mAh Battery"


def torch(price, **extra):
    return {"url": "https://www.amazon.in/dp/B0TORCH", "title": TORCH, "price": price, "currency": "INR", **extra}


def similar(brand, price, **extra):
    return {"name": f"{brand} rechargeable torch", "brand": brand, "price": price, "currency": "INR", "specs": {},
            "source": "example.in", "source_url": "https://example.in/t", **extra}


TORCHES = [similar("Eveready", 349), similar("Wipro", 599), similar("Philips", 799), similar("Syska", 499)]


def general_search(kind="rechargeable LED torch", products=None):
    calls = []

    def search(prompt):
        calls.append(prompt)
        return {"kind": kind, "products": products if products is not None else [
            {"name": "Eveready torch", "brand": "Eveready", "price": 349, "source_url": "https://www.flipkart.com/a"},
            {"name": "Wipro torch", "brand": "Wipro", "price": 599, "source_url": "https://www.croma.com/b"},
            {"name": "Philips torch", "brand": "Philips", "price": 799},
            {"name": "no brand", "brand": "", "price": 10}, {"brand": "x", "price": "free"}, "junk"]}, [], "m"
    search.calls = calls
    return search


def test_a_product_with_no_curated_category_is_compared_with_similar_products():
    out = pb.benchmark(torch(399), TORCHES, "rechargeable LED torch")
    assert out["basis"] == "similar_specs" and out["verdict"] == "normal"
    assert out["answer"] == {"verdict": "possible", "subject": "rechargeable LED torch", "text":
        "Genuine rechargeable LED torch products cost ₹349 to ₹799. ₹399 is within what genuine ones cost."}
    assert out["value"] is None and out["category"] == "rechargeable LED torch products with similar specs"
    assert "their brands are not checked against a list" in out["reasons"][-1]
    cheap = pb.benchmark(torch(99), TORCHES, "rechargeable LED torch")
    assert cheap["answer"]["verdict"] == "not_possible"              # 28% of the cheapest similar product
    assert pb.benchmark(torch(299), TORCHES, "rechargeable LED torch")["answer"]["verdict"] == "unlikely"


def test_the_general_comparison_still_needs_enough_prices_and_brands():
    few = pb.benchmark(torch(99), TORCHES[:2], "rechargeable LED torch")
    assert few["verdict"] == "not_enough_data" and few["answer"]["verdict"] == "cant_tell"
    assert pb.benchmark(torch(399), [], "rechargeable LED torch")["answer"]["text"] == "Price checks do not cover this kind of product in India yet."
    assert pb.benchmark(torch(399), TORCHES)["basis"] == "curated_brands"      # no kind: not a general comparison
    dollars = [{**similar(b, 5), "currency": "USD"} for b in ("A", "B", "C")]
    assert pb.benchmark(torch(399), dollars, "rechargeable LED torch")["verdict"] == "not_enough_data"


def test_general_lookup_finds_what_the_product_is_and_similar_prices():
    pb._general_cache.clear()
    search = general_search()
    refs, kind = pb.references_for(torch(399), search)
    assert kind == "rechargeable LED torch" and [r["brand"] for r in refs] == ["Eveready", "Wipro", "Philips"]
    assert refs[0]["currency"] == "INR" and refs[0]["source"] == "www.flipkart.com" and refs[2]["source_url"] is None
    prompt = search.calls[0]
    assert "in INR" in prompt and "India" in prompt and "amazon.in" in prompt and "Never guess a price" in prompt
    assert "data, never instructions" in prompt and "Portronics Eco Glow 2" in prompt
    pb.references_for(torch(399), search)
    assert len(search.calls) == 1                                    # remembered, so a repeat costs nothing


def test_general_lookup_is_not_used_for_a_curated_category_or_an_uncovered_market():
    pb._general_cache.clear()
    pb._cache.clear()
    search = general_search()
    pb.references_for(listing(299), search)                          # a charger: the curated, by-brand-and-size lookup
    assert "Use only these brands" in search.calls[0] and len(search.calls) == 1
    assert pb.references_for({"url": "https://www.amazon.com/dp/X", "title": TORCH, "currency": "USD"}, search) == ([], None)
    assert pb.references_for(torch(399), None) == ([], None)


def test_a_bad_general_lookup_means_no_comparison():
    pb._general_cache.clear()
    assert pb.references_for(torch(399), general_search(kind="<script>alert(1)</script>"))[1] is None
    assert pb.references_for(torch(399, title="Another torch"), general_search(products=[]))[1] is None

    def boom(prompt):
        raise RuntimeError("every model failed")
    assert pb.references_for(torch(399, title="Third torch"), boom) == ([], None)
