"""Country rules for JAPAC evidence (plan v2.2 sections 2A and J4). JAPAC is a region, not one jurisdiction: each market
keeps its own regulators, identifiers and rules.

Four places are kept apart: market_country (where the shopper buys), source_jurisdiction (who issued a notice),
manufacturing_country, and recall_affected_country (where the notice says affected units were sold).
"""
from engine import region
from engine.sources import registry

# Regulators whose notices are local for each market (a notice from any other is cross-border evidence).
LOCAL_JURISDICTIONS = {"IN": {"IN"}, "JP": {"JP"}, "AU": {"AU"}, "NZ": {"NZ", "AU"}, "SG": {"SG"}, "KR": {"KR"},
                       "TW": {"TW"}, "MY": {"MY"}, "ID": {"ID"}, "TH": {"TH"}, "PH": {"PH"}, "VN": {"VN"},
                       "US": {"US"}}
# Notes the answer shows for each market's identifiers and marks (J4).
RULES = {
    "IN": [("A valid BIS mark (R-number or ISI licence) is required for many electrical goods; a valid mark is not "
            "proof of safety, and SafeShelf cannot check it automatically (BIS has no automation API).")],
    "JP": [("Electrical products need a PSE mark. Japanese model strings and notice IDs are kept as published; "
            "translations are notes beside them.")],
    "SG": [("A SAFETY Mark is required only for controlled goods (chargers, adaptors, kettles and similar); a missing "
            "mark on other products is not a violation.")],
    "AU": ["ACCC notices list the supplier, model and serial ranges; only those units are recalled."],
    "NZ": ["Australian and New Zealand notices often cover the same supplier; each country's own notice decides."],
}


def market_of(url: str | None = None, currency: str | None = None, given: str | None = None) -> str | None:
    """ISO code (upper case) of the shopper's market: what the caller says, else the shop's address or currency."""
    if given:
        return given.upper()
    code = region.of(url, currency)
    return code.upper() if code else None


def is_local(record_jurisdiction: str | None, affected_markets: list[str] | None, market: str | None) -> bool:
    """A notice is local when its regulator is the market's own, or it names the market among affected markets."""
    if not market:
        return False
    local = LOCAL_JURISDICTIONS.get(market.upper(), {market.upper()})
    return (record_jurisdiction or "").upper() in local or market.upper() in {m.upper() for m in affected_markets or []}


def places(market: str | None, record: dict | None = None, manufacturing_country: str | None = None) -> dict:
    record = record or {}
    return {"market_country": market, "source_jurisdiction": record.get("jurisdiction"),
            "manufacturing_country": manufacturing_country,
            "recall_affected_country": record.get("affected_markets") or ([record["jurisdiction"]]
                                                                          if record.get("jurisdiction") else [])}


def rules(market: str | None) -> list[str]:
    return RULES.get((market or "").upper(), [])


def languages(market: str | None) -> list[str]:
    return registry.market(market).get("languages", ["en"])


def identifiers(market: str | None) -> list[str]:
    return registry.market(market).get("identifiers", ["gtin"])
