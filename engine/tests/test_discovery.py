"""Discovery: a first look at a product SafeShelf has never seen. No Google, no network, no database."""
import asyncio

import pytest
from fastapi import HTTPException

from engine.agents import discovery, runtime

FRIDGE = {"url": "https://www.amazon.in/dp/B0C1234567", "currency": "INR", "price": 79990, "seller": "DAWNTECH",
          "title": "Samsung 653 L, 3 Star, Convertible 5-in-1 Refrigerator (RS76CG8003S9HL, Silver)"}
REF = {"brand": "Samsung", "model": "RS76CG8003S9HL", "model_found": True, "currency": "INR", "evidence_id": "EV-REF1",
       "official_url": "https://www.samsung.com/in/refrigerators/side-by-side/rs76cg8003s9hl/", "brand_price": 79990.0,
       "energy_rating": "3 Star", "marks": ["BEE 3 Star"], "authorised_sellers": ["Samsung Shop", "Croma"], "notes": None}


def test_the_same_model_shares_one_key_whatever_the_listing():
    assert discovery.subject(FRIDGE) == ("Samsung", "RS76CG8003S9HL")
    assert discovery.model_key("Samsung", "RS76CG8003S9HL") == discovery.model_key("SAMSUNG", "rs-76cg8003s9hl")
    assert discovery.model_key("", "RS76CG8003S9HL") is None  # no brand, nothing to share it under


def test_only_the_brands_own_site_counts_as_official():
    assert discovery.on_brand_site("https://www.samsung.com/in/x", "Samsung")
    assert not discovery.on_brand_site("https://samsung-deals.example.com.evil.test/x", "LG")
    assert not discovery.on_brand_site(None, "Samsung")


def test_a_fair_price_is_said_and_changes_no_colour():
    lines, flag = discovery.compare(FRIDGE, REF)
    text = " | ".join(r["text"] for r in lines)
    assert not flag
    assert "brand's own site lists Samsung RS76CG8003S9HL (www.samsung.com)" in text
    assert "matches the brand's own price" in text
    lines, _ = discovery.compare({**FRIDGE, "price": 55990}, REF)
    assert any("30% below the brand's own price Rs 79,990 (a normal discount)" in r["text"] for r in lines)
    assert "registry itself was not checked" in text  # a web finding is never passed off as a registry check
    assert all(r["evidence_ids"] == ["EV-REF1"] for r in lines)


def test_less_than_half_the_brand_price_is_the_one_flag():
    _, flag = discovery.compare({**FRIDGE, "price": 29990}, REF)
    assert flag
    _, flag = discovery.compare({**FRIDGE, "price": 29990, "currency": "JPY"}, REF)
    assert not flag, "prices in different currencies are not compared"


def test_a_star_rating_that_differs_is_reported():
    lines, _ = discovery.compare({**FRIDGE, "title": FRIDGE["title"].replace("3 Star", "5 Star")}, REF)
    assert any("listing says 5 Star, but the brand states 3 Star" in r["text"] for r in lines)


def test_no_official_page_means_the_model_is_unconfirmed():
    lines, flag = discovery.compare(FRIDGE, {**REF, "model_found": False})
    assert not flag and "could not be confirmed" in lines[0]["text"] and len(lines) == 1


def _run(monkeypatch, saved=None, ref=REF, price=79990):
    """discover() with the pipeline, the web lookup and the database replaced."""
    stored = []
    monkeypatch.setattr(discovery.store, "latest_evidence", lambda kind, key, age: saved)
    monkeypatch.setattr(discovery.store, "add_evidence", lambda kind, key, content: stored.append((kind, key, content)) or "EV-NEW")
    monkeypatch.setattr(discovery, "reference_step", lambda brand, model, listing: ref)
    asked = {}

    async def fake_investigate(body):
        asked.update(body)
        return {"verdict": {"safe": "unknown", "real": "unknown", "overall": "unknown", "evidence_ids": [],
                            "reasons": [{"text": "Only 18 review(s) read", "evidence_ids": []}]},
                "research": None if saved else {"model": "RS76CG8003S9HL", "sources": [{"site": "CPSC", "status": "not_found", "matches": []}]},
                "messages": [{"role": "assistant", "text": "x", "evidence_ids": []}], "steps": []}

    monkeypatch.setattr(discovery.pipeline, "investigate", fake_investigate)
    runtime.start("SS-I-TEST")
    out = asyncio.run(discovery.discover({"mode": "discover", "listing": {**FRIDGE, "price": price}}))
    return out, asked, stored


