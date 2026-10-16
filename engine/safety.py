"""Safety answer for GET /v1/products/{id}/safety: Safety Radar findings + official status, verdict set by code.

Reviews are evidence (reviewer ids hashed). Each review's Gemini label is stored once, so a product is only
re-read when new reviews arrive. Recall and safety-mark checks come from M5 (engine.recalls, engine.marks).

Since plan v2.2 the answer also carries the evidence-verification result for the product's own market (the shop it
is listed on): outcome, safety_concern, evidence_strength, identity_confidence, coverage, as_of and policy_version,
from engine.investigation. The verdict colour then follows that policy: red only for a recall in the product's own
market, so a US recall no longer shows red on an Amazon.in listing. Existing fields stay as they were.
"""
import hashlib
import json
import logging
from datetime import UTC, datetime

from psycopg.types.json import Jsonb

from engine import marks, radar, recalls, store

LABEL = "AI finding - not a regulatory determination"
log = logging.getLogger(__name__)


def market_of_product(product_id: str) -> str | None:
    """The market a stored product is sold in, from its listings' shop addresses (amazon.in -> IN)."""
    from engine import region_policy
    for row in store.product_listings(product_id):
        code = region_policy.market_of(row.get("url"))
        if code:
            return code
        if (row.get("marketplace") or "").startswith("amazon.com"):
            return "US"
    return None


def assess_product(product_id: str, fp: dict, ai_findings: list[dict], reviews_checked: int) -> dict | None:
    """The v2.2 assessment for this product in its own market. None if the sources could not be consulted at all."""
    try:
        from engine import investigation
        market = market_of_product(product_id)
        product = {"product_id": product_id, "brand": fp.get("brand"), "model": fp.get("model"), "gtin": fp.get("gtin"),
                   "category": fp.get("category"), "title": (fp.get("view") or {}).get("title"), "market": market}
        hazards, _groups, texts = investigation.hazard_groups(ai_findings)
        collected = investigation.collect(product, market, review_texts=texts)
        return investigation.adjudicate(collected, hazards, reviews_checked)
    except Exception as error:  # noqa: BLE001  the radar answer stands without it
        log.warning("assessment failed for %s: %s", product_id, type(error).__name__)
        return None


def colour(decision: dict, radar_verdict: str) -> str:
    """The verdict word for the screens: red only for a confirmed local recall; green only when the radar is green."""
    if decision["outcome"] == "no_matching_notice_found":
        return radar_verdict if radar_verdict in ("green", "amber") else "not_enough_evidence"
    if decision["outcome"] == "insufficient_evidence":
        return radar_verdict if radar_verdict == "amber" else "not_enough_evidence"
    return decision["colour"]


def add_reviews(product_id: str, reviews: list[dict]) -> list[str]:
    """Store reviews as evidence linked to the product. Returns evidence ids (duplicates are stored once)."""
    ids = []
    for review in reviews:
        user = review.get("user_id")
        content = {"rid": radar.review_id(review), "title": review.get("title"), "text": review.get("text"),
                   "rating": review.get("rating"), "date": radar.review_date(review).isoformat(),
                   "images": radar.image_urls(review), "verified_purchase": review.get("verified_purchase"),
                   "reviewer": hashlib.sha256(user.encode()).hexdigest()[:16] if user else None}
        evidence_id = store.add_evidence("review", f"{product_id}:{content['rid']}", content)
        store.conn().execute(
            """INSERT INTO evidence_claims (evidence_id, claim_type, claim_id)
               SELECT %s, 'review_of', %s WHERE NOT EXISTS (
                   SELECT 1 FROM evidence_claims WHERE evidence_id = %s AND claim_id = %s)""",
            (evidence_id, product_id, evidence_id, product_id))
        store.conn().execute("UPDATE evidence SET observed_at = %s WHERE id = %s", (content["date"], evidence_id))
        ids.append(evidence_id)
    return ids


def product_reviews(product_id: str) -> list[dict]:
    rows = store.conn().execute(
        """SELECT e.id, e.content FROM evidence e JOIN evidence_claims c ON c.evidence_id = e.id
           WHERE c.claim_type = 'review_of' AND c.claim_id = %s AND e.source_type = 'review'
           ORDER BY e.observed_at""", (product_id,)).fetchall()
    return [{**json.loads(r["content"]), "id": json.loads(r["content"])["rid"], "evidence_id": r["id"]} for r in rows]


def stored_labels(reviews: list[dict]) -> dict[str, dict]:
    rows = store.conn().execute(
        "SELECT source_ref, content FROM evidence WHERE source_type = 'radar_label' AND source_ref = ANY(%s)",
        ([r["evidence_id"] for r in reviews],)).fetchall()
    by_evidence = {r["source_ref"]: json.loads(r["content"]) for r in rows}
    return {r["id"]: by_evidence[r["evidence_id"]] for r in reviews if r["evidence_id"] in by_evidence}


