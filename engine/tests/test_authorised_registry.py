"""The registry of who may sell each brand (data/authorised_sellers.json) and the matcher that reads it."""
import json
from pathlib import Path

import pytest

from engine import trust
from engine.normalize import norm_brand

REGISTRY = json.loads((Path(__file__).resolve().parents[2] / "data" / "authorised_sellers.json").read_text())
DEMO = {"kelvo", "voltnova", "viewmax"}
REAL = {k: v for k, v in REGISTRY["brands"].items() if k not in DEMO}
AMAZON, FLIPKART = "https://www.amazon.in/dp/B0X", "https://www.flipkart.com/p/itm1"


@pytest.mark.parametrize("brand", sorted(REAL))
def test_every_real_brand_cites_the_brands_own_page(brand):
    """Nothing is added from memory, news posts or forums: a source page and a date are required."""
    entry = REAL[brand]
    assert entry["source"] and entry["source_url"].startswith("https://")
    assert entry.get("as_of") or entry.get("retrieved"), "the date the page was published or read"
    assert entry.get("sellers") or entry.get("marketplaces") or entry.get("official_channels") or entry.get("domains"), \
        "it names sellers, channels or at least its own websites"
    if entry.get("list_kind") == "own_store":
        assert entry["domains"] and not entry.get("sellers") and not entry.get("marketplaces"), "own-store entries name no sellers"


@pytest.mark.parametrize("brand", sorted(REAL))
def test_registry_entries_are_well_formed(brand):
    entry = REAL[brand]
    assert brand == norm_brand(brand)
    assert all(a == norm_brand(a) for a in entry.get("aliases", [])), "aliases are written the way norm_brand writes them"
    for shop, listing in entry.get("marketplaces", {}).items():
        assert shop == trust.registrable(shop), f"{shop} is not a registrable domain"
        assert listing["sellers"] and all(isinstance(n, str) and n.strip() for n in listing["sellers"])
    for channel in entry.get("official_channels", []):
        assert channel == channel.lower() and "/" not in channel and "." in channel, channel
    assert entry.get("list_kind", "sellers") in ("sellers", "channels", "own_store")


def test_brand_names_find_their_entry_through_aliases():
    for name in ("boAt", "boAt Lifestyle", "Imagine Marketing"):
        assert trust.brand_entry(name)["source_url"].endswith("/pages/warranty"), name
    for name in ("Nothing", "CMF", "CMF by Nothing"):
        assert trust.brand_entry(name)["official_channels"] == ["flipkart.com", "myntra.com"], name
    assert trust.brand_entry("Redmi") == trust.brand_entry("Xiaomi") != {}
    assert trust.brand_entry("Some Unknown Brand") == {}


def test_boat_is_held_to_each_shops_own_list():
    """boAt's page lists Amazon's sellers apart from Flipkart's, so a seller is judged on the shop it sells on."""
    assert trust.authorised("boAt", "Appario Retail", AMAZON)
    assert trust.authorised("boAt", "Wave Tone", AMAZON) and not trust.authorised("boAt", "Wave Tone", FLIPKART)
    assert trust.authorised("boAt", "Dee Horizon", FLIPKART) and not trust.authorised("boAt", "Dee Horizon", AMAZON)
    assert trust.authorised("boAt", "Techretailer", AMAZON) and trust.authorised("boAt", "Techvast Pvt. Ltd.", FLIPKART)
    assert trust.authorised("boAt", "Appario Retail Private Ltd", AMAZON)          # the full company name on the shop
    assert not trust.authorised("boAt", "Random Traders", AMAZON)
    assert not trust.authorised("boAt", "Appario Retail", "https://www.meesho.com/p/1")   # a shop the brand names no list for
    assert not trust.authorised("boAt", "Appario Retail", None) and not trust.authorised("boAt", None, AMAZON)


