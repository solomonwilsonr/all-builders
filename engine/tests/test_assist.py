"""Owner help (engine/assist.py, engine/household.py, engine/manual.py, the chat's owner tools). No network,
no database, no Gemini."""
import asyncio
import base64
from datetime import date

import pytest
from fastapi import HTTPException

from engine import assist, household, manual
from engine.agents import concierge, runtime, screenshot

# ---------- compatibility ----------

def test_a_big_enough_usb_c_pd_charger_works():
    out = assist.compatibility({"connector": "USB-C", "watts": 65, "protocols": ["USB PD 3.0"]},
                               {"connector": "Type-C", "watts": 60, "volts": 20, "protocols": ["PD"]})
    assert out["verdict"] == "works" and not out["check_on_label"]


def test_a_small_usb_charger_charges_a_laptop_slowly_or_not_at_all():
    assert assist.compatibility({"connector": "usb-c", "watts": 45}, {"connector": "usb-c", "watts": 65})[
        "verdict"] == "works_slowly"
    assert assist.compatibility({"connector": "usb-c", "watts": 20}, {"connector": "usb-c", "watts": 65})[
        "verdict"] == "wont_work"


def test_a_barrel_plug_at_the_wrong_voltage_is_dont_use():
    out = assist.compatibility({"connector": "barrel 5.5x2.5", "volts": 12, "watts": 60},
                               {"connector": "barrel", "volts": 19.5, "watts": 65})
    assert out["verdict"] == "dont_use" and any("Wrong voltage" in r for r in out["reasons"])


def test_a_plug_that_does_not_fit_and_unknown_power():
    assert assist.compatibility({"connector": "lightning"}, {"connector": "usb-c"})["verdict"] == "wont_work"
    out = assist.compatibility({"connector": "usb-c"}, {"connector": "usb-c"})
    assert out["verdict"] == "not_enough_info" and out["check_on_label"]


def test_missing_fast_charge_standard_is_normal_speed():
    out = assist.compatibility({"connector": "usb-c", "watts": 30, "protocols": ["PD"]},
                               {"connector": "usb-c", "watts": 25, "protocols": ["PD", "PPS", "Quick Charge"]})
    assert out["verdict"] == "works" and any("Fast charging" in r for r in out["reasons"])


# ---------- power setups ----------

def test_heater_on_daisy_chained_boards_is_unsafe():
    out = assist.setup([{"name": "room heater", "watts": 2000}],
                       [{"kind": "extension", "rated_amps": 6}, {"kind": "extension", "rated_amps": 10}], "in")
    text = " ".join(out["problems"])
    assert out["verdict"] == "unsafe" and "daisy-chained" in text and "wall socket" in text and "overloaded" in text
    assert "16 A" in text


def test_light_load_within_rating_is_ok_and_unknown_rating_is_asked():
    assert assist.setup([{"name": "phone charger", "watts": 20}], [{"kind": "extension", "rated_watts": 2400}],
                        "in")["verdict"] == "ok"
    out = assist.setup([{"name": "lamp", "watts": 10}], [{"kind": "adapter"}], "in")
    assert out["verdict"] == "not_enough_info" and out["check_on_label"]


def test_us_appliance_in_japan_is_fine_but_in_india_needs_a_converter():
    assert assist.setup([{"name": "fan", "watts": 40, "volts": 110}], [], "jp")["verdict"] == "ok"
    assert assist.setup([{"name": "fan", "watts": 40, "volts": 110}], [], "in")["verdict"] == "unsafe"


def test_close_to_the_limit():
    assert assist.setup([{"name": "monitor", "watts": 2100}], [{"kind": "extension", "rated_watts": 2400}],
                        "au")["verdict"] in ("close_to_limit", "unsafe")
    assert assist.setup([{"name": "pc", "watts": 900}], [{"kind": "cable", "rated_watts": 1000}],
                        "au")["verdict"] == "close_to_limit"


