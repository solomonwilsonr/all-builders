"""'Is this product any good?' from buyer reviews: POST /v1/listings/review-verdict.

Kept apart from safety on purpose: this verdict never changes the safety colour, and it is never red (red means an
official recall). Three inputs, and code decides:
- the page's star summary (every rating, read by the extension): how buyers rate it overall;
- the reviews read, labelled by Gemini in the Safety Radar call (engine.radar: aspects, liked, problem), so a review
  is read once for both answers and each label is stored once (engine.safety.label_reviews);
- simple checks on the reviews themselves for signs of inflated ratings: a burst of five-star reviews on one day,
  reviews that open with the same words, few verified buyers.

The extension reads about ten reviews per star level (1 to 5), so every kind of buyer is heard. A complaint's share
of all buyers is then estimated per star: the share of that star's reviews that mention it, times that star's share
of all ratings, summed over the stars (a stratified estimate; stars with too few reviews read are left out and the
rest re-weighted). It is an estimate from about 50 reviews, not a count of every review.
"""
import re
from collections import Counter
from datetime import date

from engine import page_safety, safety, trust

POLICY = "review-verdict-v1"
LABEL = "AI summary of buyer reviews - about quality, not safety"
MIN_RATINGS = 30          # fewer ratings than this: not_enough_reviews
GOOD_SHARE = 0.75         # at least this share of 4-5 star ratings, and no common complaint: good
POOR_SHARE = 0.55         # under this share of 4-5 star ratings: poor. Only the stars decide poor; a complaint caps at mixed
POOR_AVERAGE = 3.5        # an average rating under this is poor too (3.3 stars with half the ratings at 3 or less)
COMMON_COMPLAINT = 0.10   # a complaint from about 1 buyer in 10 stops "good"
MIN_GROUP = 3             # labelled reviews a star level needs before its share is used in the estimate
MIN_COVERAGE = 0.8       # share of all ratings the stars read must cover before a complaint gets a percentage
MIN_CRITICAL = 15         # critical (1-3 star) reviews read before a complaint can lower the verdict; fewer: the stars decide
BURST = 5                 # this many five-star reviews on one day (and 30% of the five-star ones read) is a burst
MIN_VERIFIED_KNOWN = 10   # reviews with a known verified-purchase flag before "few verified buyers" is said
TOP_LIKED = 3             # likes returned
TOP_COMPLAINTS = 10       # complaints returned, most common first
HEADLINES = {"good": "Mostly good", "mixed": "Mixed reviews", "poor": "Poor reviews",
             "not_enough_reviews": "Not enough reviews yet"}
ASPECT_WORDS = {"build_quality": "build quality", "durability": "how long it lasts", "performance": "how well it works",
                "value": "value for money", "as_described": "matches the listing", "size_fit": "size and fit",
                "ease_of_use": "ease of use", "delivery_packaging": "delivery and packaging",
                "seller_service": "seller and service", "other": "other"}