def test_a_brands_own_website_is_always_authorised():
    assert trust.authorised("boAt", None, "https://www.boat-lifestyle.com/products/x")
    assert trust.authorised("CMF", None, "https://in.nothing.tech/products/cmf-phone-2-pro")


def test_a_brand_that_names_channels_not_sellers_has_no_authorised_seller_on_a_marketplace():
    assert not trust.authorised("Nothing", "Any Seller", AMAZON) and not trust.authorised("CMF", "Any Seller", FLIPKART)
    assert "amazon.in" not in trust.brand_entry("CMF")["official_channels"]     # the brand's statement leaves Amazon out


def test_brands_with_one_flat_list_still_work_everywhere():
    assert trust.authorised("Samsung", "Clicktech Retail Private Ltd", AMAZON)
    assert trust.authorised("Samsung", "Clicktech Retail", FLIPKART)
    assert not trust.authorised("Samsung", "Random Traders", AMAZON)
    assert trust.authorised("Redmi", "Dawntech Electronics", AMAZON)


def test_a_brand_with_only_its_own_store_recorded_marks_just_its_own_site():
    assert trust.authorised("vivo", None, "https://shop.vivo.com/in/product/1")
    assert trust.authorised("LG", None, "https://www.lg.com/in/tv-soundbars/x")
    assert trust.authorised("Philips", None, "https://www.philips.co.in/c-p/x")
    assert not trust.authorised("vivo", "Any Seller", AMAZON) and not trust.authorised("HP", "Any Seller", FLIPKART)
    assert not trust.authorised("vivo", None, "https://vivo-offers.example.com/phone")    # a look-alike site is not the brand's
    assert trust.brand_entry("iQOO") is trust.brand_entry("vivo") or trust.brand_entry("iQOO")["domains"] == ["vivo.com"]
    assert trust.brand_entry("Harman Kardon")["domains"][0] == "jbl.com"


def test_pending_lists_are_recorded_so_they_are_not_forgotten():
    for brand in ("sony", "jbl", "logitech", "belkin"):
        entry = REGISTRY["brands"][brand]
        assert entry["list_pending_url"].startswith("https://") and not entry.get("sellers") and not entry.get("marketplaces")


def test_ptron_names_its_amazon_sellers_and_sells_itself_elsewhere():
    assert trust.authorised("pTron", "Appario Retail Private Ltd", AMAZON)
    assert trust.authorised("pTron", "Cocoblu Retail Limited", AMAZON) and trust.authorised("PTRON", "Electronics Bazaar", AMAZON)
    assert trust.authorised("pTron", "Etrade Marketing Private Limited", AMAZON)
    assert trust.authorised("pTron", "Palred Electronics Private Limited", FLIPKART)      # the brand's own company
    assert not trust.authorised("pTron", "Palred Electronics Private Limited", AMAZON)    # not on its Amazon list
    assert not trust.authorised("pTron", "Appario Retail", FLIPKART) and not trust.authorised("pTron", "Random", AMAZON)
    assert trust.authorised("pTron", None, "https://ptron.in/products/x")
    assert trust.brand_entry("Palred Electronics")["source_url"].endswith("/pages/repair-service-warranty")


def test_asus_says_flipkart_and_amazon_are_its_only_online_dealers():
    entry = trust.brand_entry("ASUS")
    assert entry["official_channels"] == ["flipkart.com", "amazon.in"] and "only authorized" in entry["source"]
    assert trust.brand_entry("ROG") is entry


@pytest.mark.parametrize("brand", sorted(REAL))
def test_seller_aliases_belong_to_a_seller_the_brand_named(brand):
    entry = REAL[brand]
    named = {*entry.get("sellers", []), *(n for m in entry.get("marketplaces", {}).values() for n in m["sellers"])}
    for listed, others in entry.get("seller_aliases", {}).items():
        assert listed in named, f"{listed} is not a seller {brand} named"
        assert others and all(isinstance(a, str) and a.strip() for a in others)
        assert entry.get("notes"), "an alias is SafeShelf's own addition: its reason is written down"
