"""sellerAge (the widget's name): how long has this product been listed? POST /v1/listings/listing-age. Plain code.

The product page states "Date First Available": when the listing first appeared. That is the listing's age, not the
seller's: a marketplace does not publish when a seller joined, so the age shown says what it is. A brand-new listing has
no track record (no reviews, no history), which is the signal a shopper wants for a fresh fake or dropshipped product.
The extension reads the date from the page; the page text is the fallback. Days are worked out here, in code.

Many pages show no such date, so there are two fallbacks, in this order:
  - the first review: when every review of the product was read (the reviews_complete flag), the oldest one dates the
    listing about as well as a "Date First Available" would. When only some were read (a popular product), the oldest
    one read is only a floor ("listed at least since"), and never proof that a listing is new;
  - no reviews at all: "no reviews yet", a very new or untested listing. Said only when the reviews were really read.

Amazon's brand card also says how long the brand has sold there ("10+ years on Amazon") and how buyers rate it. That is
the BRAND's tenure, not the listing's or the seller's, so it is returned beside the age (never mixed into the verdict).
"""
import re
from datetime import date, datetime

POLICY = "listing-age-v1"
LABEL = ("The age of this product listing (its \"Date First Available\"), not the seller's: "
         "marketplaces do not publish when a seller joined.")
MONTHS = {name.lower(): n for n, names in enumerate(
    (("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",), ("june", "jun"),
     ("july", "jul"), ("august", "aug"), ("september", "sep", "sept"), ("october", "oct"), ("november", "nov"),
     ("december", "dec")), start=1) for name in names}
LABELLED = re.compile(r"Date First Available\s*[:\-]?\s*(.{0,30})", re.IGNORECASE)
MAX_AGE_DAYS = 30 * 365
NOT_THE_SELLER = "This is the listing's age, not the seller's: marketplaces do not publish when a seller joined"
NEW, RECENT, YEAR = 30, 90, 365


def parse_date(text) -> date | None:
    """A date as Amazon prints it ("12 March 2026", "March 12, 2026", "12/03/2026", "2026-03-12"), else None."""
    clean = re.sub(r"[\u200E\u200F]", "", str(text or "")).strip()
    try:
        if found := re.search(r"(\d{4})-(\d{2})-(\d{2})", clean):
            return date(int(found.group(1)), int(found.group(2)), int(found.group(3)))
        if found := re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})", clean):
            return date(int(found.group(3)), MONTHS[found.group(2).lower()], int(found.group(1)))
        if found := re.search(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})", clean):
            return date(int(found.group(3)), MONTHS[found.group(1).lower()], int(found.group(2)))
        if found := re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", clean):  # day first, as in India
            return date(int(found.group(3)), int(found.group(2)), int(found.group(1)))
    except (KeyError, ValueError):
        return None
    return None


def first_available(listing: dict) -> date | None:
    """The date the extension read from the page, else the one in the page text."""
    if parsed := parse_date(listing.get("first_available")):
        return parsed
    found = LABELLED.search(str(listing.get("page_text") or ""))
    return parse_date(found.group(1)) if found else None


def ago(days: int) -> str:
    if days <= 0:
        return "today"
    if days < 60:
        return f"{days} day{'' if days == 1 else 's'} ago"
    if days < 730:
        return f"about {round(days / 30)} months ago"
    return f"about {days // 365} years ago"


def span(days: int) -> str:
    """How long, without "ago": "5 days", "about 7 months", "about 3 years"."""
    return f"{days} day{'' if days == 1 else 's'}" if days < 60 else f"about {round(days / 30)} months" if days < 730 else f"about {days // 365} years"


def band_of(age: int) -> tuple[str, str, str]:
    """(verdict, headline, tone) for a listing age in days."""
    if age < NEW:
        return "new", "New listing", "warn"
    if age < RECENT:
        return "recent", "Recent listing", "warn"
    if age < YEAR:
        return "under_a_year", "Listed under a year ago", "none"
    return "established", "Long-listed product", "ok"


def result(verdict, headline, tone, text, basis, reasons, listed=None, age=None) -> dict:
    return {"verdict": verdict, "headline": headline, "tone": tone, "listed_on": listed.isoformat() if listed else None,
            "age_days": age, "text": text, "basis": basis, "reasons": reasons, "policy_version": POLICY, "label": LABEL}


def count_of(value) -> int | None:
    return int(value) if isinstance(value, int | float) and not isinstance(value, bool) and value >= 0 else None


