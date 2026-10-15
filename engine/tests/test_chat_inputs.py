"""Shelf Chat without the shop's page (engine/agents): a name shared with the link, the name in the link, a screenshot.
No Google calls, no database."""
import asyncio
import base64

import pytest
from fastapi import HTTPException

from engine.agents import cache, concierge, links, pipeline, runtime, screenshot

LINK = ("https://www.amazon.in/Lifelong-Protein-Leakproof-Protein-LLSHB04/dp/B0CFFBZ23F/?_encoding=UTF8"
        "&pd_rd_w=Bdg8u&ref_=pd_hp_d_r_btf_dealz_mv&th=1")
PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()


def test_the_name_an_app_shares_with_the_link_is_used():
    shared = "Check out this deal on Amazon!\nLifelong Protein Shaker Bottle LLSHB04 (700 ml)\nhttps://amzn.in/d/abc"
    assert links.shared_name(shared) == "Lifelong Protein Shaker Bottle LLSHB04 (700 ml)"
    assert links.shared_name("Kelvo CX-65 65W Charger : Amazon.in: Electronics https://amzn.in/d/x") == \
        "Kelvo CX-65 65W Charger"


def test_a_question_next_to_the_link_is_not_a_product_name():
    assert links.shared_name("is this safe? " + LINK) is None
    assert links.shared_name("Is it real " + LINK) is None
    assert links.shared_name("क्या यह सुरक्षित है " + LINK) is None
    assert links.shared_name(LINK) is None


def test_the_name_in_the_link_itself():
    assert links.name_from_url(LINK) == "Lifelong Protein Leakproof Protein LLSHB04"
    assert links.name_from_url("https://www.flipkart.com/lifelong-shaker-700-ml/p/itm123abc") == \
        "lifelong shaker 700 ml"
    assert links.name_from_url("https://amzn.in/d/abc") is None
    assert links.name_from_url("https://www.amazon.in/dp/B0CFFBZ23F") is None


class Ctx:
    agent_name = "shelf_chat"

    def __init__(self, **state):
        self.state = state


def unread(monkeypatch) -> dict:
    """The shop blocks the server; the investigation records the listing it was given."""
    asked = {}
    monkeypatch.setattr(cache, "get", lambda key: None)
    monkeypatch.setattr(cache, "put", lambda *a: None)
    monkeypatch.setattr(links, "read", lambda url: {"url": links.clean(url), "read": "none"})

    async def investigate(body):
        asked.update(body)
        return {"product_id": None, "verdict": {"overall": "unknown"}, "messages": [{"text": "Not enough evidence."}]}
    monkeypatch.setattr(pipeline, "investigate", investigate)
    runtime.start(None)
    return asked


def test_an_unreadable_link_is_checked_by_the_shared_name(monkeypatch):
    asked = unread(monkeypatch)
    pasted = "Lifelong Protein Shaker Bottle LLSHB04\nhttps://amzn.in/d/abc"
    out = asyncio.run(concierge.check_link("https://amzn.in/d/abc", Ctx(pasted=pasted)))
    assert asked["listing"]["title"] == "Lifelong Protein Shaker Bottle LLSHB04"
    assert "name in the shopper's message" in out["note"]


def test_an_unreadable_link_falls_back_to_the_name_in_the_link(monkeypatch):
    asked = unread(monkeypatch)
    out = asyncio.run(concierge.check_link(LINK, Ctx(pasted="is this safe? " + LINK)))
    assert asked["listing"] == {"url": "https://www.amazon.in/dp/B0CFFBZ23F",
                                "title": "Lifelong Protein Leakproof Protein LLSHB04"}
    assert "name in the link itself" in out["note"] and "screenshot" in out["note"]


def test_a_link_with_no_name_anywhere_asks_for_more(monkeypatch):
    asked = unread(monkeypatch)
    out = asyncio.run(concierge.check_link("https://amzn.in/d/abc", Ctx(pasted="https://amzn.in/d/abc")))
    assert "title" not in asked["listing"] and "brand and model number" in out["note"]


