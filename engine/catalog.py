"""M14a Catalog Scan: check a whole catalog (CSV) and rank what needs attention (SAFESHELF.md 4, item 19).

    scan({"csv_url": "gs://bucket/catalog.csv"})  -> contract answer of POST /v1/catalog/scan

Cheap first, expensive last: every row gets identifier matching, the recall check and the safety-mark check (no
Gemini per row); embeddings are batched; Gemini compares only the few rows closest to a recalled product.
Ranking: recall matches (flagged) > possible recall matches (sent for review) > certification mismatches (flagged)
> hazard signals on a matched product (under review). Same safety rules as everywhere: only an exact model is a
recall match; a possible rebrand goes to a person; a look-alike is never reported as recalled.
"""
import csv
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from engine import gemini, identity, marks, radar, recalls, safety, store
from engine.normalize import brand_blind_text, category_of
from engine.rules import decide

MAX_ROWS = 1000
REBRAND_COMPARES = 20  # Gemini pair compares per scan, closest candidates first
REBRAND_DISTANCE = 0.12
RANK = {"recall_match": 0, "possible_recall_match": 1, "certification_mismatch": 2, "hazard_signal": 3}
# The retailer side: what a shop does with each item on its shelves when a recall lands (shown with every finding).
SHOP_ACTIONS = {
    "recall_match": ["Stop selling it now: take it off the shelf and unpublish the online listing",
                     "Quarantine the stock you hold; don't send it back out or discount it",
                     "Follow the recall notice's remedy and contact your supplier for the return",
                     "Tell customers who bought it (receipts, loyalty or order records) how to get the remedy"],
    "possible_recall_match": ["Hold sales of this item until someone compares its model number with the recall",
                              "Ask your supplier whether your stock is the recalled product line"],
    "certification_mismatch": ["Hold sales and ask your supplier for the valid safety certificate for this model",
                               "Correct or remove the safety mark claim on the listing"],
    "hazard_signal": ["Keep selling but watch it: read the buyer reports and ask your supplier about them",
                      "Turn on recall alerts for this model (POST /v1/watchlists)"],
}
COLUMNS = {"title": ("title", "name", "product", "listing_title"), "brand": ("brand", "manufacturer"),
           "model": ("model", "model_number", "item_model_number", "sku_model"), "price": ("price", "mrp"),
           "url": ("url", "link", "listing_url"), "seller": ("seller", "vendor"), "gtin": ("gtin", "ean", "upc")}


def read_csv(csv_url: str | None = None, csv_text: str | None = None) -> list[dict]:
    """Rows as listings. gs:// is read with the service's own credentials; https with a plain GET."""
    if csv_text is None:
        if not csv_url:
            raise ValueError("give csv_url (gs:// or https://) or csv_text")
        if csv_url.startswith("gs://"):
            import google.auth
            from google.auth.transport.requests import AuthorizedSession

            bucket, _, name = csv_url.removeprefix("gs://").partition("/")
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
            response = AuthorizedSession(credentials).get(
                f"https://storage.googleapis.com/storage/v1/b/{bucket}/o/{requests.utils.quote(name, safe='')}",
                params={"alt": "media"}, timeout=60)
        else:
            response = requests.get(csv_url, timeout=60)
        response.raise_for_status()
        csv_text = response.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(csv_text))
    header = {h.strip().lower().replace(" ", "_"): h for h in reader.fieldnames or []}
    pick = {field: next((header[n] for n in names if n in header), None) for field, names in COLUMNS.items()}
    if not pick["title"]:
        raise ValueError(f"the CSV needs a title column (one of {', '.join(COLUMNS['title'])})")
    rows = []
    for line in reader:
        listing = {f: (line.get(col) or "").strip() for f, col in pick.items() if col}
        if not listing.get("title"):
            continue
        try:
            listing["price"] = float(str(listing.get("price", "")).replace(",", "").lstrip("₹$")) or None
        except ValueError:
            listing["price"] = None
        listing["category"] = category_of(listing["title"]) or ""
        rows.append(listing)
        if len(rows) >= MAX_ROWS:
            break
    return rows


class Notices:
    """All recall notices in memory for one scan: one query instead of one text search per brand (21 s of 31 s
    per 100 rows when searched in the database, 15 Oct)."""

    def __init__(self):
        self.rows = store.conn().execute(
            """SELECT id, notice_date, title, hazard, scope_json, url,
                      lower(coalesce(title, '') || ' ' || scope_json::text) AS hay
               FROM recalls ORDER BY notice_date DESC""").fetchall()
        self.by_brand: dict[str, list[dict]] = {}

    def __contains__(self, brand_norm: str) -> bool:
        return brand_norm in self.by_brand

    def __getitem__(self, brand_norm: str) -> list[dict]:
        return self.by_brand[brand_norm]

    def __setitem__(self, brand_norm: str, value: list[dict]) -> None:
        self.by_brand[brand_norm] = value

    def for_brand(self, brand: str) -> list[dict]:
        needle = (brand or "").strip().lower()
        return [n for n in self.rows if needle in n["hay"]] if len(needle) >= 3 else []


