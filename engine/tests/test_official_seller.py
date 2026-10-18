"""officialSeller: the seller against the brand's own published lists, from the title and the seller name only. Plain code:
no page text, no Gemini, no search, no network, no database."""
import pytest

from engine import official_seller as osl

AMAZON, FLIPKART = "https://www.amazon.in/dp/B0X", "https://www.flipkart.com/p/itm1"
CMF_CHARGER = ("33W Type-C Fast Charger Adapter - Quick Charge 3A Wall Charger Compatible with CMF by Nothing 2/2A Plus, USB-C Phones, "
               "Android Devices, Portable Fast Charging Adapter - White")


def ask(title, seller, url=AMAZON, **extra):
    return osl.assess({"url": url, "title": title, "seller": seller, **extra})


def test_the_real_mak_charger_page_checks_cmf_from_its_title_alone():
    """Only the URL, title and seller are sent: no page text, no brand row."""
    out = ask(CMF_CHARGER, "MAKCELLPHONESPVTLTD")
    assert (out["verdict"], out["headline"], out["official"], out["tone"]) == ("channel_not_listed", "Not an official partner", False, "none")
    assert out["text"] == "CMF is mentioned in the title. CMF's official online partners: Flipkart, Myntra."
    assert (out["mentioned_brand"], out["brand"], out["marketplace"], out["seller"]) == ("CMF", "CMF", "amazon.in", "MAKCELLPHONESPVTLTD")
    assert out["official_channels"] == ["Flipkart", "Myntra"] and out["source"]["as_of"] == "2025-08-28"
    assert out["source"]["url"].endswith("/38494767092881-Where-can-I-buy-Nothing-and-CMF-products-in-India")
    flip = ask(CMF_CHARGER, "Z", FLIPKART)
    assert (flip["verdict"], flip["official"]) == ("channel_listed", True)
    assert flip["text"] == "CMF is mentioned in the title. Flipkart is one of CMF's official online partners; no individual sellers are named."


def test_a_seller_named_on_the_brands_list_is_an_official_partner():
    out = ask("boAt Airdopes 141 Bluetooth Earbuds", "Appario Retail Private Ltd")
    assert (out["verdict"], out["headline"], out["official"], out["tone"]) == ("official_seller", "Official partner", True, "ok")
    assert out["text"] == ("boAt product sold by Appario Retail Private Ltd on Amazon.in. Appario Retail Private Ltd is on boAt's "
                           "list of official Amazon.in sellers.")
    assert out["brand"] == "boAt" and out["source"]["url"] == "https://www.boat-lifestyle.com/pages/warranty"
    assert "not a regulator's finding" in out["label"]
    assert ask("Samsung Galaxy M35 5G", "Clicktech Retail Private Ltd")["verdict"] == "official_seller"
    assert ask("pTron Bassbuds Duo", "Etrade Marketing Private Limited")["verdict"] == "official_seller"
    assert ask("pTron Bassbuds Duo", "Palred Electronics Pvt Ltd", FLIPKART)["verdict"] == "official_seller"
    assert ask("Redmi 15C 5G 4GB", "Dawntech Electronics")["verdict"] == "official_seller"


def test_a_seller_named_like_the_brand_is_a_hint_not_proof():
    out = ask("boAt Rockerz 255", "boAt")
    assert (out["verdict"], out["headline"], out["official"], out["tone"]) == ("official_brand", "Seller named like the brand", None, "none")
    assert out["text"] == "boAt product sold by boAt on Amazon.in. The seller carries the boAt name (a hint, not proof)."
    for seller in ("Samsung Electronics", "Samsung India Electronics Pvt Ltd", "SAMSUNG", "Samsung India"):
        assert ask("Samsung Galaxy M35", seller)["verdict"] == "official_brand", seller
    assert ask("Redmi 15C 5G", "Xiaomi India Pvt Ltd")["verdict"] == "official_brand"       # the brand's company, via the registry entry
    for seller in ("Samsung Mobile Zone", "Samsung Fans", "Official Samsung Store", "Sam Sung Traders"):
        assert ask("Samsung Galaxy M35", seller)["verdict"] != "official_brand", seller


def test_a_brand_with_official_sellers_on_this_shop_is_official_there_whoever_resells_it():
    out = ask("boAt Rockerz 255", "Random Traders")
    assert (out["verdict"], out["headline"], out["official"], out["tone"]) == ("channel_listed", "Official on Amazon.in", True, "ok")
    assert out["text"] == ("boAt product sold by Random Traders on Amazon.in. boAt is officially sold on Amazon.in. Its listed sellers: "
                           "Appario Retail, Techretailer, Techvast Pvt. Ltd. and 8 more.")
    assert "can still be genuine" not in out["text"]                                  # the caveat lives in the details
    assert out["reasons"][1] == "Random Traders is not among the 11 named sellers; the list may use its company name"
    assert any("company name" in r for r in out["reasons"])
    assert ask("boAt Rockerz 255", "Wave Tone", FLIPKART)["headline"] == "Official on Flipkart"   # boAt names Flipkart sellers too
    assert ask("CMF Phone 1", "Random Traders")["official"] is False                  # CMF's official partners are not Amazon
    unlisted = ask("Redmi 15C 5G", "Random Etel!")                                     # a name the list and its aliases do not have
    assert unlisted["verdict"] == "channel_listed" and unlisted["official"] is True