def test_images_must_be_small_data_urls():
    assert screenshot.decode(PNG) == (b"\x89PNG fake", "image/png")
    for bad in ("https://example.com/a.png", "data:text/html;base64,PGI+", "data:image/png;base64,***"):
        with pytest.raises(screenshot.BadImage):
            screenshot.decode(bad)
    with pytest.raises(screenshot.BadImage):
        screenshot.decode("data:image/png;base64," + base64.b64encode(b"x" * (screenshot.MAX_BYTES + 1)).decode())


PAGE = {"kind": "product_page", "shop": "amazon.in", "title": "Lifelong Protein Shaker LLSHB04", "brand": "Lifelong",
        "model_number": "LLSHB04", "model": "gemini-3-flash-preview", "price": 299, "mrp": 999, "seller": "RetailEZ", "rating": 3.9, "ratings_count": 19,
        "reviews": [{"rating": 1, "title": "Leaks", "text": "Leaks from the lid"}, {"rating": 5, "text": ""}],
        "safety_marks": ["BIS R-41012345"]}


def test_a_screenshot_becomes_a_listing():
    listing = screenshot.to_listing(PAGE)
    assert listing["title"] == "Lifelong Protein Shaker LLSHB04" and listing["currency"] == "INR"
    assert listing["reviews"] == [{"rating": 1, "title": "Leaks", "text": "Leaks from the lid"}]
    assert "Model: LLSHB04" in listing["page_text"] and "gemini" not in listing["page_text"]
    assert "M.R.P.: 999" in listing["page_text"] and "BIS R-41012345" in listing["page_text"]
    assert screenshot.label_observations(PAGE) == [{"kind": "label", "text": "BIS R-41012345"}]
    assert screenshot.to_listing({"kind": "other", "title": "A cat"}) == {}
    assert screenshot.to_listing({"kind": "product_page"}) == {}


def test_chat_checks_the_listing_in_a_screenshot(monkeypatch):
    asked, seen = {}, {}
    monkeypatch.setattr(screenshot, "read", lambda data, mime: PAGE)

    async def investigate(body):
        asked.update(body)
        return {"product_id": None, "verdict": {"overall": "amber"}, "investigation_id": "SS-I-1",
                "messages": [{"text": "One buyer reports leaks."}]}

    async def fake_run(build, prompt, state=None, timeout_s=45):
        seen["prompt"] = prompt
        return "It leaks, says one buyer.", {}
    monkeypatch.setattr(pipeline, "investigate", investigate)
    monkeypatch.setattr(concierge.runtime, "run", fake_run)
    runtime.start(None)
    out = asyncio.run(concierge.chat_session({"product_id": "unmatched", "image": PNG}))
    assert asked["listing"]["brand"] == "Lifelong"
    assert asked["page_evidence"] == {"source": "screenshot", "observations": [{"kind": "label", "text": "BIS R-41012345"}]}
    assert "The shopper sent an image" in seen["prompt"] and "One buyer reports leaks." in seen["prompt"]
    assert out["link"]["page_read"] == "screenshot" and out["link"]["reviews_on_page"] == 1
    assert out["steps"][0]["tool"] == "read_image"


def test_a_bad_image_is_refused(monkeypatch):
    runtime.start(None)
    with pytest.raises(HTTPException) as refused:
        asyncio.run(concierge.chat_session({"product_id": "unmatched", "image": "data:image/gif;base64,R0lG"}))
    assert refused.value.status_code == 422


def test_no_brand_means_recalls_were_not_searched():
    verdict = pipeline.decide({"safety_radar": {"verdict": "not_enough_evidence", "reviews_checked": 0,
                                                "official_status": {"recalled": False, "searched": False,
                                                                    "checked": ["CPSC"]}}})
    texts = [r["text"] for r in verdict["reasons"]]
    assert "Recall notices could not be searched: no brand or model number to search for" in texts
    assert not any("No official recall found" in t for t in texts)
