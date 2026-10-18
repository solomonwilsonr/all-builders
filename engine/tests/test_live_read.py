"""The page reader behind the judges' page browser (links.read_live): schema.org product data, "page not found"
pages, and the real-browser fallback. No network: fetches are replaced."""
from engine.agents import links

LD_PAGE = """<html><head><title>Anker 10000 mAh Power Bank Price in India</title>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Anker 10000 mAh Power Bank",
"image":["https://img.example/anker.jpg"],"brand":{"@type":"Brand","name":"Anker"},
"offers":{"@type":"Offer","price":"3399","priceCurrency":"INR","seller":{"@type":"Organization","name":"RetailNet"}},
"review":[{"@type":"Review","name":"Gets hot","reviewBody":"Port gets very hot while charging","reviewRating":{"ratingValue":"2"}}]}</script>
</head><body>Anker 10000 mAh</body></html>"""


def test_schema_org_product_fills_price_photos_reviews_and_seller():
    listing = links.listing_from_html("https://www.flipkart.com/anker/p/itm1", LD_PAGE)
    assert listing["price"] == 3399 and listing["currency"] == "INR"
    assert listing["image_urls"] == ["https://img.example/anker.jpg"]
    assert listing["seller"] == "RetailNet" and listing["brand"] == "Anker"
    assert listing["reviews"][0]["text"] == "Port gets very hot while charging" and listing["reviews"][0]["rating"] == 2


def test_a_page_not_found_is_not_a_product():
    listing = links.listing_from_html("https://www.amazon.in/dp/B000000000", "<html><head><title>Page Not Found</title></head><body>Sorry</body></html>")
    assert listing == {"url": "https://www.amazon.in/dp/B000000000"}


def test_full_direct_read_never_uses_the_browser(monkeypatch):
    monkeypatch.setattr(links, "fetch", lambda url: (url, LD_PAGE))
    called = []
    monkeypatch.setattr(links, "rendered_html", lambda url: called.append(url))
    r = links.read_live("https://www.flipkart.com/anker/p/itm1")
    assert r["read"] == "full" and r["via"] == "direct" and not called


def test_thin_direct_read_falls_back_to_the_browser(monkeypatch):
    monkeypatch.setattr(links, "fetch", lambda url: (url, "<html><head><title>Anker Power Bank</title></head><body></body></html>"))
    monkeypatch.setattr(links, "rendered_html", lambda url: LD_PAGE)
    r = links.read_live("https://www.amazon.in/dp/B0F991GD2F")
    assert r["via"] == "browser" and r["read"] == "full" and r["price"] == 3399


def test_without_a_firecrawl_key_the_direct_read_is_kept(monkeypatch):
    monkeypatch.setattr(links, "fetch", lambda url: (url, "<html><head><title>Anker Power Bank</title></head><body></body></html>"))
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
    r = links.read_live("https://www.amazon.in/dp/B0F991GD2F")
    assert r["via"] == "direct" and r["read"] == "partial" and r["title"] == "Anker Power Bank"
