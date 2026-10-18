"""sellerAge: how long has this seller been around? POST /v1/listings/seller-age. Rules in code, no AI, no cost.

Amazon does not publish when a seller joined, but a seller's public profile shows how many ratings it has had in the
last 30 days, 90 days, 12 months and in total. Ratings are dated, so the counts say how far back the seller's history
goes, in bands (never an exact day):
  ratings older than a year exist                     -> established (more than a year)
  all within a year, some 90-365 days old              -> about 3 to 12 months
  all within 90 days, some 30-90 days old              -> about 1 to 3 months
  all within the last 30 days                          -> under a month
  fewer than MIN_RATINGS in total                      -> too few to tell (and little track record)
A band counts only with a real gap between two counts (GAP_MIN ratings, or GAP_SHARE of the total for a big seller), so
a stray rating does not move a seller up a band. It is an estimate from rating history, and the answer says so.
"""
POLICY = "seller-age-v1"
LABEL = ("Estimated from the seller's public rating counts (30 days, 90 days, 12 months, lifetime). "
         "Amazon does not publish when a seller joined.")
MIN_RATINGS = 10
GAP_MIN = 3
GAP_SHARE = 0.01
KEYS = ("last_30_days", "last_90_days", "last_12_months", "lifetime")
BANDS = {
    "new": ("Very new seller", "warn", (0, 30),
            "All {n} of this seller's ratings are from the last 30 days, so they are likely under a month old here."),
    "recent": ("Recently started seller", "warn", (30, 90),
               "This seller's ratings go back about 1 to 3 months, so they are fairly new here."),
    "under_a_year": ("Seller under a year old", "none", (90, 365),
                     "This seller's ratings go back about 3 to 12 months."),
    "established": ("Established seller", "ok", (365, None),
                    "This seller has ratings from more than a year ago."),
}


def counts_of(feedback) -> dict | None:
    """The four counts, or None unless all are whole numbers that never shrink from a shorter period to a longer one."""
    if not isinstance(feedback, dict):
        return None
    values = {}
    for key in KEYS:
        value = feedback.get(key)
        if isinstance(value, bool) or not isinstance(value, int | float) or value < 0 or value != int(value):
            return None
        values[key] = int(value)
    ordered = [values[k] for k in KEYS]
    return values if ordered == sorted(ordered) else None


def answer(verdict: str, headline: str, tone: str, text: str, days, counts, seller, reasons) -> dict:
    return {"verdict": verdict, "headline": headline, "tone": tone, "text": text,
            "age_days": {"min": days[0], "max": days[1]} if days else None, "basis": "rating_history",
            "ratings": counts, "seller": seller, "reasons": reasons, "policy_version": POLICY, "label": LABEL}


def assess(listing: dict) -> dict:
    seller = (listing.get("seller") or "").strip()[:120] or None
    counts = counts_of(listing.get("feedback"))
    if not counts:
        return answer("unknown", "Seller age not available", "none",
                      "This seller's rating counts could not be read for this listing.", None, None, seller,
                      ["No usable rating counts were sent"])
    m30, m90, m12, life = (counts[k] for k in KEYS)
    gap = max(GAP_MIN, GAP_SHARE * life)
    if life < MIN_RATINGS:
        return answer("few_ratings", "Very few ratings", "warn",
                      f"Only {life} rating{'' if life == 1 else 's'} in total: too few to tell how long this seller has "
                      "been active, and little track record.", None, counts, seller,
                      [f"{life} lifetime rating{'' if life == 1 else 's'}; at least {MIN_RATINGS} are needed to place the seller's age"])
    if life - m12 >= gap:
        band, why = "established", f"{life - m12:,} of {life:,} ratings are older than a year"
    elif m12 - m90 >= gap:
        band, why = "under_a_year", f"No rating is older than a year, but {m12 - m90:,} are 3 to 12 months old"
    elif m90 - m30 >= gap:
        band, why = "recent", f"No rating is older than 90 days, but {m90 - m30:,} are 1 to 3 months old"
    else:
        band, why = "new", f"All {life:,} ratings are from the last 30 days"
    headline, tone, days, text = BANDS[band]
    return answer(band, headline, tone, text.format(n=life), days, counts, seller,
                  [why, f"Ratings: {m30:,} in 30 days, {m90:,} in 90 days, {m12:,} in 12 months, {life:,} in total"])