def recall_finding(fp: dict, matched: str | None, notices_by_brand: "Notices") -> dict | None:
    """Exact model in a notice -> recall_match; family named without models -> possible_recall_match."""
    if fp["brand_norm"] not in notices_by_brand:
        notices_by_brand[fp["brand_norm"]] = notices_by_brand.for_brand(fp["brand"])
    best = None
    for notice in notices_by_brand[fp["brand_norm"]]:
        match = recalls.classify(fp, notice)
        if match == "exact_model":
            return {"finding": "recall_match", "relationship": "exact_model", "status": "flagged",
                    "recall_id": notice["id"], "reason": f"model {fp['model']} is named in recall {notice['id']}"}
        if match == "needs_review" and not best:
            best = {"finding": "possible_recall_match", "relationship": "same_product_line", "status": "sent_for_review",
                    "recall_id": notice["id"], "reason": f"{notice['title']} names this product line, no model numbers"}
    if matched:  # the matched catalog product is already linked to a recall
        for link in store.conn().execute(
                "SELECT recall_id, match_class FROM recall_products WHERE product_id = %s", (matched,)).fetchall():
            if link["match_class"] == "exact_model":
                return {"finding": "recall_match", "relationship": "exact_model", "status": "flagged",
                        "recall_id": link["recall_id"], "reason": f"same product as {matched}, linked to the recall"}
            best = best or {"finding": "possible_recall_match", "relationship": "same_product_line",
                            "status": "sent_for_review", "recall_id": link["recall_id"],
                            "reason": f"same product as {matched}, linked to the recall for review"}
    return best


def models_in_catalog(model_norms: set[str]) -> dict[str, list[tuple[str, str]]]:
    """model number -> [(product_id, brand_norm)] for the catalog's latest fingerprints, in one query."""
    if not model_norms:
        return {}
    rows = store.conn().execute(
        """SELECT DISTINCT ON (product_id) product_id, attributes_json->>'model_norm' AS m,
                  attributes_json->>'brand_norm' AS b
           FROM product_fingerprints WHERE attributes_json->>'model_norm' = ANY(%s)
           ORDER BY product_id, version DESC""", (list(model_norms),)).fetchall()
    out: dict[str, list[tuple[str, str]]] = {}
    for r in rows:
        out.setdefault(r["m"], []).append((r["product_id"], r["b"]))
    return out


def mark_finding(listing: dict, fp: dict) -> dict | None:
    view = {k: listing.get(k) for k in ("title", "brand", "model")}
    for claim in marks.claims(view, use_gemini=False):
        result = marks.check(claim, {**fp, "category": fp["category"] or listing.get("category")})
        if result["result"] == "mismatch":
            return {"finding": "certification_mismatch", "relationship": None, "status": "flagged",
                    "reason": result.get("reason"), "check": result}
    return None


def hazard_finding(matched: str | None) -> dict | None:
    """Serious Safety Radar findings on the matched product, from stored labels only (no Gemini in a scan)."""
    if not matched:
        return None
    reviews = safety.product_reviews(matched)
    if not reviews:
        return None
    serious = [f for f in radar.findings(reviews, safety.stored_labels(reviews))
               if f["severity"] in ("medium", "high") and f["independent_reports"] >= 2]
    if not serious:
        return None
    top = serious[0]
    return {"finding": "hazard_signal", "relationship": None, "status": "under_review",
            "reason": f"{top['independent_reports']} buyer reports of {top['mechanism'] or top['hazard_type']}"}