# ---------- symptoms ----------

def test_symptoms_set_the_urgency_and_never_suggest_testing():
    fire = assist.symptoms(["smoke_or_flame", "warm"], "power bank", "jp")
    assert fire["urgency"] == "emergency" and fire["emergency_number"] == "119"
    swollen = assist.symptoms(["swelling"], "phone")
    assert swollen["urgency"] == "stop" and any("swollen" in s for s in swollen["steps"])
    warm = assist.symptoms(["warm"], "charger")
    assert warm["urgency"] == "watch" and warm["emergency_number"] is None
    for out in (fire, swollen, warm):
        assert assist.NO_TESTING in out["steps"]
    assert assist.symptoms(["made_up"])["urgency"] == "watch"


# ---------- suitability ----------

def test_suitability_uses_evidence_and_says_what_it_cannot_know():
    out = assist.suitability({"children_under_3": True, "allergies": ["latex", "nickel"], "accessibility": ["low vision"]},
                             ["choking", "fire_burn"], "Remote control with CR2032 coin battery, nickel-plated", "toy")
    who = {c["for"] for c in out["concerns"]}
    assert {"children under 3", "children", "nickel allergy"} <= who
    assert any("latex" in u for u in out["no_evidence"]) and any("low vision" in u for u in out["no_evidence"])
    assert assist.suitability({}, [], "")["concerns"] == []


# ---------- repair, disposal, pressure, drafts ----------

def test_repair_or_replace_order():
    assert assist.repair_or_replace({"recalled": True, "under_warranty": True})["advice"] == "recall remedy"
    assert assist.repair_or_replace({"under_warranty": True})["advice"] == "warranty service"
    assert assist.repair_or_replace({"kind": "power bank", "safety_symptom": True})["advice"] == "replace it"
    assert assist.repair_or_replace({"kind": "fridge", "repair_quote": 9000, "replacement_price": 15000})[
        "advice"] == "replace it"
    assert assist.repair_or_replace({"kind": "fridge", "repair_quote": 2000, "replacement_price": 15000})[
        "advice"] == "qualified repair"


def test_disposal_is_official_and_never_household_waste():
    out = assist.disposal("au", "power bank", damaged=True)
    assert any("B-cycle" in o["where"] for o in out["options"])
    assert any("household waste" in p for p in out["prepare"]) and any("tape" in p for p in out["prepare"])
    assert any("swollen" in p for p in out["prepare"])
    assert assist.disposal("Australia")["market"] == "au" and assist.disposal("JP")["market"] == "jp"
    assert assist.disposal("vn")["options"] == [{"where": w, "how": h} for w, h in assist.GENERIC_DISPOSAL]


def test_pressure_tactics_are_explained_once_and_unknown_ones_dropped():
    out = assist.pressure([{"tactic": "countdown_timer", "quote": "Ends in 04:59"}, {"tactic": "countdown_timer"},
                           {"tactic": "hypnosis"}, {"tactic": "preselected_extras", "quote": "Add protection plan"}],
                          "in")
    assert [t["tactic"] for t in out["tactics"]] == ["countdown_timer", "preselected_extras"]
    assert "CCPA" in out["tactics"][0]["india_rule"]
    assert "india_rule" not in assist.pressure([{"tactic": "low_stock"}], "jp")["tactics"][0]


def test_reports_fill_what_was_given_and_mark_the_rest():
    report = assist.incident_report({"brand": "Kelvo", "model": "CX-65", "what_happened": "Got very hot and melted",
                                     "symptoms": ["very hot", "melting"], "market": "in"})
    assert "Kelvo" in report["title"] and "Bought from" in report["missing"]
    assert any("National Consumer Helpline" in s["to"] for s in report["send_to"])
    request = assist.support_request({"brand": "Kelvo", "product": "charger", "order_ref": "408-1", "bought_on":
                                      "2026-09-30", "bought_from": "amazon.in", "warranty_until": "2027-09-30",
                                      "problem": "It gets very hot", "request": "replacement"})
    assert "order 408-1" in request["subject"] and "until 2027-09-30" in request["body"]
    assert "Please replace it" in request["body"]
    assert assist._name({"product": "Kelvo CX-65 65W charger", "brand": "Kelvo", "model": "CX-65"}) == \
        "Kelvo CX-65 65W charger"
    assert assist._name({"product": "charger", "brand": "Kelvo", "model": "CX-65"}) == "Kelvo charger CX-65"


