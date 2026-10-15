"""M1/M3: load a real product catalog so identify, find copies, price and photo checks work on real products.

    cd engine && PYTHONPATH=.. uv run python ../data/load_catalog.py            # local database
    (export DATABASE_URL=... for Cloud SQL through cloud-sql-proxy; embeddings are cached, so it is cheap)

Sources:
- raw/amazon_catalog/catalog_*.jsonl   everyday chargers, power banks, heaters, cords, TVs (data/vm_catalog_scan.sh)
- raw/amazon_meta + recall_listing_matches.jsonl   listings that sold recalled products, linked to their recall
  ("exact_model" only when the model number matches the notice, otherwise "needs_review")
- raw/india_catalog.jsonl   Amazon.in and Flipkart product pages (data/extract_catalog_pages.py)
Accessories (mounts, cases, cables "for" a product) are left out.
"""
import glob
import hashlib
import json
from pathlib import Path

from psycopg.types.json import Jsonb

from engine import gemini, identity, store
from engine.normalize import brand_blind_text, category_of

RAW = Path(__file__).parent / "raw"
VECTORS = RAW / "catalog_vectors.jsonl"
def from_amazon(row: dict, category: str | None = None) -> dict | None:
    """category given = keep it as is (recalled listings); otherwise from the title, accessories dropped."""
    category = category or category_of(row.get("title"))
    if not category:
        return None
    details = row.get("details") or {}
    images = [i.get("hi_res") or i.get("large") for i in row.get("images") or [] if i.get("hi_res") or i.get("large")]
    price = row.get("price")
    try:
        price = float(str(price).replace("$", "").replace(",", "")) if price not in (None, "None", "") else None
    except ValueError:
        price = None
    asin = row["parent_asin"]
    return {
        "product_id": f"SS-P-AMZ-{asin}", "listing_id": f"amazon:{asin}", "marketplace": "amazon.com",
        "url": f"https://www.amazon.com/dp/{asin}", "title": row.get("title"),
        "brand": details.get("Brand") or details.get("Brand Name") or row.get("store") or "",
        "model": details.get("Item model number") or details.get("Part Number") or "",
        "category": category, "description": " ".join((row.get("features") or [])[:2])[:500],
        "price": price, "currency": "USD", "seller": row.get("store"), "image_urls": images[:4],
        "rating_number": int(row.get("rating_number") or 0),
    }


def from_india(row: dict) -> dict | None:
    category = row.get("category") or category_of(row.get("title"))
    if not category or not row.get("title"):
        return None
    key = hashlib.sha1(row["url"].encode()).hexdigest()[:10].upper()
    return {
        "product_id": f"SS-P-IN-{key}", "listing_id": f"in:{key}", "marketplace": row.get("marketplace"),
        "url": row["url"], "title": row["title"], "brand": row.get("brand") or "", "model": row.get("model") or "",
        "category": category, "description": row.get("description") or "", "price": row.get("price") or None,
        "currency": "INR", "seller": row.get("seller"), "image_urls": (row.get("image_urls") or [])[:4],
        "attributes": row.get("attributes") or {},
    }


def load_sources() -> tuple[list[dict], list[tuple[str, str, str]]]:
    items: dict[str, dict] = {}
    for path in sorted(glob.glob(str(RAW / "amazon_catalog" / "catalog_*.jsonl"))):
        for line in Path(path).read_text().splitlines():
            item = from_amazon(json.loads(line))
            if item:
                items[item["product_id"]] = item
    links = []
    matches = RAW / "recall_listing_matches.jsonl"
    if matches.exists():
        recalled = {}
        for line in matches.read_text().splitlines():
            row = json.loads(line)
            if row["label"] == "recalled_model":
                recalled[row["asin"]] = row
        for path in sorted(glob.glob(str(RAW / "amazon_meta" / "meta_*.jsonl"))):
            for line in Path(path).read_text().splitlines():
                row = json.loads(line)
                hit = recalled.get(row["parent_asin"])
                if not hit:
                    continue
                item = from_amazon(row, category_of(row.get("title")) or "recalled_product")
                items[item["product_id"]] = item
                links.append((hit["recall_id"], item["product_id"],
                              "exact_model" if hit.get("model_number_match") else "needs_review"))
    india = RAW / "india_catalog.jsonl"
    if india.exists():
        for line in india.read_text().splitlines():
            item = from_india(json.loads(line))
            if item:
                items[item["product_id"]] = item
    return list(items.values()), links