def rebrand_findings(rows: list[dict], fps: list[dict], findings: dict[int, dict]) -> int:
    """Rows without a finding whose brand-blind embedding sits next to a recalled product of another brand:
    Gemini compares the closest few, the rules decide, a person verifies. Returns the number of compares."""
    open_rows = [i for i in range(len(rows)) if i not in findings and rows[i].get("title")]
    if not open_rows:
        return 0
    vectors = gemini.embed([brand_blind_text(rows[i], fps[i]) for i in open_rows])
    candidates = []
    for i, vector in zip(open_rows, vectors):
        hit = store.conn().execute(
            """WITH recalled AS (SELECT DISTINCT product_id FROM recall_products),
                    latest AS (SELECT DISTINCT ON (f.product_id) f.product_id, f.text_vector, f.attributes_json
                               FROM product_fingerprints f JOIN recalled r ON r.product_id = f.product_id
                               ORDER BY f.product_id, f.version DESC)
               SELECT product_id, attributes_json, text_vector <=> %s::vector AS distance FROM latest
               ORDER BY distance LIMIT 1""", (store.vector_literal(vector),)).fetchone()
        same_kind = not fps[i]["category"] or hit and hit["attributes_json"].get("category") in ("", fps[i]["category"])
        if hit and same_kind and hit["distance"] <= REBRAND_DISTANCE \
                and hit["attributes_json"].get("brand_norm") != fps[i]["brand_norm"]:
            candidates.append((hit["distance"], i, hit["product_id"], hit["attributes_json"]))
    candidates.sort()

    def compare(item: tuple) -> tuple[int, str, object, dict]:
        _, i, target, target_fp = item
        key = f"{store.short_id('', rows[i]['title'], rows[i].get('model') or '')}:{target}"
        cached = store.conn().execute(  # the same row and target are compared once, ever
            "SELECT content FROM evidence WHERE source_type = 'catalog_pair' AND source_ref = %s LIMIT 1", (key,)
        ).fetchone()
        if cached:
            proposal = json.loads(cached["content"])
        else:
            proposal = gemini.compare(fps[i]["view"], target_fp.get("view") or {})
            store.add_evidence("catalog_pair", key, proposal)
        return i, target, decide(fps[i], target_fp, proposal), proposal

    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, target, decision, proposal in pool.map(compare, candidates[:REBRAND_COMPARES]):
            if decision.relationship == "rebranded_equivalent":
                evidence_id = store.add_evidence("catalog_compare", f"{rows[i]['title']}:{target}", {
                    "row": rows[i], "target": target, "proposal": proposal, "decision": decision.__dict__})
                findings[i] = {"finding": "possible_recall_match", "relationship": "rebranded_equivalent",
                               "status": "sent_for_review", "matched_product_id": target, "evidence_ids": [evidence_id],
                               "reason": "possible rebrand of a recalled product: " + "; ".join(proposal.get("agreements", [])[:2])}
    return min(len(candidates), REBRAND_COMPARES)


def scan(body: dict) -> dict:
    started = time.time()
    rows = read_csv(body.get("csv_url"), body.get("csv_text"))
    fps = [identity.fingerprint(r) for r in rows]
    notices_by_brand = Notices()
    known = models_in_catalog({fp["model_norm"] for fp in fps if fp["model_norm"]})
    findings: dict[int, dict] = {}
    matches: dict[int, str | None] = {}
    for i, (row, fp) in enumerate(zip(rows, fps)):
        same_id = [p for p, brand in known.get(fp["model_norm"], []) if brand == fp["brand_norm"]]
        matches[i] = same_id[0] if same_id else None
        found = recall_finding(fp, matches[i], notices_by_brand) or mark_finding(row, fp) or hazard_finding(matches[i])
        if found:
            findings[i] = {"matched_product_id": matches[i], **found}
    compares = rebrand_findings(rows, fps, findings)

    results = []
    for i, found in findings.items():
        evidence_ids = found.pop("evidence_ids", None) or [store.add_evidence(
            "catalog_finding", f"{rows[i]['title']}:{found['finding']}", {"row": rows[i], **found})]
        results.append({"row": i + 2, "listing_title": rows[i]["title"], **found, "evidence_ids": evidence_ids,
                        "shop_action": SHOP_ACTIONS[found["finding"]]})
    results.sort(key=lambda r: (RANK[r["finding"]], r["row"]))
    seconds = time.time() - started
    counts = {k: sum(r["finding"] == k for r in results) for k in RANK}
    parts = [f"{counts['recall_match']} match a recalled product",
             f"{counts['possible_recall_match']} may match one (for review)",
             f"{counts['certification_mismatch']} have a safety mark that does not match the registry",
             f"{counts['hazard_signal']} have buyer reports of a hazard"]
    answer = {
        "job_id": store.short_id("SS-J-", body.get("csv_url") or "", str(started)),
        "status": "done",
        "listings_checked": len(rows),
        "summary": f"{len(results)} of your {len(rows):,} listings need attention: " +
                   ", ".join(p for p, k in zip(parts, RANK) if counts[k]) if results else
                   f"None of your {len(rows):,} listings matched a recall, a bad safety mark or a hazard signal",
        "results": results,
        "counts": counts,
        "gemini_compares": compares,
        "seconds": round(seconds, 1),
        "seconds_per_1000_listings": round(1000 * seconds / max(len(rows), 1), 1),
        "label": "Findings for review by a person - not a regulatory determination",
    }
    store.add_evidence("catalog_scan", answer["job_id"], {k: v for k, v in answer.items() if k != "results"})
    return answer
