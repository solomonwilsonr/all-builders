"""Postgres + pgvector access for the identity engine. Conclusions are versioned, never overwritten."""
import hashlib
import json
import os
import re
import threading

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

_conn: psycopg.Connection | None = None
_conn_lock = threading.Lock()


def connect_kwargs() -> dict:
    """DATABASE_URL locally; on Cloud Run the Cloud SQL socket plus DB_PASSWORD from Secret Manager, so the
    password never appears in a URL, a command line or the service config."""
    socket = os.environ.get("CLOUD_SQL_INSTANCE")
    if socket:
        return {"host": f"/cloudsql/{socket}", "dbname": os.environ.get("DB_NAME", "safeshelf"),
                "user": os.environ.get("DB_USER", "safeshelf"), "password": os.environ["DB_PASSWORD"]}
    return {"conninfo": os.environ.get("DATABASE_URL", "postgresql://safeshelf:safeshelf@localhost:5442/safeshelf")}


def conn() -> psycopg.Connection:
    """One shared connection (psycopg 3 serialises use across threads), reopened if the server dropped it."""
    global _conn
    with _conn_lock:
        if _conn is None or _conn.closed or _conn.broken:
            _conn = psycopg.connect(**connect_kwargs(), autocommit=True, row_factory=dict_row)
        return _conn


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
    """A listing seen again only fills in what was missing. What is stored stays: anyone can call identify with a
    known URL, and a caller's title or price must never replace the genuine listing's (15 Oct: an identify call with
    only the URL had emptied the demo listing, so the fake shop's Rs 299 was no longer compared with anything)."""
    raw = {k: listing.get(k) for k in ("title", "price", "currency", "seller", "image_urls") if listing.get(k)}
    conn().execute(
        """INSERT INTO listings (id, product_id, marketplace, url, title, raw) VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (id) DO UPDATE SET product_id = EXCLUDED.product_id,
               title = coalesce(listings.title, EXCLUDED.title), raw = EXCLUDED.raw || listings.raw""",
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


def nearest(vector: list[float], max_distance: float, brand_norm: str = "") -> str | None:
    """Closest product by brand-blind text embedding (latest fingerprints), if close enough; only that brand's
    products when brand_norm is given."""
    row = conn().execute(
        """WITH latest AS (SELECT DISTINCT ON (product_id) product_id, text_vector, attributes_json->>'brand_norm' AS b
                           FROM product_fingerprints ORDER BY product_id, version DESC)
           SELECT product_id, text_vector <=> %s::vector AS distance FROM latest
           WHERE %s = '' OR b = %s ORDER BY distance LIMIT 1""",
        (vector_literal(vector), brand_norm, brand_norm)).fetchone()
    return row["product_id"] if row and row["distance"] <= max_distance else None


def brands_in(title: str) -> list[str]:
    """Known brands (normalised) whose name starts the title, longest first: "Anker 20W ..." -> ["anker"]."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    candidates = ["".join(words[:n]) for n in (3, 2, 1) if len(words) >= n]
    rows = conn().execute(
        """SELECT DISTINCT attributes_json->>'brand_norm' AS b FROM product_fingerprints
           WHERE attributes_json->>'brand_norm' = ANY(%s)""", (candidates,)).fetchall()
    found = {r["b"] for r in rows}
    return [c for c in candidates if c in found]


def product_listings(product_id: str) -> list[dict]:
    return conn().execute("SELECT id, marketplace, url, title, raw FROM listings WHERE product_id = %s",
                          (product_id,)).fetchall()


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


def latest_evidence(source_type: str, source_ref: str, max_age_s: float) -> tuple[str, dict, float] | None:
    """The newest evidence of this type and reference captured within max_age_s: (id, content, age in seconds)."""
    row = conn().execute(
        "SELECT id, content, EXTRACT(EPOCH FROM now() - captured_at) AS age FROM evidence "
        "WHERE source_type = %s AND source_ref = %s AND captured_at > now() - make_interval(secs => %s) "
        "ORDER BY captured_at DESC LIMIT 1", (source_type, source_ref, max_age_s)).fetchone()
    return (row["id"], json.loads(row["content"]), float(row["age"])) if row else None


def evidence_refs(source_type: str, max_age_s: float) -> list[tuple[str, float]]:
    """Each reference with evidence of this type in the last max_age_s, and the age of its newest row (seconds)."""
    rows = conn().execute(
        "SELECT source_ref, EXTRACT(EPOCH FROM now() - max(captured_at)) AS age FROM evidence "
        "WHERE source_type = %s AND captured_at > now() - make_interval(secs => %s) GROUP BY source_ref",
        (source_type, max_age_s)).fetchall()
    return [(r["source_ref"], float(r["age"])) for r in rows]


def evidence_content(evidence_id: str) -> dict:
    row = conn().execute("SELECT content FROM evidence WHERE id = %s", (evidence_id,)).fetchone()
    return json.loads(row["content"]) if row else {}


def save_relationship(source: str, target: str, decision, would_change_if: list[str], evidence_ids: list[str]) -> int:
    latest = conn().execute(
        """SELECT * FROM product_relationships WHERE source_id = %s AND target_id = %s
           ORDER BY version DESC LIMIT 1""", (source, target)).fetchone()
    if latest and latest.get("adjudicated_by"):  # a person decided this pair: the engine never overwrites it
        return latest["version"]
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


def save_adjudicated_relationship(source: str, target: str, relationship: str, status: str, reviewer_ref: str,
                                  policy_version: str, evidence_ids: list[str], batch_scope: str | None = None) -> int:
    """A reviewer's decision about a pair, as a new version (plan v2.2 workstream C). Engine runs keep it."""
    latest = conn().execute(
        """SELECT * FROM product_relationships WHERE source_id = %s AND target_id = %s
           ORDER BY version DESC LIMIT 1""", (source, target)).fetchone()
    version = (latest["version"] + 1) if latest else 1
    conn().execute(
        """INSERT INTO product_relationships (source_id, target_id, relationship_type, confidence, status, evidence_ids,
                                              would_change_if, version, adjudicated_by, adjudicated_at,
                                              identity_policy_version, affected_batch_scope)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s)""",
        (source, target, relationship, 1.0, status, evidence_ids, [], version, reviewer_ref, policy_version,
         batch_scope))
    conn().execute(
        """INSERT INTO audit_events (entity_id, entity_type, change_type, actor, before, after)
           VALUES (%s, 'relationship', 'adjudicate', %s, %s, %s)""",
        (f"{source}->{target}", reviewer_ref,
         Jsonb(latest and {"relationship": latest["relationship_type"], "status": latest["status"],
                           "version": latest["version"]}),
         Jsonb({"relationship": relationship, "status": status, "version": version})))
    return version
