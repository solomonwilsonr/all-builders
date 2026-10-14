"""identity.resolve with a stand-in store: which URL matches count as a reference for checking a page."""
from engine import identity

FAKE = "https://example-deals-store.test/65w-charger"


def setup(monkeypatch, listings):
    monkeypatch.setattr(identity.store, "listing_by_url", lambda url: {"id": "SS-L-X", "product_id": "SS-P-X"})
    monkeypatch.setattr(identity.store, "product_listings", lambda pid: listings)
    monkeypatch.setattr(identity.store, "by_identifier", lambda fp: ["SS-P-GENUINE"])
    monkeypatch.setattr(identity.store, "latest_fingerprint", lambda pid: {"brand_norm": "kelvo"})


def test_a_page_known_only_from_itself_is_not_its_own_reference(monkeypatch):
    setup(monkeypatch, [{"url": FAKE, "marketplace": None}])
    listing = {"url": FAKE, "brand": "Kelvo", "model": "CX-65", "title": "Kelvo CX-65 Original"}
    assert identity.resolve(listing) == ("SS-P-X", "url")
    assert identity.resolve(listing, needs_reference=True) == ("SS-P-GENUINE", "model_number")


def test_catalog_and_demo_listings_still_match_by_url(monkeypatch):
    url = "https://demo.safeshelf.app/product/cx-65"
    setup(monkeypatch, [{"url": url, "marketplace": "demo"}])
    assert identity.resolve({"url": url, "title": "Kelvo CX-65"}, needs_reference=True) == ("SS-P-X", "url")
