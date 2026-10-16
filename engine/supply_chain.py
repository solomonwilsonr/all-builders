"""Supply-chain graph (plan v2.2 workstream E): manufacturer, importer, distributor and retailer edges, each cited to
the official record that names the party, with a confidence. Never inferred from appearance: two products that look
alike share no factory here unless a notice says so.
"""
from engine import store

ROLES = {"Manufacturers": "manufacturer", "Importers": "importer", "Distributors": "distributor",
         "Retailers": "retailer"}
CONFIDENCE = {"manufacturer": 0.9, "importer": 0.9, "distributor": 0.8, "retailer": 0.6}


def parties(record_scope: dict) -> list[dict]:
    out = []
    for key, role in ROLES.items():
        for item in record_scope.get(key) or []:
            name = (item.get("Name") or "").strip()
            if name and not name.lower().startswith("sold online") and len(name) < 120:
                out.append({"party_name": name, "role": role, "country": item.get("Country") or None})
    return out


def build(product_id: str) -> dict:
    """Edges for a stored product from the notices linked to it (recall_products), saved to supply_chain_edges."""
    fp = store.latest_fingerprint(product_id)
    if fp is None:
        raise KeyError(product_id)
    rows = store.conn().execute(
        """SELECT DISTINCT r.id, r.scope_json, r.url FROM recall_products p JOIN recalls r ON r.id = p.recall_id
           WHERE p.product_id = %s""", (product_id,)).fetchall()
    edges = []
    for row in rows:
        for party in parties(row["scope_json"] or {}):
            edge = {**party, "source_record_id": row["id"], "source_url": row["url"],
                    "confidence": CONFIDENCE[party["role"]]}
            edges.append(edge)
            try:
                store.conn().execute(
                    """INSERT INTO supply_chain_edges (product_key, party_name, role, country, source_record_id,
                                                       source_url, confidence)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    (product_id, edge["party_name"], edge["role"], edge["country"], row["id"], row["url"],
                     edge["confidence"]))
            except Exception:  # noqa: BLE001, S110  before `make migrate` the table may not exist
                pass
    return {"product_id": product_id, "edges": edges,
            "note": "Each party is named by an official notice (cited). Look-alike products are never linked here."}
