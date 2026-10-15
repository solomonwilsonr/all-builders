"""Which JAPAC market a listing belongs to, and what follows from it: currency, the regulators whose recall sites the
Research Agent searches (research/browser.py SOURCES), where a report goes, and the safety marks shoppers look for.

SafeShelf is JAPAC-first (India, Japan, Australia / New Zealand, Singapore and South-East Asia). The market comes from
the shop's address (amazon.co.jp, flipkart.com, shopee.sg...), else from the price's currency.
"""
from urllib.parse import urlparse

# Shop address endings, most specific first.
HOSTS = [(".co.jp", "jp"), (".jp", "jp"), (".com.au", "au"), (".au", "au"), (".co.nz", "nz"), (".nz", "nz"),
         (".com.sg", "sg"), (".sg", "sg"), (".com.my", "my"), (".my", "my"), (".co.id", "id"), (".id", "id"),
         (".co.th", "th"), (".th", "th"), (".com.ph", "ph"), (".ph", "ph"), (".vn", "vn"), (".co.in", "in"),
         (".in", "in"), ("flipkart.com", "in"), ("myntra.com", "in"), ("meesho.com", "in"), ("rakuten.co.jp", "jp")]
CURRENCY = {"in": "INR", "jp": "JPY", "au": "AUD", "nz": "NZD", "sg": "SGD", "my": "MYR", "id": "IDR", "th": "THB",
            "ph": "PHP", "vn": "VND"}
BY_CURRENCY = {v: k for k, v in CURRENCY.items()}
NAMES = {"in": "India", "jp": "Japan", "au": "Australia", "nz": "New Zealand", "sg": "Singapore", "my": "Malaysia",
         "id": "Indonesia", "th": "Thailand", "ph": "the Philippines", "vn": "Vietnam"}

# Recall sites searched for each market: its own regulator first, then large international databases (many products
# sold in JAPAC are also sold, and recalled, in the US and EU). India has no public recall database.
RECALL_SOURCES = {"jp": ["jp_caa", "cpsc", "eu"], "au": ["accc", "nz", "cpsc"], "nz": ["nz", "accc", "cpsc"],
                  "sg": ["sg", "cpsc", "eu"], "my": ["sg", "cpsc", "eu"], "id": ["cpsc", "eu", "nz"],
                  "th": ["cpsc", "eu", "nz"], "ph": ["cpsc", "eu", "nz"], "vn": ["cpsc", "eu", "nz"],
                  "in": ["cpsc", "eu", "nz"]}
DEFAULT_SOURCES = ["cpsc", "eu", "nz"]

# Where a shopper reports an unsafe product (they file it themselves; SafeShelf only drafts it).
REGULATORS = {
    "in": {"name": "National Consumer Helpline, India (with the BIS registration number if the label shows one)",
           "url": "https://consumerhelpline.gov.in/"},
    "jp": {"name": "Consumer Affairs Agency, Japan", "url": "https://www.caa.go.jp/"},
    "au": {"name": "ACCC Product Safety Australia", "url": "https://www.productsafety.gov.au/"},
    "nz": {"name": "Product Safety New Zealand", "url": "https://www.productsafety.govt.nz/"},
    "sg": {"name": "Consumer Product Safety Office, Singapore", "url": "https://www.consumerproductsafety.gov.sg/"},
    "us": {"name": "U.S. Consumer Product Safety Commission (SaferProducts.gov)", "url": "https://www.saferproducts.gov/"},
}

# The mark a shopper should look for on an electrical product's label, by market.
SAFETY_MARKS = {"in": "BIS / ISI mark with an R-number", "jp": "PSE mark (diamond or circle)",
                "au": "RCM mark", "nz": "RCM mark", "sg": "SAFETY Mark", "my": "SIRIM / ST-SIRIM label",
                "th": "TIS (TISI) mark", "ph": "PS or ICC mark", "id": "SNI mark", "vn": "CR mark"}


def of(url: str | None = None, currency: str | None = None) -> str | None:
    """The market code (in, jp, au, nz, sg, my, id, th, ph, vn), or None when nothing says."""
    host = (urlparse(url or "").hostname or "").lower()
    for ending, code in HOSTS:
        bare = ending.lstrip(".")
        if host == bare or host.endswith("." + bare):
            return code
    return BY_CURRENCY.get((currency or "").upper())


def recall_sources(code: str | None) -> list[str]:
    return RECALL_SOURCES.get(code or "", DEFAULT_SOURCES)


def currency(code: str | None, default: str = "INR") -> str:
    return CURRENCY.get(code or "", default)
