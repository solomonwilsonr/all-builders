"""The coverage list every answer carries: country by country, which sources were checked, how (live or stored copy),
when, how fresh they are, and what they found for this product. No matches in one country is never shown as a global
all-clear, and a source that failed is "source unavailable", never "no matching notice".
"""
from engine.sources import registry
from engine.sources.base import (
    CHECKED_CACHE,
    CHECKED_LIVE,
    NO_MATCH,
    NOT_SUPPORTED,
    UNAVAILABLE,
    SourceResult,
)

# Which countries a multi-country source covers, for the per-country roll-up.
MULTI = {"oecd_globalrecalls": ["AU", "JP", "KR", "SG", "TW", "MY", "ID", "TH", "PH", "VN"],
         "stored_notices": ["US", "AU", "JP", "KR", "SG", "TW", "MY", "ID", "TH", "PH", "VN", "IN"],
         "manufacturer": []}
ASEAN_STALE = "ASEAN notices in this feed stop in 2022"
STALE_NOTES = {"oecd_globalrecalls": {"SG": "Singapore notices in this feed stop in 2022", "MY": ASEAN_STALE,
                                      "ID": ASEAN_STALE, "TH": ASEAN_STALE, "PH": ASEAN_STALE, "VN": ASEAN_STALE}}
COUNTRY_NOTES = {"IN": "India has no public recall database: CCPA recall orders, safety notices and BIS raids are "
                       "checked instead, and BIS certificates can only be verified by hand.",
                 "NZ": "New Zealand recalls are not in any open feed; searched in a browser on deep checks only.",
                 "SG": "Singapore's CPSO site refuses automated requests; newer notices need a person to look."}
ORDER = [CHECKED_LIVE, CHECKED_CACHE, NO_MATCH, UNAVAILABLE, NOT_SUPPORTED]


def countries_of(source_id: str) -> list[str]:
    entry = registry.source(source_id)
    return MULTI.get(source_id, [entry["jurisdiction"]]) if entry["jurisdiction"] == "MULTI" \
        else [entry["jurisdiction"]]


def source_rows(plan: list[dict], results: list[SourceResult], matched: dict[str, dict[str, int]]) -> list[dict]:
    """One row per planned source: its state for this product. matched: {source: {country: notices that may concern
    this product}}, from the scope check."""
    by_source = {r.source: r for r in results}
    rows = []
    for step in plan:
        result = by_source.get(step["source"])
        if result is None:
            state, mode, at, detail = NOT_SUPPORTED, None, None, step["why"]
        elif not result.ok:
            state, mode, at, detail = result.coverage_state(), result.mode, result.retrieved_at.isoformat(), \
                result.detail
        else:
            n = sum(matched.get(step["source"], {}).values())
            state = (CHECKED_LIVE if result.mode == "live" else CHECKED_CACHE) if n else NO_MATCH
            mode, at = result.mode, result.retrieved_at.isoformat()
            detail = f"{n} notice(s) that may concern this product" if n else \
                f"searched {'live' if result.mode == 'live' else 'the stored copy'}; no notice matched this product"
        rows.append({"source": step["source"], "name": step["name"], "authority": step["authority"],
                     "role": step["role"], "jurisdiction": step["jurisdiction"], "state": state, "mode": mode,
                     "checked_at": at, "freshness": result.freshness if result else None,
                     "records_returned": len(result.records) if result and result.ok else 0,
                     "matched": sum(matched.get(step["source"], {}).values()),
                     "matched_by_country": dict(matched.get(step["source"], {})), "detail": detail})
    return rows


def matrix(market: str | None, rows: list[dict]) -> list[dict]:
    """Country by country: the market first, then each other country a checked source covers."""
    by_country: dict[str, list[dict]] = {}
    for row in rows:
        for country in countries_of(row["source"]):
            if not country:
                continue
            cell = dict(row)
            if row["state"] in (CHECKED_LIVE, CHECKED_CACHE):  # a match counts only in the country it belongs to
                cell["matched"] = row.get("matched_by_country", {}).get(country, 0)
                if not cell["matched"]:
                    cell["state"] = NO_MATCH
            by_country.setdefault(country, []).append(cell)
    usual = ["IN", "JP", "AU", "SG", "NZ", "KR", "TW", "US", "EU"]
    others = sorted((c for c in dict.fromkeys(usual + sorted(by_country)) if c != market),
                    key=lambda c: (-sum(x.get("matched_by_country", {}).get(c, 0) for x in by_country.get(c, [])),
                                   usual.index(c) if c in usual else len(usual)))
    order = ([market] if market else []) + others  # the market, then countries with notices, then the rest
    out = []
    for country in dict.fromkeys(order):
        if country not in by_country and country != market:
            continue
        cells = by_country.get(country, [])
        states = [c["state"] for c in cells]
        if any(s in (CHECKED_LIVE, CHECKED_CACHE) for s in states):
            state = CHECKED_LIVE if CHECKED_LIVE in states else CHECKED_CACHE
        elif NO_MATCH in states:
            state = NO_MATCH
        elif UNAVAILABLE in states:
            state = UNAVAILABLE
        else:
            state = NOT_SUPPORTED
        checked = [c["checked_at"] for c in cells if c["checked_at"]]
        notes = [STALE_NOTES.get(c["source"], {}).get(country) for c in cells]
        notes = [n for n in notes if n] + ([COUNTRY_NOTES[country]] if country in COUNTRY_NOTES else [])
        out.append({"country": country, "name": registry.market_name(country) if country != "EU" else
                    "the European Union", "is_market": country == market, "state": state,
                    "checked_at": max(checked) if checked else None,
                    "sources": [{"source": c["source"], "authority": c["authority"], "state": c["state"],
                                 "mode": c["mode"], "freshness": c["freshness"]} for c in cells],
                    "matched": sum(c["matched"] for c in cells), "notes": notes})
    return out


def summary_line(country_rows: list[dict]) -> str:
    """'India: no matching notice (stored copy) · US: 1 notice (live) · Japan: source unavailable'."""
    words = {CHECKED_LIVE: "notice found (live)", CHECKED_CACHE: "notice found (stored copy)",
             NO_MATCH: "no matching notice", UNAVAILABLE: "couldn't be checked", NOT_SUPPORTED: "not checked"}
    return " · ".join(f"{r['name']}: {words[r['state']]}" for r in country_rows[:6])