# ---------- household dates ----------

def test_household_dates_and_due_soon():
    d = household.dates({"bought_on": "2026-01-31", "return_days": 10, "warranty_months": 1})
    assert d["return_by"] == date(2026, 2, 10) and d["warranty_until"] == date(2026, 2, 28)
    assert household.dates({"bought_on": "2026-01-31", "warranty_until": "2028-01-01",
                            "warranty_months": 12})["warranty_until"] == date(2028, 1, 1)
    rows = [{"item_id": "HI-1", "name": "charger", "return_by": "2026-10-21", "warranty_until": "2027-10-01"},
            {"item_id": "HI-2", "name": "kettle", "return_by": "2026-10-01"}]
    soon = household.due(rows, date(2026, 10, 18))
    assert soon == [{"item_id": "HI-1", "name": "charger", "ends": "return", "until": "2026-10-21", "days_left": 3}]
    with pytest.raises(ValueError):
        household.add("public", None, {"name": "x"})


# ---------- manual ----------

def pdf_url(pages: int) -> str:
    body = b"%PDF-1.4\n" + b"<< /Type /Pages /Count 2 >>\n" + b"<< /Type /Page >>\n" * pages
    return "data:application/pdf;base64," + base64.b64encode(body).decode()


def test_manual_decode_and_page_references():
    _, pages = manual.decode(pdf_url(3))
    assert pages == 3
    refs = manual.keep_references([{"page": 2, "quote": "Unplug before cleaning"}, {"page": 9}, {"page": 2},
                                   {"page": "1"}], pages)
    assert refs == [{"page": 2, "quote": "Unplug before cleaning"}]
    for bad in ("data:image/png;base64,AAAA", "data:application/pdf;base64,"
                + base64.b64encode(b"not a pdf").decode()):
        with pytest.raises(manual.BadDocument):
            manual.decode(bad)


def test_a_manual_question_is_answered_from_the_manual_with_pages(monkeypatch):
    monkeypatch.setattr(manual, "ask", lambda data, pages, q, lang, history="": {
        "answered": True, "answer": "Error E4 means the filter is blocked.", "references": [
            {"page": 12, "printed_page": "11", "quote": "E4 filter blocked"}], "safety_warning": "Unplug it first.",
        "unreferenced": False, "pages_in_file": 20})
    runtime.start(None)
    out = asyncio.run(concierge.chat_session({"product_id": "unmatched", "message": "What does E4 mean?",
                                              "document": pdf_url(20)}))
    text = out["messages"][0]["text"]
    assert "(Manual: p. 11.)" in text and "Unplug it first" in text and out["manual"]["references"]
    with pytest.raises(HTTPException):
        asyncio.run(concierge.chat_session({"message": "hi", "document": "data:text/plain;base64,aGk="}))


# ---------- images: receipts and pressure ----------

def test_a_receipt_becomes_household_items_not_an_investigation():
    seen = {"kind": "receipt", "shop": "www.Amazon.in", "currency": "INR", "receipt": {
        "order_number": "408-1", "purchase_date": "2026-09-30", "total": 1499,
        "items": [{"name": "65W charger", "brand": "Kelvo", "model_number": "CX-65", "price": 1499}, {"price": 5}],
        "return_days": 10}}
    assert screenshot.to_listing(seen) == {}
    r = screenshot.receipt(seen)
    assert r["shop"] == "amazon.in" and r["return_days"] == 10 and r["items"] == [
        {"name": "65W charger", "brand": "Kelvo", "model": "CX-65", "price": 1499}]
    assert screenshot.receipt({"kind": "product_page"}) is None


