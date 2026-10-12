"""Postgres + pgvector access for the identity engine. Conclusions are versioned, never overwritten."""
import hashlib
import json
import os
from functools import cache

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


@cache
def conn() -> psycopg.Connection:
    url = os.environ.get("DATABASE_URL", "postgresql://safeshelf:safeshelf@localhost:5442/safeshelf")
    return psycopg.connect(url, autocommit=True, row_factory=dict_row)


def short_id(prefix: str, *parts: str) -> str:
    return prefix + hashlib.sha1("|".join(parts).encode()).hexdigest()[:8].upper()


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"


def upsert_product(product_id: str, fp: dict) -> None:
    conn().execute(
        """INSERT INTO products (id, brand, model, category, gtin) VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (id) DO UPDATE SET brand = EXCLUDED.brand, model = EXCLUDED.model,
                                          category = EXCLUDED.category, gtin = EXCLUDED.gtin""",
        (product_id, fp["brand"], fp["model"], fp["category"], fp["gtin"]),
    )


def upsert_listing(listing_id: str, product_id: str, listing: dict) -> None:
    raw = {k: listing.get(k) for k in ("title", "price", "currency", "seller", "image_urls") if listing.get(k)}
    conn().execute(
        """INSERT INTO listings (id, product_id, marketplace, url, title, raw) VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (id) DO UPDATE SET product_id = EXCLUDED.product_id, title = EXCLUDED.title, raw = EXCLUDED.raw""",
        (listing_id, product_id, listing.get("marketplace"), listing.get("url"), listing.get("title"), Jsonb(raw)),
    )


def listing_by_url(url: str) -> dict | None:
    return conn().execute("SELECT id, product_id FROM listings WHERE url = %s LIMIT 1", (url,)).fetchone()


def latest_fingerprint(product_id: str) -> dict | None:
    row = conn().execute(
        """SELECT version, attributes_json FROM product_fingerprints WHERE product_id = %s
           ORDER BY version DESC LIMIT 1""", (product_id,)).fetchone()
    return row and {"version": row["version"], **row["attributes_json"]}


def save_fingerprint(product_id: str, fingerprint: dict, vector: list[float]) -> int:
    """New version only when the fingerprint changed."""
    latest = latest_fingerprint(product_id)
    if latest and {k: v for k, v in latest.items() if k != "version"} == fingerprint:
        return latest["version"]
    version = (latest["version"] + 1) if latest else 1
    conn().execute(
        """INSERT INTO product_fingerprints (product_id, version, text_vector, attributes_json)
           VALUES (%s, %s, %s::vector, %s)""",
        (product_id, version, vector_literal(vector), Jsonb(fingerprint)),
    )
    return version


def by_identifier(fp: dict, exclude: str | None = None) -> list[str]:
    """Products whose latest fingerprint has the same GTIN or model number."""
    if not (fp["gtin"] or fp["model_norm"]):
        return []
    rows = conn().execute(
        """WITH latest AS (
               SELECT DISTINCT ON (product_id) product_id, attributes_json AS a FROM product_fingerprints
               ORDER BY product_id, version DESC)
           SELECT product_id FROM latest
           WHERE product_id IS DISTINCT FROM %s
             AND ((%s <> '' AND a->>'model_norm' = %s) OR (%s <> '' AND a->>'gtin' = %s))""",
        (exclude, fp["model_norm"], fp["model_norm"], fp["gtin"] or "", fp["gtin"] or "")).fetchall()
    return [r["product_id"] for r in rows]


def neighbours(product_id: str, k: int = 8, max_distance: float = 0.25) -> list[tuple[str, float]]:
    """Nearest products by brand-blind text embedding, same category, latest fingerprints only."""
    rows = conn().execute(
        """WITH latest AS (
               SELECT DISTINCT ON (product_id) product_id, text_vector, attributes_json->>'category' AS category
               FROM product_fingerprints ORDER BY product_id, version DESC)
           SELECT o.product_id, o.text_vector <=> q.text_vector AS distance
           FROM latest q JOIN latest o ON o.product_id <> q.product_id AND o.category = q.category
           WHERE q.product_id = %s ORDER BY distance LIMIT %s""",
        (product_id, k)).fetchall()
    return [(r["product_id"], float(r["distance"])) for r in rows if r["distance"] <= max_distance]


def add_evidence(source_type: str, source_ref: str, content: dict) -> str:
    body = json.dumps(content, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha1(body.encode()).hexdigest()
    existing = conn().execute("SELECT id FROM evidence WHERE hash = %s LIMIT 1", (digest,)).fetchone()
    if existing:
        return existing["id"]
    evidence_id = short_id("EV-", digest)
    conn().execute(
        "INSERT INTO evidence (id, source_type, source_ref, content, hash) VALUES (%s, %s, %s, %s, %s)",
        (evidence_id, source_type, source_ref, body, digest))
    return evidence_id


def evidence_content(evidence_id: str) -> dict:
    row = conn().execute("SELECT content FROM evidence WHERE id = %s", (evidence_id,)).fetchone()
    return json.loads(row["content"]) if row else {}


def save_relationship(source: str, target: str, decision, would_change_if: list[str], evidence_ids: list[str]) -> int:
    latest = conn().execute(
        """SELECT * FROM product_relationships WHERE source_id = %s AND target_id = %s
           ORDER BY version DESC LIMIT 1""", (source, target)).fetchone()
    if latest and (latest["relationship_type"], latest["status"], latest["evidence_ids"]) == (
            decision.relationship, decision.status, evidence_ids):
        return latest["version"]
    version = (latest["version"] + 1) if latest else 1
    conn().execute(
        """INSERT INTO product_relationships (source_id, target_id, relationship_type, confidence, status,
                                              evidence_ids, would_change_if, version)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (source, target, decision.relationship, decision.confidence, decision.status,
         evidence_ids, would_change_if, version))
    after = {"relationship": decision.relationship, "status": decision.status, "confidence": decision.confidence,
             "reasons": decision.reasons, "version": version}
    before = latest and {"relationship": latest["relationship_type"], "status": latest["status"],
                         "version": latest["version"]}
    conn().execute(
        """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, before, after)
           VALUES (%s, 'relationship', %s, 'engine.identity', %s, %s)""",
        (f"{source}->{target}", "update" if latest else "create", Jsonb(before), Jsonb(after)))
    return version


def latest_relationships(product_id: str) -> list[dict]:
    return conn().execute(
        """SELECT DISTINCT ON (target_id) * FROM product_relationships WHERE source_id = %s
           ORDER BY target_id, version DESC""", (product_id,)).fetchall()


def graph_version() -> int:
    return conn().execute("SELECT count(*) AS n FROM product_relationships").fetchone()["n"]