def test_a_trade_name_of_a_listed_company_counts_and_says_so():
    """Amazon shows Xiaomi's listed "Dawntech Electronics" as "Dawntech Etel!" (an alias SafeShelf recorded, labelled as its own)."""
    out = ask("Redmi 15C 5G Prime Edition Moonlight Blue 4GB + 128GB", "Dawntech Etel!")
    assert (out["verdict"], out["headline"], out["official"]) == ("official_seller", "Official partner", True)
    assert out["text"] == ("Redmi product sold by Dawntech Etel! on Amazon.in. Dawntech Etel! is a trade name of Dawntech Electronics, "
                           "which is on Redmi's list of official Amazon.in sellers.")
    assert out["reasons"][1] == "'Dawntech Etel!' is recorded by SafeShelf as a trade name of Dawntech Electronics: that name is not on the brand's own list"
    direct = ask("Redmi 15C 5G", "Dawntech Electronics")
    assert direct["verdict"] == "official_seller" and "trade name" not in direct["text"]
    assert ask("Redmi 15C 5G", "Dawntech Etel Pvt Ltd")["verdict"] == "official_seller"        # the full company name on the shop
    sam = ask("Samsung Galaxy M17e 5G Mobile (Blitz Blue, 4GB RAM, 128GB Storage)", "Dawntech Etel!")  # Samsung lists it as "Darshita Etel"
    assert sam["official"] is True and "trade name of Darshita Etel" in sam["text"]
    assert ask("OnePlus Nord CE 4", "Dawntech Etel!")["official"] is not True                  # an alias only counts for the brands that carry it


def test_a_brand_that_names_its_channels_says_who_its_partners_are():
    out = ask("CMF Phone 2 Pro 8GB", "Any Seller")
    assert (out["verdict"], out["headline"], out["official"]) == ("channel_not_listed", "Not an official partner", False)
    assert out["text"] == "CMF product sold by Any Seller on Amazon.in. CMF's official online partners: Flipkart, Myntra."
    flip = ask("Nothing Phone (3a)", "Any Seller", FLIPKART)
    assert (flip["verdict"], flip["headline"], flip["official"]) == ("channel_listed", "Official channel", True)
    assert flip["text"] == "Nothing product sold by Any Seller on Flipkart. Flipkart is one of Nothing's official online partners; no individual sellers are named."
    asus = ask("ASUS Vivobook 15 Laptop", "Any Seller")
    assert asus["verdict"] == "channel_listed" and "Amazon.in is one of ASUS's official online partners" in asus["text"]


def test_a_long_channel_list_is_shortened():
    out = ask("boAt Airdopes", "Z", "https://www.meesho.com/p/1")
    assert out["text"] == ("boAt product sold by Z on Meesho. boAt's official online partners: boat-lifestyle.com, Amazon.in, "
                           "Flipkart and 20 more.")


def test_a_title_that_opens_with_a_brand_is_that_brand_and_names_in_it_are_ignored():
    """An Anker charger "for Samsung phones" is an Anker product: Samsung's list says nothing about it."""
    out = ask("Anker 20W Charger for Samsung and CMF Phones", "Random Traders")
    assert out["verdict"] == "no_list" and "mentioned_brand" not in out and out["brand"] == "Anker"
    assert ask("Samsung Galaxy Buds charger for CMF Phone 1", "Clicktech Retail")["brand"] == "Samsung"
    assert "mentioned_brand" not in ask("Samsung Galaxy Buds charger for CMF Phone 1", "Clicktech Retail")


def test_a_brand_named_later_in_the_title_is_checked_when_the_title_opens_with_something_else():
    listed = ask("USB-C Charger Compatible with boAt Earbuds", "Wave Tone")
    assert (listed["verdict"], listed["mentioned_brand"]) == ("official_seller", "boAt")
    assert listed["text"] == "boAt is mentioned in the title. Wave Tone is on boAt's list of official Amazon.in sellers."
    other = ask("USB-C Charger Compatible with boAt Earbuds", "Random Traders")
    assert other["verdict"] == "channel_listed" and other["text"].startswith("boAt is mentioned in the title. boAt is officially sold on Amazon.in.")


def test_names_that_are_not_brands_with_something_to_say_stay_quiet():
    for title in ("33W Charger for vivo and LG phones", "MAK 33W charger", "Charger for mi pad", "Nothingness charger", "33W Charger Compatible with Sony"):
        out = ask(title, "Z")
        assert out["verdict"] == "unknown_brand" and "mentioned_brand" not in out, title
    assert ask("", "Z")["text"] == "The listing's title was not found, so there is no brand to check."