def test_pressure_on_a_cart_screenshot_is_explained(monkeypatch):
    monkeypatch.setattr(screenshot, "decode", lambda image: (b"x", "image/png"))
    monkeypatch.setattr(screenshot, "read", lambda data, mime: {
        "kind": "product_page", "currency": "INR",
        "pressure": [{"tactic": "countdown_timer", "quote": "Deal ends in 09:59"}]})
    runtime.start(None)
    out = asyncio.run(concierge.check_image("data:image/png;base64,eA==", "en"))
    assert out["pressure_tactics"][0]["tactic"] == "countdown_timer" and "india_rule" in out["pressure_tactics"][0]


# ---------- the owner comes from the request, never the body ----------

def test_owner_is_set_from_the_header_not_the_body(monkeypatch):
    from engine.agents import handler

    class Request:
        def __init__(self, headers):
            self.headers, self.state = headers, type("State", (), {})()
    body = handler._owner({"mode": "chat", "_owner": "OW-someone-else", "_tenant": "acme"}, Request({"x-owner-ref": "u1"}))
    assert body["_owner"].startswith("OW-") and body["_owner"] != "OW-someone-else" and body["_tenant"] == "public"
    assert handler._owner({"_owner": "OW-x"}, Request({}))["_owner"] is None


def test_owner_tools_are_on_the_concierge_and_state_reaches_them(monkeypatch):
    names = {getattr(t, "__name__", getattr(t, "name", "")) for t in concierge.concierge("m").tools}
    assert {"guide_symptoms", "check_compatibility", "find_household_products", "share_household"} <= names
    seen = {}

    async def fake_run(build, prompt, state=None, timeout_s=45):
        seen.update(state)
        return "Stop using it.", {}
    monkeypatch.setattr(concierge.runtime, "run", fake_run)
    runtime.start(None)
    asyncio.run(concierge.chat_session({"product_id": "unmatched", "message": "My charger gets hot", "_owner": "OW-1",
                                        "context": {"url": "https://www.amazon.co.jp/dp/X"}}))
    assert seen["owner"] == "OW-1" and seen["tenant"] == "public" and seen["market"] == "jp"


# ---------- second round: voice, specs, compare, consent, reminders, memory ----------

def test_voice_notes_decode_with_codec_parameters():
    from engine.agents import listen
    data, mime = listen.decode("data:audio/ogg;codecs=opus;base64," + base64.b64encode(b"OggS....").decode())
    assert data.startswith(b"OggS") and mime == "audio/ogg"
    assert listen.decode("data:audio/x-m4a;base64,AAAA")[1] == "audio/mp4"
    with pytest.raises(listen.BadAudio):
        listen.decode("data:video/mp4;base64,AAAA")


def test_specs_keep_only_values_their_quote_backs_up():
    from engine import specs
    out = specs.verify({"watts": 65, "volts": 20, "amps": 3.25, "connector": "USB-C", "protocols": ["USB PD", "PPS"],
                        "quotes": {"watts": "Output: 65W max", "volts": "5V/9V/15V/20V", "amps": "up to 5A",
                                   "connector": "USB-C port", "protocols": "supports USB PD 3.0"}})
    assert out["values"] == {"watts": 65, "volts": 20, "connector": "USB-C", "protocols": ["USB PD"]}
    assert specs.look_up("Anker", "")["found"] is False


def test_compare_picks_by_colour_never_by_price_alone():
    out = assist.compare([{"name": "Cheap", "overall": "amber", "price": 299},
                          {"name": "Genuine", "overall": "green", "price": 1399}])
    assert out["pick"] == "Genuine"
    assert assist.compare([{"name": "A", "overall": "red"}, {"name": "B", "overall": "amber"}])["pick"] is None
    assert assist.compare([{"name": "A", "overall": "unknown"}, {"name": "B", "overall": "unknown"}])["pick"] is None
    assert assist.compare([{"name": "A", "overall": "green"}])["pick"] is None


