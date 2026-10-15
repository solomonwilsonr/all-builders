"""JAPAC market from the shop's address or the price's currency."""
from engine import region


def test_market_from_the_shop_address():
    assert region.of("https://www.amazon.co.jp/dp/B0X") == "jp"
    assert region.of("https://www.amazon.com.au/dp/B0X") == "au"
    assert region.of("https://www.amazon.in/dp/B0CFFBZ23F") == "in"
    assert region.of("https://www.flipkart.com/x/p/itm1") == "in"
    assert region.of("https://shopee.sg/product/1") == "sg"
    assert region.of("https://www.lazada.com.my/products/x") == "my"
    assert region.of("https://www.mightyape.co.nz/product/x") == "nz"
    assert region.of("https://example-deals-store.test/x") is None
    assert region.of("https://www.linkedin.com/x") is None  # "in" must be a whole domain part


def test_market_from_currency_and_what_follows():
    assert region.of(None, "JPY") == "jp"
    assert region.recall_sources("jp")[0] == "jp_caa"
    assert region.recall_sources("au")[:2] == ["accc", "nz"]
    assert region.recall_sources(None) == region.DEFAULT_SOURCES
    assert region.currency("sg") == "SGD" and region.currency(None) == "INR"
