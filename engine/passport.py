"""Product passport answers: identity, history, safer alternatives, reports and bench results (M7).

    product(product_id)       -> Product       (contract: GET /v1/products/{id})
    history(product_id)       -> History       (contract: GET /v1/products/{id}/history)
    alternatives(product_id)  -> Alternatives  (contract: GET /v1/products/{id}/alternatives)
    create_report(body, ref)  -> Report        (contract: POST /v1/reports)
    bench_results()           -> BenchResults  (contract: GET /v1/bench/results)

Everything here reads what the engine already stored; no Gemini calls, so these answer fast.
"""
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from psycopg.types.json import Jsonb

from engine import radar, store, trust
from engine.rules import attribute_conflicts
from engine.safety import product_reviews, stored_labels

BENCH_RESULTS = Path(__file__).resolve().parents[1] / "bench" / "results.json"
TWIN_TYPES = ("exact_model", "rebranded_equivalent")
RELATIONSHIP_WORDS = {"exact_model": "exact same model", "rebranded_equivalent": "possible rebrand",
                      "model_variant": "model variant", "shared_component": "shares a part",
                      "visually_similar": "look-alike"}


def _fingerprint(product_id: str) -> dict:
    fp = store.latest_fingerprint(product_id)
    if fp is None:
        raise KeyError(product_id)
    return fp


def _listing_offer(product_id: str, brand: str) -> dict | None:
    """The listing to point a shopper at: an authorised seller first, then the cheapest."""
    offers = []
    for row in store.product_listings(product_id):
        raw = row["raw"] or {}
        ok = trust.authorised(brand, raw.get("seller"), row["url"]) or row["marketplace"] == "demo"
        offers.append({"url": row["url"], "seller": raw.get("seller"), "seller_authorised": ok,
                       "price": raw.get("price"), "currency": raw.get("currency"), "title": row["title"]})
    offers.sort(key=lambda o: (not o["seller_authorised"], o["price"] is None, o["price"] or 0))
    return offers[0] if offers else None


# ---------- product ----------

def product(product_id: str) -> dict:
    fp = _fingerprint(product_id)
    row = store.conn().execute("SELECT identity_status FROM products WHERE id = %s", (product_id,)).fetchone()
    listings = store.product_listings(product_id)
    images = list(dict.fromkeys(u for r in listings for u in (r["raw"] or {}).get("image_urls") or []))
    return {
        "product_id": product_id,
        "category": fp["category"],
        "brand": fp["brand"],
        "model": fp["model"],
        "gtin": fp["gtin"],
        "attributes": fp["attributes"],
        "visual_features": fp.get("view", {}).get("visual_features", {}),
        "identity_version": fp["version"],
        "verification_status": row["identity_status"] if row else "provisional",
        "image_urls": images[:8],
        "listings": [{"listing_id": r["id"], "marketplace": r["marketplace"], "url": r["url"], "title": r["title"]}
                     for r in listings],
    }


# ---------- history (Safety Passport) ----------

def _recalls(product_id: str) -> list[dict]:
    rows = store.conn().execute(
        """SELECT DISTINCT ON (r.id) r.id, r.authority, r.notice_date, r.title, r.url, rp.match_class
           FROM recall_products rp JOIN recalls r ON r.id = rp.recall_id WHERE rp.product_id = %s
           ORDER BY r.id, rp.match_class = 'exact_model' DESC""", (product_id,)).fetchall()
    return [{"recall_id": r["id"], "authority": r["authority"], "notice_date": r["notice_date"].isoformat()
             if r["notice_date"] else None, "title": r["title"], "url": r["url"],
             "match": "matches a recall" if r["match_class"] == "exact_model" else "possible match, under review"}
            for r in sorted(rows, key=lambda r: r["notice_date"] or datetime.min.date())]


def _relationship_events(product_id: str) -> list[dict]:
    rows = store.conn().execute(
        """SELECT entity_id, change_type, actor, before, after, at FROM audit_events
           WHERE entity_type = 'relationship' AND entity_id LIKE %s ORDER BY at""",
        (product_id + "->%",)).fetchall()
    events, last = [], {}
    for r in rows:
        target, after, before = r["entity_id"].split("->", 1)[1], r["after"] or {}, r["before"] or {}
        state = (after.get("relationship"), after.get("status"))
        if last.get(target) == state:  # re-checked, same conclusion: not a change
            continue
        last[target] = state
        words = f"{RELATIONSHIP_WORDS.get(state[0], state[0])} ({state[1]})"
        if r["change_type"] == "create":
            summary = f"{target} linked as {words}"
        else:
            summary = f"{target} changed from {RELATIONSHIP_WORDS.get(before.get('relationship'), '?')} to {words}"
        events.append({"at": r["at"], "change_type": "relationship_changed", "summary": summary,
                       "actor": "analyst" if not r["actor"].startswith("engine.") else "system"})
    return events