def test_consent_needs_the_shoppers_own_yes():
    for yes in ("Yes, send it", "ok", "हाँ भेज दो", "はい", "go ahead please"):
        assert assist.confirmed(yes), yes
    for no in ("What happens after?", "not now", "no", "yesterday it melted"):
        assert not assist.confirmed(no), no


def test_nothing_is_filed_without_a_yes(monkeypatch):
    from engine import incidents
    from engine.agents import owner_tools

    class Ctx:
        agent_name, state = "shelf_chat", {"pasted": "what would happen after?"}
    monkeypatch.setattr(incidents, "report", lambda *a: pytest.fail("filed without consent"))
    runtime.start(None)
    out = asyncio.run(owner_tools.file_incident_report(Ctx(), "It melted", brand="Kelvo"))
    assert out["error"].startswith("Not sent")
    Ctx.state = {"pasted": "Yes, send it", "owner": "OW-1", "market": "in"}
    monkeypatch.setattr(incidents, "report", lambda body, who: {"report_id": "IR-1", "who": who, **body})
    assert asyncio.run(owner_tools.file_incident_report(Ctx(), "It melted", brand="Kelvo"))["report_id"] == "IR-1"


def test_reminders_before_returns_and_warranties_end():
    rows = [{"id": "HI-1", "name": "charger", "owner_ref": "OW-1", "tenant_id": "public",
             "return_by": date(2026, 10, 21), "warranty_until": date(2026, 11, 17)},
            {"id": "HI-2", "name": "kettle", "return_by": date(2026, 10, 18)}]
    found = {(r["item_id"], r["kind"], r["days_left"]) for r in household.reminders(rows, date(2026, 10, 18))}
    assert found == {("HI-1", "return_ending", 3), ("HI-1", "warranty_ending", 30), ("HI-2", "return_ending", 0)}
    assert household.reminders(rows, date(2026, 10, 19)) == []


def test_memory_keeps_the_last_turns_and_the_facts():
    from engine import chat_memory
    m = {}
    for i in range(10):
        m = chat_memory.remember(m, f"q{i}", f"a{i}", product_id="SS-P-1" if i == 0 else None)
    assert len(m["history"]) == chat_memory.MAX_TURNS and m["history"][-1] == {"role": "assistant", "text": "a9"}
    assert m["product_id"] == "SS-P-1"
    assert chat_memory.load("SS-A-1", None) == {}  # no owner, no memory


def test_a_follow_up_uses_the_remembered_product_history_and_manual(monkeypatch):
    from engine import chat_memory
    saved = {}
    monkeypatch.setattr(chat_memory, "load", lambda sid, owner: {
        "product_id": "SS-P-10291", "history": [{"role": "user", "text": "is it safe?"}], "document": pdf_url(2)})
    monkeypatch.setattr(chat_memory, "save", lambda sid, owner, memory: saved.update(memory))
    seen = {}

    async def fake_chat(body, document=None):
        seen.update(body=body, document=document)
        return {"product_id": body["product_id"], "messages": [{"text": "Because of 6 reports."}]}
    monkeypatch.setattr(concierge, "_chat", fake_chat)
    out = asyncio.run(concierge.chat_session({"message": "why?", "_owner": "OW-1", "session_id": "SS-A-1"}))
    assert seen["body"]["product_id"] == "SS-P-10291" and seen["body"]["history"] and seen["document"]
    assert out["messages"][0]["text"] and saved["history"][-1]["text"] == "Because of 6 reports."
    # what the screen sends wins
    asyncio.run(concierge.chat_session({"message": "and this?", "product_id": "unmatched", "_owner": "OW-1",
                                        "session_id": "SS-A-1"}))
    assert seen["body"]["product_id"] == "unmatched"
