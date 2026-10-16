"""Plan v2.2 workstreams D-I without a database: hazard discovery, cross-border filters, watch alerts, case
lifecycle rules, webhook signatures, tenancy helpers, title parsing, camera scrubbing."""
import hashlib
import hmac

import pytest

from engine import camera, cases, crossborder, hazard_discovery, investigation, tenancy, watch, webhooks


# --- hazard discovery ---------------------------------------------------------------------------------------------

def test_wilson_interval_and_anomaly():
    low, high = hazard_discovery.wilson(2, 20)
    assert 0 < low < 0.1 < high < 0.4
    assert hazard_discovery.anomaly(1, 10, 5)["status"] == "too_few_reviews"
    assert hazard_discovery.anomaly(1, 400, 5)["status"] == "within_baseline"
    hot = hazard_discovery.anomaly(12, 100, 5)
    assert hot["status"] == "investigation_candidate" and "not per unit sold" in hot["note"]


def test_integrity_flags_copies_photos_and_bursts():
    reviews = [{"id": str(i), "text": "It melted!" if i < 3 else f"review {i}", "date": "2026-01-0" + str(1 + i % 2)}
               for i in range(6)]
    out = hazard_discovery.integrity(reviews, {"1": ["h"], "4": ["h"]})
    assert set(out["flags"]) == {"copied_text", "recycled_photos", "burst"}
    assert "never delete" in out["note"]


def test_hypotheses_stay_hypotheses():
    found = hazard_discovery.hypotheses([{"hazard_type": "fire_burn"}],
                                        ["It overheated while charging", "used a third-party cable"])
    assert found and all(h["status"] == "hypothesis" and h["verification_test"] for h in found)
    assert hazard_discovery.hypotheses([], []) == []


# --- cross-border ---------------------------------------------------------------------------------------------------

def test_generic_words_are_not_model_numbers():
    row = {"id": "x", "title": "5-drawer chest", "scope_json": {"Products": [{"Name": "5-drawer", "Model": "5-drawer"}],
                                                                "Description": "model number 2-burner"}}
    assert crossborder.notice_models(row, {}) == set()
    real = {"id": "y", "title": "Baseus power bank", "scope_json": {"Description": "model number BS-30KP365"}}
    assert crossborder.notice_models(real, {}) == {"BS30KP365"}


def test_same_brand_across_corporate_names():
    a = {"title": "Chervon North America Recalls EGO Power+ Blowers",
         "scope_json": {"Manufacturers": [{"Name": "Chervon North America"}]}}
    b = {"title": "Chervon Australia Pty Ltd - EGO Power+ blower", "scope_json": {}}
    c = {"title": "Kmart Australia - generic blower", "scope_json": {}}
    for row in (a, b, c):
        row["brand_words"] = crossborder.brand_words(row)
    assert crossborder.same_brand(a, b) and not crossborder.same_brand(a, c)


# --- watchlist alerts ------------------------------------------------------------------------------------------------

def test_alerts_only_when_the_outcome_changes():
    answer = {"outcome": "potential_concern", "headline": "h", "contradictions": []}
    assert watch.alert_for(None, answer)["kind"] == "new_concern"
    assert watch.alert_for("potential_concern", answer) is None
    worse = {**answer, "outcome": "confirmed_recall"}
    assert watch.alert_for("potential_concern", worse)["kind"] == "worsened"
    withdrawn = {"outcome": "no_matching_notice_found", "contradictions": [{"kind": "retraction"}]}
    assert watch.alert_for("confirmed_recall", withdrawn)["kind"] == "retraction"
    assert watch.alert_for("confirmed_recall", {"outcome": "no_matching_notice_found"})["kind"] == "correction"


# --- case lifecycle ---------------------------------------------------------------------------------------------------

def test_lifecycle_rules():
    assert "investigating" in cases.TRANSITIONS["triage"]
    assert "resolved" not in cases.TRANSITIONS["candidate"]
    assert all("reopened" in cases.TRANSITIONS[s] for s in ("substantiated", "unsubstantiated", "resolved"))
    assert "notify_owners" in cases.NEEDS_SUBSTANTIATED


# --- webhooks and tenancy -------------------------------------------------------------------------------------------

def test_webhook_signature(monkeypatch):
    monkeypatch.setenv("SAFESHELF_WEBHOOK_KEY", "server-key")
    secret = webhooks.secret_for("WH-1")
    assert secret == webhooks.secret_for("WH-1") != webhooks.secret_for("WH-2")
    sig = webhooks.sign(secret, "1700000000", b'{"a":1}')
    expected = hmac.new(secret.encode(), b'1700000000.{"a":1}', hashlib.sha256).hexdigest()
    assert sig == "sha256=" + expected


def test_webhooks_refuse_internal_addresses(monkeypatch):
    monkeypatch.setenv("SAFESHELF_WEBHOOK_KEY", "k")
    with pytest.raises(ValueError):
        webhooks.create("TN-1", "https://127.0.0.1/hook", ["watchlist.alert"])
    with pytest.raises(ValueError):
        webhooks.create("TN-1", "http://partner.example/hook", ["watchlist.alert"])


def test_webhooks_need_a_server_key(monkeypatch):
    monkeypatch.delenv("SAFESHELF_WEBHOOK_KEY", raising=False)
    with pytest.raises(RuntimeError):
        webhooks.secret_for("WH-1")


def test_tenancy_helpers(monkeypatch):
    assert tenancy.owner_hash("uid-1") == tenancy.owner_hash("uid-1") != tenancy.owner_hash("uid-2")
    assert "uid-1" not in tenancy.owner_hash("uid-1")
    public = tenancy.caller({})
    assert public.tenant_id == "public" and public.scopes == ["consumer"]
    with pytest.raises(PermissionError):
        tenancy.require(public, "reviewer")
    monkeypatch.setenv("API_KEY", "internal-key")
    internal = tenancy.caller({"x-api-key": "internal-key"})
    assert internal.is_admin and internal.tenant_id == "internal"


# --- identity from listings, camera --------------------------------------------------------------------------------

@pytest.mark.parametrize("title,model", [
    ("HAIARA モバイルバッテリー W5PRO 10000mAh", "W5PRO"),
    ("NEWDERY Power Bank 10000mAh ZHX-PB22", "ZHX-PB22"),
    ("Samsung 653 L Convertible 5-in-1 RS76CG8003S9HL", "RS76CG8003S9HL"),
    ("New 65W Fast Charger USB-C", None),
])
def test_title_model_keeps_the_written_form(title, model):
    assert investigation.title_model({"title": title}) == model


def test_camera_scrubs_contact_details():
    assert camera.scrub("Call +91 98765 43210 or mail a@b.co") == "Call [removed] or mail [removed]"
    with pytest.raises(ValueError):
        camera.decode("not a data url")