def vectors_for(rows: list[tuple[str, str]]) -> dict[str, list[float]]:
    """Embeddings by text hash, cached on disk so loading a second database costs nothing."""
    cache: dict[str, list[float]] = {}
    if VECTORS.exists():
        for line in VECTORS.read_text().splitlines():
            entry = json.loads(line)
            cache[entry["h"]] = entry["v"]
    todo = list(dict.fromkeys(h for h, _ in rows if h not in cache))
    texts = dict(rows)
    for start in range(0, len(todo), 250):
        chunk = todo[start:start + 250]
        new = gemini.embed([texts[h] for h in chunk])
        with VECTORS.open("a") as f:
            f.writelines(json.dumps({"h": h, "v": [round(x, 6) for x in v]}) + "\n" for h, v in zip(chunk, new))
        cache.update(zip(chunk, new))
        print(f"  embedded {min(start + 250, len(todo))}/{len(todo)}", flush=True)
    return cache


def bulk(sql: str, rows: list[tuple], chunk: int = 500) -> None:
    """executemany in chunks: one 29,000-row pipeline is too much for the smallest Cloud SQL tier (it dropped the
    connection, 13 Oct). Each chunk retries once on a fresh connection; inserts are idempotent, so reruns are safe."""
    import psycopg

    for start in range(0, len(rows), chunk):
        for attempt in (1, 2):
            try:
                with store.conn().cursor() as cur:
                    cur.executemany(sql, rows[start:start + chunk])
                break
            except psycopg.OperationalError:
                if attempt == 2:
                    raise
        if (start // chunk) % 10 == 9:
            print(f"    {start + chunk}/{len(rows)}", flush=True)


def load_reviews(product_ids: set[str]) -> None:
    """Real Amazon reviews of loaded products (the backtest's recalled listings and controls) as evidence, with
    Safety Radar labels: reused from the backtest cache, labelled now if they were not, or "no hazard" when the
    review has no hazard words at all (keyword pre-filter)."""
    from bench import backtest as bt

    reviews = []
    for path in sorted((RAW / "amazon_reviews").glob("reviews_*.jsonl")):
        for line in path.read_text().splitlines():
            review = json.loads(line)
            if f"SS-P-AMZ-{review['parent_asin']}" in product_ids:
                reviews.append(review)
    labels: dict[str, dict] = {}
    for cached in (RAW / "bench_cache").glob("radar-*.json"):
        labels.update(json.loads(cached.read_text()))
    hazard_words = [r for r in reviews if bt.PREFILTER.search(f"{r.get('title') or ''} {r.get('text') or ''}")]
    todo = [r for r in hazard_words if bt.rid(r) not in labels]
    print(f"{len(reviews)} reviews; {len(hazard_words)} with hazard words, {len(todo)} still to label")
    by_asin: dict[str, list[dict]] = {}
    for review in todo:
        by_asin.setdefault(review["parent_asin"], []).append(review)
    jobs = [bt.radar_job(f"Amazon listing {asin}", batch[i:i + 15])
            for asin, batch in by_asin.items() for i in range(0, len(batch), 15)]
    labels.update(bt.run_jobs(jobs))

    evidence, claims, label_rows = [], [], []
    for review in reviews:
        key = bt.rid(review)
        pid = f"SS-P-AMZ-{review['parent_asin']}"
        content = {"rid": key, "title": review.get("title"), "text": review.get("text"), "rating": review.get("rating"),
                   "date": bt.review_day(review).isoformat(), "images": [i.get("large_image_url") or
                   i.get("medium_image_url") for i in review.get("images") or []],
                   "verified_purchase": review.get("verified_purchase"),
                   "reviewer": hashlib.sha256((review.get("user_id") or "").encode()).hexdigest()[:16]}
        body = json.dumps(content, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha1(body.encode()).hexdigest()
        evidence_id = store.short_id("EV-", digest)
        evidence.append((evidence_id, "review", f"{pid}:{key}", body, content["date"], digest))
        claims.append((evidence_id, pid, evidence_id, pid))
        label = labels.get(key) or {"hazard": False, "experience": "not_a_hazard", "model": "keyword pre-filter"}
        label_body = json.dumps(label, sort_keys=True, ensure_ascii=False)
        label_digest = hashlib.sha1(label_body.encode() + evidence_id.encode()).hexdigest()
        label_rows.append((store.short_id("EV-", label_digest), "radar_label", evidence_id, label_body, label_digest))
    bulk(
            """INSERT INTO evidence (id, source_type, source_ref, content, observed_at, hash)
               VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""", evidence)
    bulk(
            """INSERT INTO evidence_claims (evidence_id, claim_type, claim_id) SELECT %s, 'review_of', %s
               WHERE NOT EXISTS (SELECT 1 FROM evidence_claims WHERE evidence_id = %s AND claim_id = %s)""", claims)
    bulk(
            """INSERT INTO evidence (id, source_type, source_ref, content, hash) VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""", label_rows)
    print(f"stored {len(evidence)} reviews with Safety Radar labels")


def main() -> None:
    items, links = load_sources()
    print(f"{len(items)} products, {len(links)} recall links")
    prints = {}
    for item in items:
        listing = {k: item.get(k) for k in ("title", "brand", "model", "category", "description", "attributes")}
        fp = identity.fingerprint(listing)
        text = brand_blind_text(listing, fp)
        prints[item["product_id"]] = (fp, hashlib.sha1(text.encode()).hexdigest(), text)
    vectors = vectors_for([(h, text) for _, h, text in prints.values()])

    bulk(
            """INSERT INTO products (id, brand, model, category, gtin) VALUES (%s, %s, %s, %s, NULL)
               ON CONFLICT (id) DO UPDATE SET brand = EXCLUDED.brand, model = EXCLUDED.model,
                                              category = EXCLUDED.category""",
            [(i["product_id"], i["brand"], prints[i["product_id"]][0]["model"], i["category"]) for i in items])
    bulk(
            """INSERT INTO listings (id, product_id, marketplace, url, title, raw) VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET raw = EXCLUDED.raw, title = EXCLUDED.title""",
            [(i["listing_id"], i["product_id"], i["marketplace"], i["url"], i["title"],
              Jsonb({k: i.get(k) for k in ("title", "price", "currency", "seller", "image_urls", "rating_number")
                     if i.get(k) is not None})) for i in items])
    bulk(
            """INSERT INTO product_fingerprints (product_id, version, text_vector, attributes_json)
               VALUES (%s, 1, %s::vector, %s)
               ON CONFLICT (product_id, version) DO UPDATE SET text_vector = EXCLUDED.text_vector,
                                                               attributes_json = EXCLUDED.attributes_json""",
            [(pid, store.vector_literal(vectors[h]), Jsonb(fp)) for pid, (fp, h, _) in prints.items()])
    bulk(
            """INSERT INTO recall_products (recall_id, product_id, match_class)
               SELECT %s, %s, %s WHERE NOT EXISTS (
                   SELECT 1 FROM recall_products WHERE recall_id = %s AND product_id = %s)""",
            [(r, p, m, r, p) for r, p, m in links])
    load_reviews({i["product_id"] for i in items})
    print(f"loaded {len(items)} products ({sum(i['marketplace'] == 'amazon.com' for i in items)} Amazon.com, "
          f"{sum(i['marketplace'] != 'amazon.com' for i in items)} Indian), {len(links)} recall links")


if __name__ == "__main__":
    main()
