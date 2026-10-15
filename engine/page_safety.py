"""'Is it safe?' for a listing SafeShelf has no product for: POST /v1/listings/safety-check.

Uses only what the shopper's page shows, and never creates a product (a fake shop must not become one):
- recalls: the listing's brand and model number against the official recall list (engine.recalls rules: only an
  exact model number is "recalled"; a notice that names the product family without model numbers is for review);
- reviews: the reviews shown on the page, read by the same Safety Radar as stored products (engine.radar). They are
  kept as evidence under the listing's URL, so each review is labelled once and the chat can cite it.
Code sets the verdict (radar.verdict). A handful of reviews with no hazard is "not enough evidence", never "safe".
Two page-only additions, so the backtested rules for stored products stay as they are: a notice without model
numbers is matched on the kind of product named in the page title (for review, never "recalled"), and two buyers'
serious first-hand reports of any hazard type are enough for amber (a page shows only a few reviews).
"""
import re
from datetime import UTC, datetime

from engine import identity, radar, recalls, safety, trust

MAX_REVIEWS = 30  # the page shows fewer; more would only slow the first check
MAX_RECALLS = 15  # newest brand notices; each one without model fields costs one cached Gemini read
LABEL = "AI finding from the reviews on this page - not a regulatory determination"
# When the brand is only the title's first word, these are not brands: no recall search for them.
NOT_BRANDS = {"new", "original", "super", "best", "premium", "pack", "set", "combo", "the", "fast", "smart", "mini",
              "pro", "portable", "wireless", "usb", "universal", "heavy", "multi", "electric", "digital"}
# Title words that say nothing about what kind of product it is.
NOT_KINDS = NOT_BRANDS | {"with", "pack", "for", "and", "black", "white", "blue", "inch", "fast", "charging", "watt",
                          "home", "office", "kids", "type", "port", "ports", "plus", "ultra", "model", "edition"}


def page_reviews(listing: dict) -> list[dict]:
    """The page's reviews in the Radar's shape. The text is required; rating and date are optional."""
    out = []
    today = datetime.now(UTC).date().isoformat()
    for review in (listing.get("reviews") or [])[:MAX_REVIEWS]:
        text = str(review.get("text") or "").strip()
        if not text:
            continue
        date = str(review.get("date") or "")[:10]
        try:
            datetime.fromisoformat(date)
        except ValueError:
            date = today  # undated: counts as seen today, so the trend is never invented from it
        out.append({"title": str(review.get("title") or "")[:200] or None, "text": text[:1500],
                    "rating": review.get("rating"), "date": date})
    return out


def kind_words(title: str) -> str:
    """The page title's product words ("VRURC OD-B7 Wall Charger" -> "wall charger"), standing in for a category."""
    return " ".join(w for w in re.findall(r"[a-z]{4,}", title.lower()) if w not in NOT_KINDS)


def recall_status(brand: str, fp: dict) -> dict:
    exact, review = [], []
    for recall in recalls.brand_recalls(brand)[:MAX_RECALLS]:
        try:
            match_class = recalls.classify(fp, recall)
        except RuntimeError:  # the notice could not be read by any model: say nothing rather than guess
            continue
        if match_class:
            entry = {"recall_id": recall["id"], "title": recall["title"], "url": recall.get("url"),
                     "notice_date": str(recall["notice_date"]) if recall.get("notice_date") else None}
            (exact if match_class == "exact_model" else review).append(entry)
    return {"recalled": bool(exact), "checked": recalls.authorities(), "recall_ids": [r["recall_id"] for r in exact],
            "recall_ids_under_review": [r["recall_id"] for r in review], "recalls": exact + review}


def searchable_brand(listing: dict, brand: str) -> str:
    """The brand to search recall notices for, or "" when it is only a generic first word of the title."""
    first = ((listing.get("title") or "").split() or [""])[0].strip(",:-")
    if brand == first and (brand.lower() in NOT_BRANDS or any(c.isdigit() for c in brand)):
        return ""
    return brand


def listing_safety(listing: dict) -> dict:
    brand = trust.listing_brand(listing)
    fp = identity.fingerprint({**listing, "brand": listing.get("brand") or brand})
    if not fp["category"]:  # a family-only notice is matched on the kind of product the title names
        title = listing.get("title") or ""
        fp["category"] = kind_words(re.sub(re.escape(brand), "", title, flags=re.IGNORECASE) if brand else title)
    status = recall_status(searchable_brand(listing, brand), fp)

    key = f"listing:{listing.get('url') or listing.get('title') or ''}"
    reviews = page_reviews(listing)
    if reviews:
        safety.add_reviews(key, reviews)
    stored = safety.product_reviews(key)  # this visit's reviews plus any seen on earlier visits to the same page
    view = f"{brand} {fp['model'] or ''} ({listing.get('title') or 'product'})".strip()
    labels = safety.label_reviews(view, stored)
    review_evidence = {r["id"]: r["evidence_id"] for r in stored}
    ai_findings = radar.findings(stored, labels)
    for finding in ai_findings:
        finding["evidence_ids"] = [review_evidence[e.removeprefix("REV-")] for e in finding["evidence_ids"]]
    verdict = radar.verdict(status["recalled"], len(stored), ai_findings)
    serious = sum(f["independent_reports"] for f in ai_findings if f["severity"] in ("medium", "high"))
    if verdict in ("green", "not_enough_evidence") and serious >= 2:
        verdict = "amber"
    return {
        "listing_url": listing.get("url"),
        "brand": brand or None,
        "model": fp["model"] or None,
        "verdict": verdict,
        "official_status": status,
        "ai_findings": ai_findings,
        "reviews_checked": len(stored),
        "label": LABEL,
    }