def test_a_marketplace_seller_list_is_not_claimed_for_brands_with_only_their_own_sites():
    for title in ("vivo T3x 5G", "Portronics Eco Glow 2 Torch", "LG 7kg Washing Machine", "Sony WH-1000XM5"):
        out = ask(title, "Some Seller")
        assert out["verdict"] == "no_list" and out["official"] is None, title
        assert out["verdict"] not in osl.SHOWN
    assert ask("vivo T3x 5G", "S")["text"] == "vivo publishes no list of authorised Amazon.in sellers."


def test_amazon_itself_as_the_seller():
    out = ask("boAt Airdopes", "Amazon")
    assert (out["verdict"], out["headline"], out["official"]) == ("amazon_retail", "Sold by Amazon", None)
    assert out["text"] == "boAt product sold by Amazon itself."
    assert ask("boAt Airdopes", "Amazon Retail India")["verdict"] == "amazon_retail"
    assert ask("boAt Airdopes", "Amazon Basics Traders")["verdict"] == "channel_listed"


def test_other_websites_are_the_brands_own_or_not():
    own = ask("boAt Airdopes", None, "https://www.boat-lifestyle.com/products/x")
    assert (own["verdict"], own["headline"], own["official"], own["tone"]) == ("official_website", "Official website", True, "ok")
    fake = ask("boAt Airdopes", None, "https://boat-deals.example.com/p/1")
    assert (fake["verdict"], fake["headline"], fake["official"], fake["tone"]) == ("third_party_website", "Not an official website", False, "none")
    assert fake["text"] == "boAt's own websites: boat-lifestyle.com. This is not one of them."


def test_the_seller_name_is_all_the_page_needs_to_give():
    assert ask("boAt Airdopes", None)["verdict"] == "no_list"
    assert ask("boAt Airdopes", None)["text"] == "The seller's name was not found on the page."
    assert osl.assess({})["verdict"] == "unknown_brand"
    assert ask("NoName 65W charger", "x")["text"] == "No brand with a published seller list is named in the title."


def test_the_page_text_is_never_read():
    """Whatever the page text says, only the title and seller decide."""
    with_text = ask("33W Charger", "Z", page_text="Brand\tboAt\nSold by Wave Tone")
    assert with_text["verdict"] == "unknown_brand" and with_text == ask("33W Charger", "Z")


@pytest.mark.parametrize("verdict", sorted(osl.SHOWN))
def test_every_shown_verdict_is_neutral_or_green_never_a_warning_colour(verdict):
    cases = {"official_brand": ask("boAt Rockerz", "boAt"), "official_seller": ask("boAt Rockerz", "Wave Tone"),
             "amazon_retail": ask("boAt Rockerz", "Amazon"), 
             "channel_not_listed": ask("CMF Phone 1", "Z"), "channel_listed": ask("Nothing Phone 3a", "Z", FLIPKART),
             "official_website": ask("boAt Rockerz", None, "https://www.boat-lifestyle.com/"),
             "third_party_website": ask("boAt Rockerz", None, "https://x.example.com/")}
    assert cases[verdict]["verdict"] == verdict and cases[verdict]["tone"] in ("ok", "none")
    assert cases[verdict]["official"] in (True, False, None)


def test_an_amazon_brand_store_link_shows_the_brand_sells_officially_when_the_registry_has_no_list():
    """Portronics: the registry holds only its own website; the listing links to the "Portronics Store" on Amazon.in."""
    listing = {"url": AMAZON, "title": "Portronics Eco Glow 2 Tactical Rechargeable Flashlight", "seller": "ETrade Online"}
    assert osl.assess(listing)["verdict"] == "no_list"
    out = osl.assess({**listing, "brand_store": "Portronics"})
    assert (out["verdict"], out["official"], out["headline"]) == ("channel_listed", True, "Official brand store on Amazon.in")
    assert out["text"] == "Portronics product sold by ETrade Online on Amazon.in. Portronics has an official brand store on Amazon.in."
    assert osl.assess({**listing, "brand_store": "Someone Else"})["verdict"] == "no_list"          # not the title's brand
    assert osl.assess({**listing, "brand_store": "Portronics", "url": FLIPKART})["verdict"] != "channel_listed"  # an Amazon link only
    unknown = osl.assess({"url": AMAZON, "title": "Zebronics Zeb-Fit Watch", "seller": "Z", "brand_store": "Zebronics"})
    assert unknown["official"] is True                                                         # a brand with no registry entry too
    assert osl.assess({"url": AMAZON, "title": "boAt Rockerz", "seller": "Z", "brand_store": "boAt"})["reasons"][0].startswith("boAt publishes")  # a registry list stays in charge
