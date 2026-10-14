"""Evidence lookup: plain-words source and the exact quote, with a stand-in store."""
import json
from datetime import UTC, datetime

from engine import evidence

NOW = datetime(2026, 10, 14, tzinfo=UTC)


def row(id_, kind, ref, content, observed=None):
    return {"id": id_, "source_type": kind, "source_ref": ref, "content": json.dumps(content),
            "observed_at": observed, "captured_at": NOW}


def test_page_review_keeps_exact_text_and_links_the_page(monkeypatch):
    r = row("EV-1", "review", "listing:https://www.amazon.in/dp/B0X:3c2e", {"text": "Port melted.", "rating": 1.0,
                                                                            "date": "2026-09-02"})
    e = evidence.describe(r)
    assert e == {"evidence_id": "EV-1", "type": "review", "source": "Customer review on amazon.in",
                 "url": "https://www.amazon.in/dp/B0X", "quote": "Port melted.", "rating": 1, "date": "2026-09-02"}


def test_catalog_review_names_the_marketplace(monkeypatch):
    monkeypatch.setattr(evidence.store, "product_listings",
                        lambda pid: [{"marketplace": "demo", "url": "https://demo.safeshelf.app/product/cx-65"}])
    e = evidence.describe(row("EV-2", "review", "SS-P-10291:demo-08", {"text": "Smoke came out.", "rating": 1}))
    assert e["source"] == "Customer review on the demo shop" and e["quote"] == "Smoke came out."


def test_check_and_photo_rows():
    trust = evidence.describe(row("EV-3", "trust_check", "https://shop.test/x", {"summary": "Be careful: price."}))
    assert (trust["type"], trust["quote"], trust["url"]) == ("check", "Be careful: price.", "https://shop.test/x")
    photo = evidence.describe(row("EV-4", "photo_check", "https://img.test/1.jpg", {"description": "Melted casing"}))
    assert photo["type"] == "review_photo" and photo["quote"] == "Melted casing"


def test_lookup_keeps_order_and_drops_unknown_ids(monkeypatch):
    rows = [row("EV-B", "trust_check", "", {"summary": "b"}), row("EV-A", "trust_check", "", {"summary": "a"})]

    class Conn:
        def execute(self, sql, args):
            return type("R", (), {"fetchall": lambda self: rows})()

    monkeypatch.setattr(evidence.store, "conn", lambda: Conn())
    assert [e["evidence_id"] for e in evidence.lookup("EV-A, EV-X,EV-B")] == ["EV-A", "EV-B"]
    assert evidence.lookup(" , ") == []