def _hazard_events(product_id: str) -> list[dict]:
    rows = store.conn().execute(
        """SELECT a.entity_id, a.after, a.at FROM audit_events a JOIN hazard_signals h ON h.id = a.entity_id
           WHERE a.entity_type = 'hazard_signal' AND h.product_id = %s ORDER BY a.at""", (product_id,)).fetchall()
    events, last = [], {}
    for r in rows:
        f = r["after"] or {}
        state = (f.get("severity"), f.get("independent_reports"), f.get("with_photos"))
        if last.get(r["entity_id"]) == state:
            continue
        first = r["entity_id"] not in last
        last[r["entity_id"]] = state
        photos = f" ({f['with_photos']} with photos)" if f.get("with_photos") else ""
        verb = "First" if first else "Now"
        events.append({"at": r["at"], "change_type": "hazard_signal", "actor": "system",
                       "summary": f"{verb} {f.get('independent_reports')} {f.get('hazard_type', '').replace('_', '/')} "
                                  f"report(s){photos}, severity {f.get('severity')}: {f.get('mechanism')}",
                       "evidence_ids": (f.get("evidence_ids") or [])[:5]})
    return events


def history(product_id: str) -> dict:
    fp = _fingerprint(product_id)
    created = store.conn().execute("SELECT created_at FROM products WHERE id = %s", (product_id,)).fetchone()
    events = [{"at": created["created_at"], "change_type": "identity_created", "actor": "system",
               "summary": f"First seen and identified as {fp['brand']} {fp['model']}".strip()}]
    events += _relationship_events(product_id) + _hazard_events(product_id)
    reports = store.conn().execute(
        "SELECT id, evidence_ids FROM reports WHERE product_id = %s", (product_id,)).fetchall()
    for r in reports:
        at = store.conn().execute("SELECT min(at) AS at FROM audit_events WHERE entity_id = %s", (r["id"],)).fetchone()
        events.append({"at": at["at"] or created["created_at"], "change_type": "report_received", "actor": "consumer",
                       "summary": "Problem report received (personal details masked)",
                       "evidence_ids": r["evidence_ids"] or []})
    events.sort(key=lambda e: e["at"])
    for n, event in enumerate(events, 1):
        event["version"] = n
        event["at"] = event["at"].astimezone(UTC).isoformat().replace("+00:00", "Z")
    return {"product_id": product_id, "events": events, "recalls": _recalls(product_id)}


# ---------- safer alternatives ----------

def hazard_reports(product_id: str) -> tuple[int, int]:
    """(first-hand hazard reports, reviews read) from stored Radar labels. No new Gemini calls."""
    reviews = product_reviews(product_id)
    labels = stored_labels(reviews)
    signals = store.conn().execute(
        "SELECT count(*) AS n FROM hazard_signals WHERE product_id = %s AND status = 'under_review'",
        (product_id,)).fetchone()["n"]
    return sum(radar.counts(label) for label in labels.values()) + signals, len(labels)


def _recalled(product_id: str) -> bool:
    return bool(store.conn().execute(
        "SELECT 1 FROM recall_products WHERE product_id = %s AND match_class = 'exact_model' LIMIT 1",
        (product_id,)).fetchone())


def _marks_ok(product_id: str) -> bool | None:
    rows = store.conn().execute(
        "SELECT validation_status FROM certifications WHERE product_id = %s", (product_id,)).fetchall()
    return None if not rows else all(r["validation_status"] != "mismatch" for r in rows)


def reviewed_neighbours(product_id: str, k: int = 20) -> list[str]:
    """Same-category products with at least radar.MIN_REVIEWS Radar-labelled reviews, closest first."""
    rows = store.conn().execute(
        """WITH latest AS (
               SELECT DISTINCT ON (product_id) product_id, text_vector, attributes_json->>'category' AS category
               FROM product_fingerprints ORDER BY product_id, version DESC),
           reviewed AS (
               SELECT c.claim_id AS product_id FROM evidence_claims c
               JOIN evidence l ON l.source_type = 'radar_label' AND l.source_ref = c.evidence_id
               WHERE c.claim_type = 'review_of' GROUP BY c.claim_id HAVING count(*) >= %s)
           SELECT o.product_id FROM latest q
           JOIN latest o ON o.category = q.category AND o.product_id <> q.product_id
           JOIN reviewed r ON r.product_id = o.product_id
           WHERE q.product_id = %s ORDER BY o.text_vector <=> q.text_vector LIMIT %s""",
        (radar.MIN_REVIEWS, product_id, k)).fetchall()
    return [r["product_id"] for r in rows]


