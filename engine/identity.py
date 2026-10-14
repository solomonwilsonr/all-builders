"""M3 identity engine: identify a listing, find its twins, and keep every decision (SAFESHELF.md 7.2).

    identify(listing)          -> Identity        (contract: POST /v1/products/identify)
    duplicates(product_id)     -> Duplicates      (contract: POST /v1/products/duplicates)
    relationships(product_id)  -> relationships   (contract: GET /v1/products/{id}/relationships)
"""
import contextvars
import re
from concurrent.futures import ThreadPoolExecutor

from engine import gemini, store
from engine.normalize import brand_blind_text, normalise
from engine.rules import decide

ORDER = {"exact_model": 0, "rebranded_equivalent": 1, "model_variant": 2, "shared_component": 3, "visually_similar": 4}
# What Gemini sees of each product: identity facts only, no prices or sellers.
VIEW_FIELDS = ("brand", "model", "category", "title", "description", "attributes", "visual_features",
               "label_text", "certifications_claimed")


def fingerprint(listing: dict) -> dict:
    fp = normalise(listing)
    fp["view"] = {k: listing[k] for k in VIEW_FIELDS if listing.get(k)}
    fp["certifications_claimed"] = listing.get("certifications_claimed") or []
    return fp


def register(product_id: str, listing_id: str, listing: dict) -> dict:
    """Store a product, its listing and a fingerprint (new version only if it changed)."""
    fp = fingerprint(listing)
    [vector] = gemini.embed([brand_blind_text(listing, fp)])
    store.upsert_product(product_id, fp)
    store.upsert_listing(listing_id, product_id, listing)
    fp["version"] = store.save_fingerprint(product_id, fp, vector)
    return fp


def same_brand(fp: dict, listing: dict, product_id: str) -> bool:
    """The brand matches, or no brand was given and the known product's brand appears in the title."""
    other = (store.latest_fingerprint(product_id) or {}).get("brand_norm", "")
    if fp["brand_norm"]:
        return fp["brand_norm"] == other
    return bool(other) and other in re.sub(r"[^a-z0-9]", "", (listing.get("title") or "").lower())


def resolve(listing: dict, max_distance: float = 0.12, needs_reference: bool = False) -> tuple[str | None, str]:
    """Which known product does this listing claim to be? Read-only, so fake-shop listings never become products.
    Returns (product_id, how): url, model_number, look_alike (brand-blind embedding) or (None, none).
    needs_reference: a product known only from this very page, as a shopper sent it (no marketplace: made by an
    earlier identify of, say, a fake shop), is no reference for checking that page, so the model number decides.
    Catalog and demo listings carry a marketplace and always count."""
    fp = fingerprint(listing)
    known = listing.get("url") and store.listing_by_url(listing["url"])
    if known and (not needs_reference or any(row["url"] != listing["url"] or row["marketplace"]
                                             for row in store.product_listings(known["product_id"]))):
        return known["product_id"], "url"
    same_id = [p for p in store.by_identifier(fp) if same_brand(fp, listing, p)]
    if same_id:
        return same_id[0], "model_number"
    [vector] = gemini.embed([brand_blind_text(listing, fp)])
    brand = fp["brand_norm"] or next((b for b in store.brands_in(listing.get("title") or "")), "")
    same_brand_match = brand and store.nearest(vector, max_distance * 2, brand)
    if same_brand_match:  # the brand's own product first; a brand-blind look-alike only when it has none close
        return same_brand_match, "same_brand_look_alike"
    nearest = store.nearest(vector, max_distance)
    return (nearest, "look_alike") if nearest else (None, "none")


