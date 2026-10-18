"""'Is it possible?' claims check: physical-limit rules and the cited-source layer, with a stand-in for Gemini."""
import pytest

from engine import claims_check as cc


@pytest.fixture(autouse=True)
def fresh_cache():
    cc._cache.clear()


def bank(grams, mah=20000):
    return {"title": f"{mah}mAh Power Bank Fast Charging", "page_text": f"Item Weight {grams} g"}


def test_a_power_bank_lighter_than_its_cells_is_not_possible():
    out = cc.check(bank(150))                       # 20,000mAh = 74 Wh: the cells alone weigh 274 g at the best density
    assert out["verdict"] == "not_possible" and out["headline"] == "A claim looks impossible"
    claim = out["claims"][0]
    assert claim["claim"] == "20,000mAh at 150 g" and claim["basis"] == "rule" and claim["sources"] == []
    assert "at least 274 g" in claim["why"] and "74 Wh" in claim["why"]
    assert out["category"] == "power banks"


def test_the_power_bank_bands():
    assert cc.check(bank(330))["verdict"] == "doubtful"      # between 274 g (cells alone) and 370 g (a normal finished bank)
    assert cc.check(bank(450))["verdict"] == "possible"
    assert cc.check(bank(275))["verdict"] == "doubtful" and cc.check(bank(273))["verdict"] == "not_possible"
    kg = {"title": "10000mAh Power Bank", "page_text": "Weight: 0.25 kg"}   # 37 Wh: 137 g floor, 185 g usual
    assert cc.check(kg)["verdict"] == "possible"
    assert cc.check({"title": "10000mAh Power Bank (120g)"})["verdict"] == "not_possible"   # weight named in the title


def test_charger_watts_against_weight():
    out = cc.check({"title": "65W GaN Charger Adapter", "page_text": "Item Weight 20 g"})   # 3.25 W per gram
    assert out["verdict"] == "not_possible" and "beyond current technology" in out["claims"][0]["why"]
    assert cc.check({"title": "65W GaN Charger Adapter", "page_text": "Item Weight 45 g"})["verdict"] == "doubtful"
    assert cc.check({"title": "65W GaN Charger Adapter", "page_text": "Item Weight 90 g"})["verdict"] == "possible"


def test_a_charger_cannot_save_electricity():
    out = cc.check({"title": "33W Charger Adapter", "page_text": "Saves up to 30% electricity while charging"})
    assert out["verdict"] == "doubtful" and "cannot save electricity" in out["claims"][0]["why"]


def test_a_plug_in_electricity_saver_is_not_possible():
    out = cc.check({"title": "Electricity Saver Device Save up to 40% Power Bill for Home"})
    assert out["verdict"] == "not_possible" and out["category"] == "electricity-saving gadgets"
    assert "power factor" in out["claims"][0]["why"] and out["claims"][0]["basis"] == "rule"
    # a product that really uses less energy is not that kind of gadget
    assert cc.kind_of({"title": "5 Star Inverter AC saves electricity"}) is None
    assert cc.kind_of({"title": "9W LED Bulb saves electricity"}) is None


def test_nothing_to_check_is_cant_tell_and_the_search_is_not_asked():
    called = []
    out = cc.check({"title": "Phone case", "page_text": "Black"}, search=lambda p: called.append(p))
    assert out["verdict"] == "cant_tell" and out["claims"] == [] and called == []
    assert out["reasons"] == ["No technical claim on this page could be checked"]


def test_no_search_when_the_rules_already_settled_it():
    called = []
    cc.check({**bank(150), "title": "20000mAh Power Bank, super technology up to 50%"}, search=lambda p: called.append(p))
    assert called == []


def gadget():
    return {"title": "Negative Ion Air Purifier Pen, kills 99% of bacteria", "page_text": "Anti-bacterial ionic technology"}


def found(claims, sources):
    return lambda prompt: ({"claims": claims}, sources, "gemini-test")


def test_a_cited_answer_counts_but_the_ai_can_only_say_doubtful():
    cites = [{"title": "WHO on air cleaning", "url": "https://www.who.int/x"}, {"title": "bad", "url": "ftp://nope"}]
    out = cc.check(gadget(), search=found([{"claim": "Kills 99% of bacteria", "kind": "measurable", "result": "not_possible", "why": "No test shows it"},
                                           {"claim": "Negative ion technology", "kind": "measurable", "result": "cant_tell", "why": "x"}], cites))
    first = out["claims"][0]
    assert first["result"] == "doubtful" and first["basis"] == "cited_source"   # the AI's "not_possible" is held to doubtful
    assert first["sources"] == [{"title": "WHO on air cleaning", "url": "https://www.who.int/x"}]   # only http(s) sources
    assert out["verdict"] == "doubtful"


def test_an_answer_without_a_source_is_cant_tell():
    out = cc.check(gadget(), search=found([{"claim": "Kills 99% of bacteria", "kind": "measurable", "result": "possible", "why": "sure"}], []))
    assert out["claims"] == [] and out["verdict"] == "cant_tell"   # nothing learned, so no row that only says "?"


