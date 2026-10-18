"""identity.resolve with a stand-in store: which URL matches count as a reference for checking a page."""
from engine import identity

FAKE = "https://example-deals-store.test/65w-charger"


def setup(monkeypatch, listings, stored=None):
    monkeypatch.setattr(identity.store, "listing_by_url", lambda url: {"id": "SS-L-X", "product_id": "SS-P-X"})
    monkeypatch.setattr(identity.store, "product_listings", lambda pid: listings)
    monkeypatch.setattr(identity.store, "by_identifier", lambda fp: ["SS-P-GENUINE"])
    fingerprint = {"brand_norm": "kelvo", "model_norm": "CX65"}
    monkeypatch.setattr(identity.store, "latest_fingerprint",
                        lambda pid: fingerprint if pid == "SS-P-GENUINE" else (stored or fingerprint))


def test_a_page_known_only_from_itself_is_not_its_own_reference(monkeypatch):
    setup(monkeypatch, [{"url": FAKE, "marketplace": None}])
    listing = {"url": FAKE, "brand": "Kelvo", "model": "CX-65", "title": "Kelvo CX-65 Original"}
    assert identity.resolve(listing) == ("SS-P-X", "url")
    assert identity.resolve(listing, needs_reference=True) == ("SS-P-GENUINE", "model_number")


def test_catalog_and_demo_listings_still_match_by_url(monkeypatch):
    url = "https://demo.safeshelf.app/product/cx-65"
    setup(monkeypatch, [{"url": url, "marketplace": "demo"}])
    assert identity.resolve({"url": url, "title": "Kelvo CX-65"}, needs_reference=True) == ("SS-P-X", "url")


def test_an_empty_product_known_by_url_is_no_reference(monkeypatch):
    # 18 Oct: the fake shop's URL had become a product with no brand or model and a second, blank listing.
    setup(monkeypatch, [{"url": FAKE, "marketplace": None}, {"url": "https://www.amazon.in/dp/B0XYZ12345",
                                                            "marketplace": None}], stored={"brand_norm": ""})
    listing = {"url": FAKE, "title": "65W Super Fast Charger - Kelvo CX-65 Original", "page_text": "Model CX-65"}
    assert identity.resolve(listing, needs_reference=True) == ("SS-P-GENUINE", "model_number")


def test_a_look_alike_with_another_model_or_capacity_is_no_match(monkeypatch):
    # 18 Oct: "HAIARA W5PRO 10000mAh" landed on a provisional "HAIARA W5" (5000 mAh).
    w5 = {"brand_norm": "haiara", "model_norm": "W5", "attributes": {"capacity_mah": 5000}}
    monkeypatch.setattr(identity.store, "listing_by_url", lambda url: None)
    monkeypatch.setattr(identity.store, "by_identifier", lambda fp: [])
    monkeypatch.setattr(identity.store, "latest_fingerprint", lambda pid: w5)
    monkeypatch.setattr(identity.store, "brands_in", lambda title: ["haiara"])
    monkeypatch.setattr(identity.store, "nearest", lambda vector, distance, brand="": "SS-P-W5")
    monkeypatch.setattr(identity.gemini, "embed", lambda texts: [[0.0]])
    listing = {"url": "https://www.amazon.co.jp/dp/SAFESHELF-W5PRO", "title": "HAIARA モバイルバッテリー W5PRO 10000mAh"}
    assert identity.resolve(listing, needs_reference=True) == (None, "none")
    w5["model_norm"] = ""  # no model on file: the capacity alone tells them apart
    assert identity.resolve(listing, needs_reference=True) == (None, "none")


def test_a_url_filed_under_another_model_is_no_match(monkeypatch):
    # 18 Oct: the W5PRO demo URL itself had been attached to the HAIARA W5 (5000 mAh) before the look-alike check.
    w5 = {"brand_norm": "haiara", "model_norm": "W5", "attributes": {"capacity_mah": 5000}}
    url = "https://www.amazon.co.jp/dp/SAFESHELF-W5PRO"
    monkeypatch.setattr(identity.store, "listing_by_url", lambda u: {"id": "SS-L-FB8D9FB5", "product_id": "SS-P-W5"})
    monkeypatch.setattr(identity.store, "product_listings", lambda pid: [{"url": url, "marketplace": "amazon.com"}])
    monkeypatch.setattr(identity.store, "by_identifier", lambda fp: [])
    monkeypatch.setattr(identity.store, "latest_fingerprint", lambda pid: w5)
    monkeypatch.setattr(identity.store, "brands_in", lambda title: ["haiara"])
    monkeypatch.setattr(identity.store, "nearest", lambda vector, distance, brand="": "SS-P-W5")
    monkeypatch.setattr(identity.gemini, "embed", lambda texts: [[0.0]])
    listing = {"url": url, "title": "HAIARA モバイルバッテリー W5PRO 10000mAh"}
    assert identity.resolve(listing, needs_reference=True) == (None, "none")
