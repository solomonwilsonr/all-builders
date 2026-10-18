"""The extension's listing checks as chat tools (engine/agents/listing_tools.py): no Google calls, no database."""
import asyncio
from types import SimpleNamespace

from engine.agents import cache, links, listing_tools, runtime

URL = "https://www.amazon.in/dp/B0TEST1234"
PAGE = {"url": URL, "title": "Ambrane 20000mAh Power Bank", "price": 899, "currency": "INR", "seller": "Shop X",
        "reviews": [{"rating": 1, "text": "Got hot"}], "read": "full", "via": "direct"}


def ctx(**state):
    return SimpleNamespace(agent_name="shelf_chat", state=state)


def run(coro):
    runtime.start()
    return asyncio.run(coro)


def test_checks_read_the_link_this_chat_is_about(monkeypatch):
    cache.clear()
    cache.put("link:" + links.clean(URL), PAGE, 600)
    seen = {}
    monkeypatch.setattr(listing_tools.official_seller, "assess", lambda listing: seen.update(listing) or {"ok": 1})
    out = run(listing_tools.check_official_seller(ctx(link_url=URL)))
    assert out == {"ok": 1}
    assert seen["title"] == PAGE["title"] and seen["seller"] == "Shop X"
    assert "read" not in seen and "via" not in seen  # how the page was read is not part of the listing


def test_a_link_read_this_turn_wins_and_a_hidden_page_keeps_its_name(monkeypatch):
    cache.clear()
    monkeypatch.setattr(listing_tools.links, "read", lambda url: {"url": url, "read": "none"})
    monkeypatch.setattr(listing_tools.listing_age, "assess", lambda listing: listing)

    async def go():
        runtime.start().results["checkLink"] = {"url": URL, "title": "Named in the message"}
        return await listing_tools.check_listing_age(ctx(link_url="https://elsewhere.example/p"))
    out = asyncio.run(go())
    assert out["url"] == URL and out["title"] == "Named in the message"


def test_no_link_asks_for_one():
    cache.clear()
    out = run(listing_tools.check_reviews(ctx()))
    assert out == {"error": listing_tools.NO_PAGE}


def test_a_blocked_link_is_an_answer_not_a_crash(monkeypatch):
    cache.clear()

    def blocked(url):
        raise links.BlockedLink("it points inside a private network")
    monkeypatch.setattr(listing_tools.links, "read", blocked)
    out = run(listing_tools.compare_price(ctx(), url="http://10.0.0.1/x"))
    assert out["error"].startswith("SafeShelf can't open that link")