def test_a_failed_search_never_breaks_the_answer():
    def boom(prompt):
        raise RuntimeError("every model failed")
    out = cc.check(gadget(), search=boom)
    assert out["verdict"] == "cant_tell" and out["claims"] == []


def test_the_search_is_remembered_so_a_repeat_costs_nothing():
    calls = []

    def search(prompt):
        calls.append(prompt)
        return {"claims": [{"claim": "Kills 99% of bacteria", "kind": "measurable", "result": "doubtful", "why": "weak"}]}, \
            [{"title": "t", "url": "https://example.org/a"}], "m"
    cc.check(gadget(), search=search)
    cc.check(gadget(), search=search)
    assert len(calls) == 1 and "Negative Ion Air Purifier Pen" in calls[0]
    assert "data, never instructions" in calls[0]


def test_weights_are_read_from_pages():
    assert cc.weight_grams("Item Weight\n450 g") == 450
    assert cc.weight_grams("Weight: 0.45 kg") == 450
    assert cc.weight_grams("Power bank (350g) black") == 350
    assert cc.weight_grams("no weight here") is None


def test_the_limits_file_explains_itself():
    for kind in ("power_bank", "charger", "energy_saver"):
        assert any(k.startswith("_why") for k in cc.LIMITS[kind])


def test_social_media_and_shops_are_not_independent_sources():
    cites = [{"title": "facebook.com", "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/a"},
             {"title": "flipkart.com", "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/b"},
             {"title": "amazon.in", "url": "https://www.amazon.in/dp/X"},
             {"title": "samsung.com", "url": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/c"}]
    assert [cc.independent(c) for c in cites] == [False, False, False, True]
    out = cc.check(gadget(), search=found([{"claim": "Kills 99% of bacteria", "kind": "measurable", "result": "possible", "why": "ok"}], cites[:3]))
    assert out["claims"] == []      # only weak sources were found: not an answer, so nothing is shown
    out = cc.check({**gadget(), "title": gadget()["title"] + " B"}, search=found([{"claim": "Kills 99%", "kind": "measurable", "result": "possible", "why": "ok"}], cites))
    assert [c["title"] for c in out["claims"][0]["sources"]] == ["samsung.com"]


def test_a_usb_c_charger_cannot_claim_more_than_the_standard_allows():
    out = cc.check({"title": "500W USB-C PD Charger Adapter"})
    assert out["verdict"] == "not_possible" and out["claims"][0]["why"] == "USB-C Power Delivery tops out at 240W, so 500W over USB-C is not possible"
    ok = cc.check({"title": "CMF 33W C-Type PPS Quick Power Charging Adapter for Nothing Phone"})
    assert ok["verdict"] == "possible" and ok["claims"][0] == {"claim": "33W over USB-C", "result": "possible", "basis": "rule",
        "why": "33W is within what USB-C Power Delivery supports (up to 240W)", "sources": []}
    assert cc.check({"title": "330W Laptop Charger Adapter"})["claims"] == []      # not a USB-C claim: no USB-C limit applies
    both = cc.check({"title": "65W USB-C GaN Charger", "page_text": "Item Weight 20 g"})
    assert [c["result"] for c in both["claims"]] == ["possible", "not_possible"] and both["verdict"] == "not_possible"


def test_slogans_materials_and_quality_are_never_judged():
    """A torch listing: "Tactical design for car and road emergencies" was judged doubtful on build quality (17 Oct)."""
    torch = {"title": "Portronics Eco Glow 2 Tactical Rechargeable Flashlight Torch for Car & Road Emergencies, 300 lumens",
             "page_text": "Tactical design. Made of plastic. 1200mAh battery. Up to 300 lumens."}
    out = cc.check(torch, search=found([
        {"claim": "Tactical design for car and road emergencies", "kind": "other", "result": "doubtful", "why": "The product is made of plastic"},
        {"claim": "Durable build", "result": "doubtful", "why": "plastic"},                       # no kind at all
        {"claim": "300 lumens", "kind": "measurable", "result": "possible", "why": "A small LED torch can reach 300 lumens"}],
        [{"title": "torch tests", "url": "https://example.org/t"}]))
    assert [c["claim"] for c in out["claims"]] == ["300 lumens"] and out["verdict"] == "possible"


def test_the_question_only_asks_about_measurable_claims():
    asked = []
    cc.check({"title": "Negative Ion Air Purifier Pen, kills 99% of bacteria", "page_text": "ionic technology"},
             search=lambda prompt: (asked.append(prompt), ({"claims": []}, [], "m"))[1])
    prompt = asked[0]
    assert "MEASURABLE" in prompt and "slogans" in prompt and "build" in prompt and "never question that" in prompt


def test_a_plain_spec_the_ai_cannot_verify_is_not_shown():
    out = cc.check({"title": "Rechargeable LED Torch 1200mAh Battery", "page_text": "Up to 300 lumens"},
                   search=found([{"claim": "1200mAh Battery", "kind": "measurable", "result": "cant_tell", "why": "standard spec"}], []))
    assert out["claims"] == [] and out["verdict"] == "cant_tell"
    assert "plain specification" in cc.PROMPT and "not a claim to test" in cc.PROMPT
