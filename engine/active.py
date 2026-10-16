"""Active evidence acquisition (plan v2.2 workstream F): which missing fact would most change this assessment, and the
cheapest authorised way to get it. A small value-of-information list, ranked by impact over cost; it stops suggesting
once the outcome is settled. Every step is read-only or asks the shopper: nothing here acts on the shopper's behalf.
"""

# (fact, how to get it, cost 1-5: 1 = the shopper glances at the label, 5 = a person investigates)
STEPS = {
    "model": ("the model number printed on the product's label", "photo of the label (camera check)", 1),
    "batch": ("the serial, lot or date code on the unit", "photo of the label or the box", 1),
    "local_version": ("whether the local version is the same model (importer, model suffix)",
                      "a reviewer compares the foreign notice with the local listing", 4),
    "person_match": ("a person comparing the model code and photos with the notice", "reviewer queue", 4),
    "market_source": ("the local regulator's own list, which couldn't be read automatically",
                      "a person checks the regulator's site", 3),
    "certificate": ("the safety-mark registration (e.g. BIS R-number)", "look it up in the BIS Care app", 2),
    "more_reviews": ("more first-hand owner reports", "SafeShelf re-checks as reviews arrive (watchlist)", 2),
    "deep_sources": ("sites that need a browser (EU Safety Gate, New Zealand)", "a deep check", 2),
    "damage_photo": ("a photo of any damage (scorch marks, swelling)", "camera check", 1),
}
IMPACT = {"model": 5, "batch": 5, "local_version": 4, "person_match": 4, "market_source": 3, "certificate": 2,
          "more_reviews": 2, "deep_sources": 2, "damage_photo": 3}


def plan(decision: dict, product: dict, coverage_rows: list[dict], depth: str, matches: list[dict]) -> list[dict]:
    if decision["outcome"] == "confirmed_recall":
        return []  # settled: what to do now is owner guidance, not more evidence
    wanted = []
    if not product.get("model"):
        wanted.append("model")
    if decision["basis"] == "local_recall_batch_unknown" or any(m.get("scope") == "batch_unknown" for m in matches):
        wanted.append("batch")
    if decision["basis"] == "recalled_abroad_same_model":
        wanted += ["batch", "local_version"]
    if decision["basis"] == "possible_match":
        wanted.append("person_match")
    market = next((r for r in coverage_rows if r.get("is_market")), None)
    if market and market["state"] in ("source_unavailable", "not_supported"):
        wanted.append("market_source")
    if decision["basis"] in ("seizure_or_notice", "registry_mismatch") or (product.get("market") == "IN"):
        wanted.append("certificate")
    if decision["basis"] in ("hazard_reports", "substantiated_hazard_signal"):
        wanted.append("damage_photo")
    if any("review" in limit for limit in decision.get("limitations", [])):
        wanted.append("more_reviews")
    if depth != "deep":
        wanted.append("deep_sources")
    ranked = sorted(dict.fromkeys(wanted), key=lambda k: (-IMPACT[k] / STEPS[k][2], STEPS[k][2]))
    return [{"fact": STEPS[k][0], "how": STEPS[k][1], "cost": STEPS[k][2], "impact": IMPACT[k], "key": k}
            for k in ranked[:4]]