def test_a_first_discovery_searches_everything_and_is_saved(monkeypatch):
    out, asked, stored = _run(monkeypatch)
    assert asked["recall_sites"] is True and asked["product_id"] == "unmatched"
    assert out["mode"] == "discover" and out["discovery"]["from_saved"] is False
    assert any("brand's own site" in r["text"] for r in out["verdict"]["reasons"])
    assert stored and stored[0][:2] == ("discovery", "samsung|RS76CG8003S9HL") and stored[0][2]["reference"] == REF


def test_the_next_shopper_reuses_the_saved_lookup(monkeypatch):
    saved = ("EV-OLD", {"reference": REF, "research": {"model": "RS76CG8003S9HL", "sources": [
        {"site": "ACCC", "status": "not_found", "matches": []}]}}, 3 * 3600)
    out, asked, stored = _run(monkeypatch, saved=saved)
    assert asked["recall_sites"] is False, "the recall sites were searched for this model 3 hours ago"
    assert out["discovery"]["from_saved"] and out["discovery"]["saved_minutes_ago"] == 180
    assert any("No recall notice for RS76CG8003S9HL on ACCC" in r["text"] for r in out["verdict"]["reasons"])
    assert not stored, "a reused lookup is not saved again"


def test_an_impossible_price_turns_is_it_real_amber(monkeypatch):
    out, _, _ = _run(monkeypatch, price=19990)
    assert out["verdict"]["real"] == "amber" and out["verdict"]["overall"] == "amber"


def test_recheck_needs_its_token(monkeypatch):
    monkeypatch.setattr(discovery, "RECHECK_TOKEN", "")
    with pytest.raises(HTTPException) as no_token:
        asyncio.run(discovery.recheck({"mode": "recheck"}))
    assert no_token.value.status_code == 503
    monkeypatch.setattr(discovery, "RECHECK_TOKEN", "s3cret")
    with pytest.raises(HTTPException) as wrong:
        asyncio.run(discovery.recheck({"mode": "recheck", "token": "guess"}))
    assert wrong.value.status_code == 403


def test_recheck_reports_only_new_notices(monkeypatch):
    monkeypatch.setattr(discovery, "RECHECK_TOKEN", "s3cret")
    old = {"brand": "Samsung", "model": "RS76CG8003S9HL", "market": "IN",
           "research": {"sources": [{"site": "CPSC", "matches": [{"url": "https://old", "covers_this_model": "maybe"}]}]}}
    monkeypatch.setattr(discovery.store, "evidence_refs", lambda kind, age: [("samsung|RS76CG8003S9HL", 25 * 3600), ("lg|GLI292", 2 * 3600)])
    monkeypatch.setattr(discovery.store, "latest_evidence", lambda kind, key, age: ("EV-OLD", old, 25 * 3600))
    saved = []
    monkeypatch.setattr(discovery.store, "add_evidence", lambda kind, key, content: saved.append(key) or "EV-NEW")
    monkeypatch.setattr(discovery.research, "check", lambda brand, model, kind, sources: {"sources": [{"site": "CPSC", "status": "found", "matches": [
        {"url": "https://old", "covers_this_model": "maybe"}, {"url": "https://new", "title": "Fridge recall", "covers_this_model": "yes", "evidence_id": "EV-N"}]}]})
    runtime.start("SS-I-TEST2")
    out = asyncio.run(discovery.recheck({"mode": "recheck", "token": "s3cret"}))
    assert out["rechecked"] == ["samsung|RS76CG8003S9HL"], "checked 2 hours ago: not due yet"
    assert [a["url"] for a in out["new_possible_recalls"]] == ["https://new"]
    assert saved == ["samsung|RS76CG8003S9HL"]
