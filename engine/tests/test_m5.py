from engine import marks, recalls, store
from engine.normalize import normalise

TV = {**normalise({"brand": "ViewMax", "model": "VM-55U8", "category": "television"}), "category": "television"}
CHARGER = normalise({"brand": "Kelvo", "model": "CX-65", "category": "usb_charger"})


class FakeConn:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *args):
        return self

    def fetchall(self):
        return self.rows


def registry(monkeypatch, rows):
    monkeypatch.setattr(store, "conn", lambda: FakeConn(rows))


def record(**kw):
    return {"registration_number": "ATV-DEMO-0001", "brand": "ViewMax", "model": "VM-55U8", "star_rating": 3.0,
            "status": "Approved", "raw": {}, **kw}


def test_claims_read_stars_and_numbers_without_gemini():
    found = marks.claims({"title": "ViewMax 55-inch TV, 5-Star Energy Rating", "label_text": "Reg ATV5188"},
                         use_gemini=False)
    assert found == [{"authority": marks.AU, "number": "ATV5188", "claimed_value": "5 stars"}]
    bis = marks.claims({"brand": "Kelvo", "label_text": "Output 65W | R-41097318"}, use_gemini=False)
    assert bis == [{"authority": marks.BIS, "number": "R-41097318", "claimed_value": "Kelvo"}]


def test_more_stars_than_registered_is_a_star_rating_mismatch(monkeypatch):
    registry(monkeypatch, [record()])
    result = marks.check({"authority": marks.AU, "claimed_value": "5 stars"}, TV)
    assert (result["result"], result["field"], result["registry_value"]) == ("mismatch", "star_rating", "3 stars")


def test_matching_stars_verify_and_other_brands_mismatch(monkeypatch):
    registry(monkeypatch, [record()])
    assert marks.check({"authority": marks.AU, "claimed_value": "3 stars"}, TV)["result"] == "verified"
    registry(monkeypatch, [record(brand="OtherCo")])
    assert marks.check({"authority": marks.AU, "number": "ATV-DEMO-0001"}, TV)["field"] == "brand"


def test_unknown_when_registry_cannot_answer(monkeypatch):
    registry(monkeypatch, [])
    assert marks.check({"authority": marks.AU, "claimed_value": "5 stars"}, TV)["result"] == "unknown"
    assert "appliances only" in marks.check({"authority": marks.AU, "claimed_value": "5 stars"}, CHARGER)["reason"]
    assert marks.check({"authority": marks.BIS, "number": "R-12345678"}, CHARGER)["result"] == "unknown"


def test_bis_mock_verifies_the_right_brand_only():
    assert marks.check({"authority": marks.BIS, "number": "R-41097318"}, CHARGER)["result"] == "verified"
    other = normalise({"brand": "VoltNova", "model": "VN-65PD", "category": "usb_charger"})
    assert marks.check({"authority": marks.BIS, "number": "R-41097318"}, other)["field"] == "brand"


def test_recall_needs_the_exact_model_number():
    notice = {"id": "cpsc:1", "title": "Anker Recalls Power Banks", "scope_json": {"Products": [{"Model": "A1366"}]}}
    anker = normalise({"brand": "Anker", "model": "A1366", "category": "power_bank"})
    other = normalise({"brand": "Anker", "model": "A1289", "category": "power_bank"})
    assert recalls.classify(anker, notice) == "exact_model"
    assert recalls.classify(other, notice) is None


def test_family_named_without_models_goes_to_review(monkeypatch):
    notice = {"id": "cpsc:2", "title": "VRURC Portable Chargers Recalled", "scope_json": {"Products": [{"Model": ""}]}}
    monkeypatch.setattr(recalls, "notice_models", lambda recall: set())
    vrurc = normalise({"brand": "VRURC", "model": "T1159", "category": "portable_charger"})
    assert recalls.classify(vrurc, notice) == "needs_review"