def label_reviews(product_view: str, reviews: list[dict]) -> dict[str, dict]:
    labels = stored_labels(reviews)
    todo = [r for r in reviews if r["id"] not in labels]
    if todo:
        fresh = radar.classify(product_view, todo, timeout_s=60)
        for review in todo:
            if review["id"] in fresh:
                # The review's id is part of the content: identical labels must not collapse into one row.
                store.add_evidence("radar_label", review["evidence_id"],
                                   {**fresh[review["id"]], "review_evidence_id": review["evidence_id"]})
        labels.update(fresh)
    return labels


def check_photos(view: str, reviews: list[dict], labels: dict[str, dict], limit: int = 5) -> dict[str, dict]:
    """Gemini vision on photos attached to hazard reports (most severe first), each photo checked once ever."""
    urls = [u for r in sorted(reviews, key=lambda r: radar.SEVERITY_ORDER.index(labels.get(r["id"], {}).get("severity")
                                                                                 or "low"), reverse=True)
            if radar.counts(labels.get(r["id"], {})) for u in radar.image_urls(r)]
    results: dict[str, dict] = {}
    for url in urls[:limit]:
        cached = store.conn().execute(
            "SELECT content FROM evidence WHERE source_type = 'photo_check' AND source_ref = %s LIMIT 1", (url,)
        ).fetchone()
        if cached:
            results[url] = json.loads(cached["content"])
            continue
        try:
            results[url] = radar.check_photo(view, url)
        except Exception:  # noqa: BLE001, S112  unreachable image or model error: the photo just does not count
            continue
        store.add_evidence("photo_check", url, results[url])
    return results


def official_status(product_id: str) -> dict:
    """Only exact-model recall links make a product recalled; family-level and rebrand links are under review."""
    links = recalls.link(product_id) + store.conn().execute(  # plus links stored by the catalog loader
        "SELECT recall_id, match_class FROM recall_products WHERE product_id = %s", (product_id,)).fetchall()
    exact = sorted({x["recall_id"] for x in links if x["match_class"] == "exact_model"})
    review = sorted({x["recall_id"] for x in links if x["match_class"] == "needs_review"} - set(exact))
    return {"recalled": bool(exact), "checked": recalls.authorities(), "recall_ids": exact, "recall_ids_under_review": review}


def save_signals(product_id: str, ai_findings: list[dict]) -> None:
    for finding in ai_findings:
        signal_id = store.short_id("HZ-", product_id, finding["hazard_type"])
        store.conn().execute(
            """INSERT INTO hazard_signals (id, product_id, hazard_type, mechanism, severity, status, first_seen, last_seen)
               VALUES (%s, %s, %s, %s, %s, 'under_review', %s, now()::date)
               ON CONFLICT (id) DO UPDATE SET mechanism = EXCLUDED.mechanism, severity = EXCLUDED.severity,
                                              last_seen = EXCLUDED.last_seen""",
            (signal_id, product_id, finding["hazard_type"], finding["mechanism"], finding["severity"],
             finding["first_seen"]))
        store.conn().execute(
            """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, after)
               VALUES (%s, 'hazard_signal', 'update', 'engine.radar', %s)""", (signal_id, Jsonb(finding)))


def safety(product_id: str, assess: bool = True) -> dict:
    """assess=False: the radar and stored recall links only, as before plan v2.2 (the investigation uses this)."""
    fp = store.latest_fingerprint(product_id)
    if fp is None:
        raise KeyError(product_id)
    reviews = product_reviews(product_id)
    view = f"{fp['brand']} {fp['model']} ({fp['category']})"
    labels = label_reviews(view, reviews)
    review_evidence = {r["id"]: r["evidence_id"] for r in reviews}
    photos = check_photos(view, reviews, labels)
    ai_findings = radar.findings(reviews, labels, photos)
    for finding in ai_findings:  # point at stored evidence rows, not internal review ids
        finding["evidence_ids"] = [review_evidence[e.removeprefix("REV-")] for e in finding["evidence_ids"]]
    save_signals(product_id, ai_findings)
    status = official_status(product_id)
    radar_verdict = radar.verdict(status["recalled"], len(reviews), ai_findings)
    answer = {
        "product_id": product_id,
        "verdict": radar_verdict,
        "official_status": status,
        "ai_findings": ai_findings,
        "certifications": marks.certifications(product_id)["checks"],
        "reviews_checked": len(reviews),
        "label": LABEL,
    }
    decision = assess_product(product_id, fp, ai_findings, len(reviews)) if assess else None
    if decision:
        answer.update({
            "verdict": colour(decision, radar.verdict(False, len(reviews), ai_findings)),
            "outcome": decision["outcome"], "headline": decision["headline"],
            "safety_concern": decision["safety_concern"], "evidence_strength": decision["evidence_strength"],
            "identity_confidence": decision["identity_confidence"], "coverage": decision["coverage"],
            "limitations": decision["limitations"], "what_would_change": decision["what_would_change"],
            "lead_record": decision["lead_record"], "review_required": decision["review_required"],
            "source_mode": decision["source_mode"], "policy_version": decision["policy_version"],
            "plain": decision.get("plain"),
            "as_of": datetime.now(UTC).isoformat(timespec="seconds"),
        })
    return answer