YEARS = re.compile(r"(\d{1,3})(\+?)\s+years?\s+on\s+Amazon", re.IGNORECASE)
POSITIVE = re.compile(r"(\d{1,3})%\s+positive\s+ratings\s+from\s+([\d.,]+\s?[KkMm]?\+?)\s+customers", re.IGNORECASE)
ORDERS = re.compile(r"([\d.,]+\s?[KkMm]?\+?)\s+recent\s+orders\s+from\s+this\s+brand", re.IGNORECASE)
BRAND = re.compile(r"Top Brand\s+(.{2,40}?)\s+\d{1,3}%\s+positive", re.IGNORECASE)


def brand_card(listing: dict) -> dict | None:
    """What Amazon's brand card says: the brand, how long it has sold on Amazon, and how buyers rate it. None without one."""
    flat = re.sub(r"\s+", " ", f"{listing.get('brand_text') or ''} {listing.get('page_text') or ''}")
    years, positive, orders, name = YEARS.search(flat), POSITIVE.search(flat), ORDERS.search(flat), BRAND.search(flat)
    if not (years or positive):
        return None
    return {"name": name.group(1).strip() if name else None,
            "years_on_amazon": f"{years.group(1)}{years.group(2)}" if years else None,
            "positive_ratings": {"percent": int(positive.group(1)), "customers": positive.group(2).replace(" ", "")} if positive else None,
            "recent_orders": orders.group(1).replace(" ", "") if orders else None}


def assess(listing: dict, today: date | None = None) -> dict:
    """The listing's age (page date, else the reviews), with the brand card beside it."""
    return {**listing_age(listing, today), "brand": brand_card(listing)}


def listing_age(listing: dict, today: date | None = None) -> dict:
    today = today or datetime.now().astimezone().date()
    listed = first_available(listing)
    age = (today - listed).days if listed else None
    if listed is not None and 0 <= age <= MAX_AGE_DAYS:
        when = f"{listed.day} {listed:%B %Y}"
        verdict, headline, tone = band_of(age)
        text = {"new": f"This product was first listed {ago(age)} ({when}). A brand-new listing has little track record.",
                "recent": f"This product was first listed {ago(age)} ({when}), so it has a short track record."}.get(
                    verdict, f"This product was first listed {ago(age)} ({when}).")
        return result(verdict, headline, tone, text, "date_first_available",
                      [f"Date First Available: {when} ({age} day{'' if age == 1 else 's'} ago)", NOT_THE_SELLER], listed, age)

    # No usable date on the page: the reviews are the next best evidence.
    read, complete, total = count_of(listing.get("reviews_read")), listing.get("reviews_complete") is True, count_of(listing.get("ratings_total"))
    oldest = parse_date(listing.get("oldest_review"))
    oldest_age = (today - oldest).days if oldest else None
    if oldest is not None and 0 <= oldest_age <= MAX_AGE_DAYS:
        when = f"{oldest.day} {oldest:%B %Y}"
        if complete:  # every review was read: the oldest one is the first one
            verdict, headline, tone = band_of(oldest_age)
            text = (f"The first review of this product is from {ago(oldest_age)} ({when}), so it has been listed about that "
                    "long." + (" A brand-new listing has little track record." if verdict == "new" else ""))
            return result(verdict, headline, tone, text, "first_review",
                          [f"No \"Date First Available\" on this page; the oldest of all its reviews is from {when}", NOT_THE_SELLER],
                          oldest, oldest_age)
        return result("listed_at_least", f"Listed for at least {span(oldest_age)}", "none",
                      f"The oldest review we read is from {ago(oldest_age)} ({when}), so this product has been listed for at "
                      "least that long. We did not read every review, so it may be much older.", "review_floor",
                      [f"No \"Date First Available\" on this page; the oldest review we read is from {when}", NOT_THE_SELLER],
                      oldest, oldest_age)
    if (read == 0 and complete) or total == 0:  # the reviews were really read, and there are none
        return result("no_reviews", "No reviews yet", "warn", "This product has no reviews yet: a very new or untested listing.",
                      "no_reviews", ["No \"Date First Available\" on this page, and no reviews to date it by", NOT_THE_SELLER])
    return result("unknown", "Listing age not available", "none", "This page does not show when the product was first listed.",
                  "none", ["No usable \"Date First Available\" on the page, and no review dates to go by"])