def alternatives(product_id: str, limit: int = 3) -> dict:
    """Twins (same hardware) only when this product is clean: a twin shares its hazards and recalls.
    Otherwise similar products in the same category with no recall and no hazard reports in at least
    radar.MIN_REVIEWS reviews read. Empty when nothing meets that bar."""
    fp = _fingerprint(product_id)
    reports, _ = hazard_reports(product_id)
    risky = _recalled(product_id) or reports > 0
    twins = {r["target_id"]: r["relationship_type"] for r in store.latest_relationships(product_id)
             if r["relationship_type"] in TWIN_TYPES and r["status"] != "rejected"}
    if risky:
        candidates = [(p, "similar_product") for p in reviewed_neighbours(product_id) if p not in twins]
    else:
        candidates = [(p, rel) for p, rel in twins.items()
                      if rel == "exact_model" or store.conn().execute(
                          """SELECT 1 FROM product_relationships WHERE source_id = %s AND target_id = %s
                             AND status = 'verified' LIMIT 1""", (product_id, p)).fetchone()]
    out = []
    for candidate, relationship in candidates:
        other = store.latest_fingerprint(candidate)
        if not other or _recalled(candidate) or (other["brand_norm"] and other["brand_norm"] == fp["brand_norm"]
                                                 and other["model_norm"] == fp["model_norm"] and risky):
            continue
        n_reports, n_read = hazard_reports(candidate)
        marks_ok = _marks_ok(candidate)
        offer = _listing_offer(candidate, other["brand"])
        # "No hazard reports" only means something once enough reviews were read.
        if n_reports or n_read < radar.MIN_REVIEWS or marks_ok is False or not offer:
            continue
        differs = attribute_conflicts(fp["attributes"], other["attributes"])
        why = ("same product, genuine" if relationship == "exact_model" else
               "verified same hardware under another brand" if relationship in TWIN_TYPES else
               f"similar {fp['category'].replace('_', ' ') or 'product'}, no official recall")
        evidence = f"0 hazard reports in {n_read} reviews read"
        out.append({
            "product_id": candidate,
            "relationship": relationship,
            "brand": other["brand"],
            "model": other["model"],
            "seller": offer["seller"],
            "seller_authorised": offer["seller_authorised"],
            "price": offer["price"],
            "currency": offer["currency"],
            "hazard_reports": 0,
            "reviews_read": n_read,
            "certifications_valid": marks_ok,
            "differences": differs,
            "url": offer["url"],
            "reason": f"{why}; {evidence}" + ("; authorised seller" if offer["seller_authorised"] else ""),
        })
    # Closest match first (same key specs), then authorised seller, then most reviews read.
    out.sort(key=lambda a: (len(a["differences"]), not a["seller_authorised"], -a["reviews_read"]))
    return {
        "product_id": product_id,
        "basis": "this product has hazard reports or a recall, so its twins are excluded" if risky else
                 "genuine twins of this product",
        "alternatives": out[:limit],
    }


# ---------- reports ----------

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,}\d")
NAME = re.compile(r"\b(my name is|i am|i'm|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)")


def mask_pii(text: str) -> str:
    masked = EMAIL.sub("[email hidden]", text)
    masked = PHONE.sub("[phone hidden]", masked)
    return NAME.sub(lambda m: f"{m.group(1)} [name hidden]", masked)


def create_report(body: dict, reporter: str | None = None) -> dict:
    product_id = body["product_id"]
    _fingerprint(product_id)
    description = mask_pii(body.get("description") or "")
    photos = [u for u in body.get("photo_urls") or [] if isinstance(u, str)][:10]
    evidence_id = store.add_evidence("report", product_id, {
        "product_id": product_id, "description": description, "photo_urls": photos,
        "received_at": datetime.now(UTC).isoformat()})
    store.conn().execute("UPDATE evidence SET pii_status = 'masked' WHERE id = %s", (evidence_id,))
    report_id = store.short_id("SS-R-", evidence_id)
    reporter_ref = hashlib.sha256(reporter.encode()).hexdigest()[:16] if reporter else None
    store.conn().execute(
        """INSERT INTO reports (id, reporter_ref, product_id, description, evidence_ids) VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (id) DO NOTHING""", (report_id, reporter_ref, product_id, description, [evidence_id]))
    store.conn().execute(
        """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, after)
           VALUES (%s, 'report', 'create', 'consumer', %s)""",
        (report_id, Jsonb({"product_id": product_id, "evidence_ids": [evidence_id]})))
    return {"report_id": report_id, "status": "received", "pii_masked": True, "product_id": product_id,
            "evidence_ids": [evidence_id]}


# ---------- bench ----------

def bench_results() -> dict:
    return json.loads(BENCH_RESULTS.read_text())