def identify(listing: dict) -> dict:
    """Resolve a listing to a product: known URL, then a matching identifier, else a new provisional product.

    A listing attaches to a known product but never rewrites it: a shop's claims are evidence, not identity.
    """
    fp = fingerprint(listing)
    known = listing.get("url") and store.listing_by_url(listing["url"])
    listing_id = known["id"] if known else store.short_id("SS-L-", listing.get("url") or listing.get("title") or "")
    matched, how = resolve(listing)
    # A brand-blind look-alike is another brand's product: never attach a listing to it.
    if matched and how in ("url", "model_number", "same_brand_look_alike"):
        product_id = matched
        stored = store.latest_fingerprint(product_id)
        store.upsert_listing(listing_id, product_id, listing)
        if fp["gtin"] and fp["gtin"] == stored["gtin"]:
            status, confidence = "verified", 0.95
        else:
            status, confidence = "provisional", 0.7 if how == "same_brand_look_alike" else 0.85
    else:
        product_id = store.short_id("SS-P-", fp["brand_norm"], fp["model_norm"], listing.get("title") or "")
        stored = register(product_id, listing_id, listing)
        status, confidence = ("provisional", 0.6) if stored["model_norm"] or stored["gtin"] else ("unknown", 0.3)
    evidence_id = store.add_evidence("listing_snapshot", listing.get("url") or listing_id, fp["view"])
    return {
        "product_id": product_id,
        "listing_id": listing_id,
        "category": stored["category"],
        "brand": stored["brand"],
        "model": stored["model"],
        "attributes": stored["attributes"],
        "certifications_claimed": stored["certifications_claimed"],
        "identity_status": status,
        "confidence": confidence,
        "evidence_ids": [evidence_id],
    }


def compare_and_store(source: str, target: str) -> None:
    a, b = store.latest_fingerprint(source), store.latest_fingerprint(target)
    proposal = gemini.compare(a["view"], b["view"])
    decision = decide(a, b, proposal)
    evidence_id = store.add_evidence("pair_compare", f"{source}:{target}", {
        "source": source, "target": target, "fingerprint_versions": [a["version"], b["version"]],
        "proposal": proposal, "decision": decision.__dict__})
    store.save_relationship(source, target, decision, proposal.get("would_change_if") or [], [evidence_id])


def duplicates(product_id: str, refresh: bool = False) -> dict:
    """Candidates come from identifiers and brand-blind vector search; Gemini compares; rules decide."""
    fp = store.latest_fingerprint(product_id)
    if fp is None:
        raise KeyError(product_id)
    if refresh or not store.latest_relationships(product_id):
        candidates = dict.fromkeys(store.by_identifier(fp, exclude=product_id))
        candidates.update(dict.fromkeys(p for p, _ in store.neighbours(product_id)))
        # In parallel, so one slow Gemini call doesn't hold up the rest; each pair is stored on its own.
        # Each worker runs in a copy of this context, so the trace still sees its Gemini calls.
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda target, ctx: ctx.run(compare_and_store, product_id, target),
                          candidates, [contextvars.copy_context() for _ in candidates]))
    matches = []
    for rel in store.latest_relationships(product_id):
        detail = store.evidence_content(rel["evidence_ids"][0]) if rel["evidence_ids"] else {}
        proposal = detail.get("proposal", {})
        matches.append({
            "product_id": rel["target_id"],
            "relationship": rel["relationship_type"],
            "status": rel["status"],
            "confidence": round(rel["confidence"], 2),
            "agreements": proposal.get("agreements", []),
            "conflicts": proposal.get("conflicts", []),
            "would_change_if": rel["would_change_if"] or [],
            "evidence_ids": rel["evidence_ids"] or [],
        })
    matches.sort(key=lambda m: (ORDER[m["relationship"]], -m["confidence"]))
    return {"query_product_id": product_id, "graph_version": store.graph_version(), "matches": matches}


def relationships(product_id: str) -> dict:
    rows = store.latest_relationships(product_id)
    return {
        "product_id": product_id,
        "relationships": [{"target_id": r["target_id"], "relationship": r["relationship_type"], "status": r["status"],
                           "confidence": round(r["confidence"], 2), "evidence_ids": r["evidence_ids"] or []}
                          for r in sorted(rows, key=lambda r: ORDER[r["relationship_type"]])],
        "graph_version": store.graph_version(),
    }