def _num(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        found = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
        return float(found.group()) if found else None
    return None


def _iso(value) -> str | None:
    try:
        return date.fromisoformat(str(value or "")[:10]).isoformat()
    except ValueError:
        return None


def rating_summary(raw) -> dict | None:
    """The page's star summary: average, count, and the share of ratings per star (only if all five add up)."""
    if not isinstance(raw, dict):
        return None
    average, count = _num(raw.get("average")), _num(raw.get("count"))
    dist = raw.get("distribution") if isinstance(raw.get("distribution"), dict) else {}
    values = {star: _num(dist.get(str(star), dist.get(star))) for star in range(1, 6)}
    total = sum(v for v in values.values() if v is not None)
    shares = ({star: v / total for star, v in values.items()}
              if all(v is not None and v >= 0 for v in values.values()) and 90 <= total <= 110 else None)
    summary = {"average": average if average and 0 < average <= 5 else None,
               "count": int(count) if count and count >= 1 else None, "shares": shares}
    return summary if summary["count"] or shares else None


def _rating(review: dict) -> float | None:
    value = _num(review.get("rating"))
    return value if value and 1 <= value <= 5 else None


def _mentions(review: dict, label: dict, aspect: str, sentiment: str) -> bool:
    return any(a.get("aspect") == aspect and a.get("sentiment") == sentiment for a in label.get("aspects") or [])


def _snippet(text: str, limit: int = 140) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


# Words that say how bad or good, not what: ignored when deciding whether two phrases are the same complaint.
GENERIC = {"poor", "bad", "good", "great", "quality", "issue", "issues", "problem", "problems", "not", "doesn", "very",
           "after", "working", "works", "work", "stopped", "too", "the", "and", "for", "with", "that", "this", "than",
           "does", "did", "was", "are", "has", "have", "can", "could", "only", "more", "less", "really", "nice",
           "best", "worst", "excellent", "amazing", "average", "decent", "okay", "fine"}


def _tokens(phrase: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", phrase.lower()) if w not in GENERIC}


def _parts(phrase: str) -> list[str]:
    """A phrase naming two things ("poor network and seems used") counts as two complaints."""
    return [p.strip() for p in re.split(r"\s+(?:and|&)\s+|\s*[,;/]\s*", phrase) if p.strip()]


def _clusters(labelled: list[tuple[dict, dict]], sentiment: str) -> list[dict]:
    """One cluster per thing buyers say, not per category: phrases that share a content word ("sound quality poor",
    "poor sound") are one cluster, but "battery dies fast" is not "sound quality poor" even though Gemini files both
    under "performance". A review joins the cluster of each thing its phrase names. Clusters are never merged, so two
    different complaints in one review's phrase cannot chain into one."""
    field = "problem" if sentiment == "neg" else "liked"
    clusters: list[dict] = []
    for review, lab in labelled:
        aspects = [a["aspect"] for a in lab.get("aspects") or [] if a.get("sentiment") == sentiment]
        if not aspects:
            continue
        parts = _parts((lab.get(field) or "").strip().lower()) or [""]
        for part in parts:
            tokens = _tokens(part)
            if not part or not tokens:  # no specific words: the cluster is the category itself
                part, tokens = ASPECT_WORDS[aspects[0]], {f"aspect:{aspects[0]}"}
            home = max((c for c in clusters if c["tokens"] & tokens), key=lambda c: len(c["tokens"] & tokens), default=None)
            if home is None:
                home = {"tokens": set(), "members": [], "phrases": Counter(), "aspects": Counter()}
                clusters.append(home)
            home["tokens"] |= tokens
            if all(r["id"] != review["id"] for r, _ in home["members"]):
                home["members"].append((review, lab))
            home["phrases"][part] += 1
            home["aspects"][aspects[0]] += 1
    return clusters


def _estimate(labelled: list[tuple[dict, dict]], shares: dict | None, members: list[tuple[dict, dict]]) -> float | None:
    """Share of all buyers (0-1) in this cluster: per star, its rate among that star's reviews times that star's
    share of all ratings, summed. None unless the stars with enough reviews read cover at least 80% of all ratings:
    leaving out a star and re-weighting the rest would lean the estimate towards the stars that were read."""
    if not shares:
        return None
    ids = {r["id"] for r, _ in members}
    total = used = 0.0
    for star in range(1, 6):
        group = [r for r, _ in labelled if _rating(r) and round(_rating(r)) == star]
        if len(group) < MIN_GROUP or not shares[star]:
            continue
        total += shares[star] * sum(r["id"] in ids for r in group) / len(group)
        used += shares[star]
    return total if used >= MIN_COVERAGE else None


def themes(labelled: list[tuple[dict, dict]], sentiment: str, shares: dict | None) -> list[dict]:
    """What buyers liked (pos) or complained about (neg), one entry per thing they say, most common first."""
    out = []
    for cluster in _clusters(labelled, sentiment):
        members = cluster["members"]
        phrase = cluster["phrases"].most_common(1)[0][0]
        estimate = _estimate(labelled, shares, members)
        example = next((r for r, lab in members if (lab.get("problem" if sentiment == "neg" else "liked") or "")
                        .strip().lower() == phrase), members[0][0])
        out.append({"aspect": cluster["aspects"].most_common(1)[0][0], "phrase": phrase, "mentions": len(members),
                    "share_estimate": round(estimate, 3) if estimate is not None else None,
                    "evidence_ids": [r["evidence_id"] for r, _ in members if r.get("evidence_id")][:5],
                    "_tokens": cluster["tokens"],
                    **({"quote": _snippet(example.get("text")),
                        # every review behind this complaint, so a screen can show what was counted, with no second call
                        "reviews": [{"rating": _rating(r), "date": r.get("date"), "title": r.get("title"),
                                     "text": _snippet(r.get("text"), 500)}
                                    for r, _ in sorted(members, key=lambda m: _rating(m[0]) or 6)]}
                       if sentiment == "neg" else {})})
    return sorted(out, key=lambda t: (t["share_estimate"] or 0, t["mentions"]), reverse=True)


def _public(theme: dict) -> dict:
    return {k: v for k, v in theme.items() if k != "_tokens"}


def tidy(liked: list[dict], complaints: list[dict]) -> tuple[list[dict], list[dict]]:
    """A thing is never both a like and a complaint in one answer: a like that shares its subject with a complaint
    shown is dropped ("good sound" next to "sound quality poor" says nothing a shopper can use)."""
    shown = complaints[:TOP_COMPLAINTS]
    main = shown[:3]  # only the leading complaints push a like out, or ten complaints would leave no likes at all
    complaint_words = set().union(*(c["_tokens"] for c in main)) if main else set()
    liked = [t for t in liked if not (t["_tokens"] & complaint_words)][:TOP_LIKED]
    return [_public(t) for t in liked], [_public(t) for t in shown]


def trust_signals(raw_reviews: list) -> list[dict]:
    """Signs the reviews read may be inflated. Code only, from the reviews as the page showed them."""
    reviews = [r for r in raw_reviews if isinstance(r, dict) and (r.get("text") or "").strip()]
    flags = []
    five = [_iso(r.get("date")) for r in reviews if _rating(r) == 5 and _iso(r.get("date"))]
    if five:
        day, n = Counter(five).most_common(1)[0]
        if n >= BURST and n >= 0.3 * len(five):
            d = date.fromisoformat(day)
            flags.append({"kind": "same_day_burst", "detail": f"{n} five-star reviews were posted on {d.day} {d:%b %Y}"})
    openings = Counter(" ".join(words[:8]) for r in reviews
                       if len(words := re.findall(r"\w+", str(r.get("text")).lower())) >= 5)
    repeated = sum(n for n in openings.values() if n >= 2)
    if repeated >= 3:
        flags.append({"kind": "repeated_text", "detail": f"{repeated} reviews open with the same words"})
    known = [r["verified_purchase"] for r in reviews if isinstance(r.get("verified_purchase"), bool)]
    if len(known) >= MIN_VERIFIED_KNOWN and sum(known) / len(known) < 0.5:
        flags.append({"kind": "few_verified",
                      "detail": f"Only {sum(known)} of {len(known)} reviews read are from verified buyers"})
    return flags


def decide(summary: dict | None, reviews: list[dict], labels: dict[str, dict], flags: list[dict],
           listing_url: str | None = None) -> dict:
    """The verdict from the star summary, the labelled reviews and the trust flags. Code only."""
    rated = [r for r in reviews if _rating(r)]
    if summary and summary["shares"]:
        source, positive = "page_summary", summary["shares"][4] + summary["shares"][5]
    elif rated:  # no usable summary: the reviews read, which lean towards critical ones on Amazon
        source, positive = "reviews_read", sum(_rating(r) >= 4 for r in rated) / len(rated)
    else:
        source, positive = "none", None
    count = (summary or {}).get("count") or len(rated)
    average = (summary or {}).get("average") or (round(sum(map(_rating, rated)) / len(rated), 1) if rated else None)

    # Labels from before the quality fields existed have no "aspects": they count for safety only.
    labelled = [(r, labels[r["id"]]) for r in reviews if isinstance(labels.get(r["id"], {}).get("aspects"), list)]
    shares = summary["shares"] if summary else None
    all_complaints = themes(labelled, "neg", shares)
    liked, complaints = tidy(themes(labelled, "pos", shares), all_complaints)
    critical_read = sum(1 for r, _ in labelled if (_rating(r) or 5) <= 3)
    # A complaint only moves the verdict when enough unhappy reviews were read to judge its share; else the stars decide.
    top = max((c["share_estimate"] or 0 for c in complaints), default=0) if critical_read >= MIN_CRITICAL else 0

    if positive is None or count < MIN_RATINGS:
        verdict = "not_enough_reviews"
    elif positive < POOR_SHARE or (summary and summary["average"] and summary["average"] < POOR_AVERAGE):
        verdict = "poor"
    elif positive >= GOOD_SHARE and top < COMMON_COMPLAINT:
        verdict = "good"
    else:
        verdict = "mixed"

    # Why this verdict: the rule that decided it, in a line or two. Nothing else.
    pct = round(100 * positive) if positive is not None else None
    of = f"{count:,} ratings" if source == "page_summary" else f"the {len(rated)} reviews read"
    low_avg = bool(summary and summary["average"] and summary["average"] < POOR_AVERAGE)
    if verdict == "not_enough_reviews":
        reasons = [f"Only {count:,} rating{'' if count == 1 else 's'}: at least {MIN_RATINGS} are needed for a verdict"]
    elif verdict == "poor":
        reasons = ([f"Only {pct}% of {of} are 4 or 5 stars (poor is under {round(100 * POOR_SHARE)}%)"]
                   if positive < POOR_SHARE else []) + \
                  ([f"The average rating, {summary['average']}, is under {POOR_AVERAGE}"] if low_avg else [])
    elif verdict == "good":
        reasons = [f"{pct}% of {of} are 4 or 5 stars (good is {round(100 * GOOD_SHARE)}% or more) and no complaint is common"]
    elif positive < GOOD_SHARE:
        reasons = [f"{pct}% of {of} are 4 or 5 stars: not enough for good ({round(100 * GOOD_SHARE)}%), not low enough for poor"]
    else:
        reasons = [f"{pct}% of {of} are 4 or 5 stars, but about {round(100 * top)}% of buyers hit \"{complaints[0]['phrase']}\""]
    if source == "reviews_read":
        reasons.append("The page's star summary could not be read, so this uses only the reviews read")

    if verdict == "not_enough_reviews" or flags or source != "page_summary" or critical_read < MIN_CRITICAL:
        confidence = "low"
    elif count >= 100:
        confidence = "high"
    else:
        confidence = "medium"
    return {
        "listing_url": listing_url,
        "verdict": verdict,
        "headline": HEADLINES[verdict],
        "confidence": confidence,
        "rating": {"average": average, "count": count or None, "source": source,
                   "positive_share": round(positive, 3) if positive is not None else None},
        "reviews_read": len(reviews),
        "reviews_labelled": len(labelled),
        "liked": liked,
        "complaints": complaints,
        "trust": {"may_be_inflated": bool(flags), "flags": flags},
        "reasons": reasons,
        "policy_version": POLICY,
        "label": LABEL,
    }


def review_verdict(listing: dict) -> dict:
    """The reviews are stored under the listing's key, the same as the safety check's, so labels are shared."""
    key = page_safety.listing_key(listing)
    incoming = page_safety.page_reviews(listing)
    if incoming:
        safety.add_reviews(key, incoming)
    stored = safety.product_reviews(key)  # this visit's reviews plus any seen on earlier visits to the same page
    view = f"{trust.listing_brand(listing)} ({listing.get('title') or 'product'})".strip()
    labels = safety.label_reviews(view, stored) if stored else {}
    return decide(rating_summary(listing.get("rating_summary")), stored, labels,
                  trust_signals(listing.get("reviews") or []), listing.get("url"))
