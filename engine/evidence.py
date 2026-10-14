"""GET /v1/evidence?ids=EV-1,EV-2: what each evidence ID points to, in plain words.

The extension shows these under chat answers and findings, and finds a review on the page by its quote, so a
review's quote is its exact text (never trimmed at the start or paraphrased). Unknown IDs are left out.
"""
import json
from urllib.parse import urlparse

from engine import store

MAX_IDS = 50
MARKETPLACE_NAMES = {"demo": "the demo shop", "amazon.com": "Amazon.com", "amazon.in": "Amazon.in",
                     "flipkart.com": "Flipkart"}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").removeprefix("www.")


def _review_place(source_ref: str) -> tuple[str, str | None]:
    """Where a stored review was read: the shopper's page (listing:<url>:<id>) or a product's catalog listing."""
    if source_ref.startswith("listing:"):
        url = source_ref.removeprefix("listing:").rsplit(":", 1)[0]
        return (f"Customer review on {_host(url) or 'the product page'}", url if url.startswith("http") else None)
    product_id = source_ref.rsplit(":", 1)[0]
    for row in store.product_listings(product_id):
        name = MARKETPLACE_NAMES.get(row["marketplace"] or "", row["marketplace"])
        if name:
            return f"Customer review on {name}", row["url"]
    return "Customer review", None


def describe(row: dict) -> dict:
    content = json.loads(row["content"] or "{}")
    kind, ref = row["source_type"], row["source_ref"] or ""
    date = (row["observed_at"] or row["captured_at"]).date().isoformat()
    item = {"evidence_id": row["id"], "date": date, "url": None}
    if kind == "review":
        source, url = _review_place(ref)
        rating = content.get("rating")
        return {**item, "type": "review", "source": source, "url": url, "quote": content.get("text") or "",
                "rating": int(rating) if rating else None, "date": content.get("date") or date}
    if kind == "photo_check":
        return {**item, "type": "review_photo", "source": "Photo from a customer review, described by AI",
                "quote": content.get("description") or "", "url": ref if ref.startswith("http") else None}
    if kind == "trust_check":
        return {**item, "type": "check", "source": "SafeShelf \"Is it real?\" check of this listing",
                "quote": content.get("summary") or "", "url": ref if ref.startswith("http") else None}
    if kind == "radar_label":
        return {**item, "type": "ai_label", "source": "AI reading of a customer review",
                "quote": content.get("quote") or content.get("mechanism") or ""}
    if kind == "pair_compare":
        reasons = (content.get("decision") or {}).get("reasons") or []
        return {**item, "type": "check", "source": "SafeShelf comparison of two products", "quote": "; ".join(reasons)}
    if kind == "recall_models":
        models = ", ".join(content.get("models") or []) or "no model numbers named"
        return {**item, "type": "recall_notice", "source": f"Official recall notice {ref}", "quote": f"Models: {models}"}
    view = content.get("view") or content
    return {**item, "type": "listing_text", "source": "Product listing", "url": ref if ref.startswith("http") else None,
            "quote": view.get("title") or view.get("description") or ""}


def lookup(ids: str) -> list[dict]:
    wanted = [i.strip() for i in ids.split(",") if i.strip()][:MAX_IDS]
    if not wanted:
        return []
    rows = store.conn().execute(
        "SELECT id, source_type, source_ref, content, observed_at, captured_at FROM evidence WHERE id = ANY(%s)",
        (wanted,)).fetchall()
    by_id = {r["id"]: describe(r) for r in rows}
    return [by_id[i] for i in wanted if i in by_id]
