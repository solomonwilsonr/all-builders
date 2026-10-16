"""The deterministic evidence policy (plan v2.2 J3 steps 6-7, invariants 1-4 and 8). Agents and Gemini collect and
explain evidence; only this code sets the outcome.

Outcomes:
  confirmed_recall             a LOCAL official recall names this exact model, its batch limits include the unit (or
                               it has none), the source checks out, and nothing retracts it
  substantiated_hazard_signal  two or more independent first-hand observations of a serious hazard (medium or high
                               severity, at least one high or with a damage photo), or an exact-model official
                               safety notice / incident record corroborated by an independent report
  potential_concern            anything that warrants a look but is not proven for this unit: a foreign recall of the
                               same model, a local recall whose batch limits are unknown, a variant, a suspected
                               rebrand, a notice naming the brand and type without models, a seizure of this product
                               type, a weak hazard signal, a registry mismatch
  no_matching_notice_found     the market's own sources (or, failing that, global sources) answered and nothing in them
                               concerns this product. Not proof of safety.
  insufficient_evidence        not enough to say: the product can't be identified, or no source for its market answered

Separate outputs: safety_concern, evidence_strength, identity_confidence and coverage are never folded into one score.
"""
from engine.evidence_verification import POLICY_VERSION
from engine.sources.base import CHECKED_CACHE, CHECKED_LIVE, NO_MATCH

OUTCOMES = ("confirmed_recall", "substantiated_hazard_signal", "potential_concern", "no_matching_notice_found",
            "insufficient_evidence")
COLOUR = {"confirmed_recall": "red", "substantiated_hazard_signal": "amber", "potential_concern": "amber",
          "no_matching_notice_found": "green", "insufficient_evidence": "unknown"}
POSSIBLE_TIERS = ("exact", "variant", "suspected_rebrand", "family_named")
LEAD_FIELDS = ("record_id", "authority", "title", "url", "published", "tier", "scope", "local", "jurisdiction")
TIER_RANK = ["exact", "variant", "suspected_rebrand", "family_named", "lookalike", "unresolved", "none"]
HEADLINES = {
    "confirmed_recall": "Recalled in {market}: this exact model is on an official recall list",
    "recalled_abroad_same_model": "Recalled abroad, same model number; not confirmed for {market}",
    "local_recall_batch_unknown": "Recalled in {market} for some units; check your serial or batch number",
    "substantiated_hazard_signal": "Several independent owners report a serious hazard (not a regulator's decision)",
    "possible_match": "An official notice may cover this product; a person must check the model",
    "seizure_or_notice": "Officials acted against this type of product in {market}; check its certification",
    "hazard_reports": "Some owners report a possible hazard (AI finding, under review)",
    "registry_mismatch": "A safety mark on the listing doesn't match the official registry",
    "brand_recalls_model_unknown": "This brand has recalls of other models; the model number is needed to tell",
    "no_matching_notice_found": "No matching notice found in the sources checked (this is not proof of safety)",
    "insufficient_evidence": "Not enough evidence to say",
}


def _best(matches: list[dict], **want) -> dict | None:
    pool = [m for m in matches if all(m.get(k) == v if not isinstance(v, (set, tuple)) else m.get(k) in v
                                      for k, v in want.items())]
    pool.sort(key=lambda m: m.get("published") or "", reverse=True)  # newest first, then (stable) closest match
    pool.sort(key=lambda m: (TIER_RANK.index(m["tier"]), not m["local"]))
    return pool[0] if pool else None


def decide(market: str | None, market_name: str, product: dict, matches: list[dict], hazards: list[dict],
           coverage_rows: list[dict], reviews_checked: int, min_reviews: int, registry_issues: list[dict] | None = None,
           as_of: str | None = None) -> dict:
    """matches: one per (record, product) pair that is not tier 'none', each with tier, scope, local, authenticity,
    support, retracted, excluded, record_type, record_id, authority, title, published, url.
    hazards: radar findings with independent_groups (after corroboration), severity, with_photos.
    coverage_rows: coverage.matrix() rows (country level)."""
    registry_issues = registry_issues or []
    live = [m for m in matches if not m.get("retracted") and not m.get("excluded")]
    official = [m for m in live if m.get("authenticity") in ("authentic", "official_domain")]
    usable = [m for m in official if m.get("support") != "unsupported"]
    # An official record whose wording code couldn't tie to the claim, or a record from an unofficial address, is
    # never dropped silently: it becomes a possible match for a person, so it can't turn into "no notice found".
    doubtful = [{**m, "tier": "family_named" if m["tier"] == "exact" else m["tier"]}
                for m in live if m not in usable and m["tier"] in POSSIBLE_TIERS]
    review_reasons: list[str] = []
    basis, outcome = None, None
    recall_types = ("recall_notice",)

    confirmed = _best(usable, tier="exact", scope="in_scope", local=True, record_type=recall_types)
    abroad = _best(usable, tier="exact", scope=("in_scope", "batch_unknown"), local=False, record_type=recall_types)
    local_batch = _best(usable, tier="exact", scope="batch_unknown", local=True, record_type=recall_types)
    possible = _best(usable + doubtful, tier=("variant", "suspected_rebrand", "family_named"))
    exact_notice = _best(usable, tier="exact", record_type=("safety_notice", "incident_report"))
    seizure = _best(usable, record_type="seizure", local=True, tier=("exact", "variant", "family_named"))
    serious = [h for h in hazards if h.get("severity") in ("medium", "high")]
    substantiated = [h for h in serious if h.get("independent_groups", 0) >= 2
                     and (h.get("severity") == "high" or h.get("with_photos", 0) >= 1)]
    weak = [h for h in serious if h.get("independent_groups", 0) >= 2 or h.get("with_photos", 0) >= 1]
    corroborated_notice = exact_notice and any(h.get("independent_groups", 0) >= 1 for h in serious)

    if confirmed:
        outcome, basis = "confirmed_recall", "confirmed_recall"
    elif substantiated or corroborated_notice:
        outcome, basis = "substantiated_hazard_signal", "substantiated_hazard_signal"
    elif local_batch:
        outcome, basis = "potential_concern", "local_recall_batch_unknown"
    elif abroad:
        outcome, basis = "potential_concern", "recalled_abroad_same_model"
        review_reasons.append(f"Cross-border match: {abroad['authority']} recall {abroad['record_id']} names this "
                              f"model; a reviewer approves before it is shown as affecting {market_name}.")
    elif possible:
        outcome, basis = "potential_concern", "possible_match"
        review_reasons.append(f"Possible match ({possible['tier'].replace('_', ' ')}) with {possible['record_id']}: "
                              "a person compares the model code and photos.")
    elif seizure:
        outcome, basis = "potential_concern", "seizure_or_notice"
    elif weak or exact_notice:
        outcome, basis = "potential_concern", "hazard_reports"
    elif registry_issues:
        outcome, basis = "potential_concern", "registry_mismatch"

    market_row = next((r for r in coverage_rows if r.get("is_market")), None)
    answered = [r for r in coverage_rows if r["state"] in (CHECKED_LIVE, CHECKED_CACHE, NO_MATCH)]
    market_answered = bool(market_row and market_row["state"] in (CHECKED_LIVE, CHECKED_CACHE, NO_MATCH))
    identifiable = bool(product.get("model") or product.get("gtin") or product.get("brand"))
    brand_only = [m for m in usable if m["tier"] == "unresolved" and m.get("record_type") == "recall_notice"]
    if outcome is None and brand_only and not product.get("model"):
        # Without a model number, "no matching notice" would hide that this brand has recalls: say what's missing.
        outcome, basis = "insufficient_evidence", "brand_recalls_model_unknown"
    if outcome is None:
        if identifiable and (market_answered or answered):
            outcome, basis = "no_matching_notice_found", "no_matching_notice_found"
        else:
            outcome, basis = "insufficient_evidence", "insufficient_evidence"

    limitations = []
    if market and not market_answered:
        state = market_row["state"].replace("_", " ") if market_row else "not supported"
        limitations.append(f"{market_name}'s own regulator could not be checked ({state}); the answer rests on "
                           "other countries' sources.")
    if not market:
        limitations.append("The shopper's country is unknown, so no local regulator was chosen.")
    for row in coverage_rows:
        limitations += [n for n in row.get("notes", []) if row.get("is_market")]
    if reviews_checked < min_reviews:
        limitations.append(f"Only {reviews_checked} review(s) read; hazard signals need at least {min_reviews}.")
    if not product.get("model"):
        limitations.append("No model number, so notices could only be matched by brand and product type.")
    if outcome == "no_matching_notice_found":
        limitations.append("No matching notice in what was checked is not proof that the product is safe.")

    strength = evidence_strength(outcome, basis, confirmed or abroad or local_batch or possible, substantiated)
    identity = (confirmed or local_batch or abroad or possible or {}).get("tier") or (
        "unresolved" if not product.get("model") else "none")
    level = {"confirmed_recall": "high", "substantiated_hazard_signal": "high"}.get(outcome) or (
        "medium" if basis in ("local_recall_batch_unknown", "recalled_abroad_same_model") else
        "low" if outcome == "potential_concern" else "none" if outcome == "no_matching_notice_found" else "unknown")
    lead = confirmed or local_batch or abroad or possible or seizure or exact_notice
    return {
        "outcome": outcome, "basis": basis, "colour": COLOUR[outcome],
        "headline": HEADLINES.get(basis, HEADLINES.get(outcome, "")).format(market=market_name),
        "safety_concern": {"level": level, "text": HEADLINES.get(basis, "").format(market=market_name)},
        "evidence_strength": strength, "identity_confidence": identity,
        "lead_record": {k: lead.get(k) for k in LEAD_FIELDS} if lead else None,
        "review_required": bool(review_reasons), "review_reasons": review_reasons,
        "limitations": list(dict.fromkeys(limitations)), "policy_version": POLICY_VERSION, "as_of": as_of,
        "decided_by": "code (engine/evidence_verification/adjudicator.py); AI collected and explained the evidence",
    }


def evidence_strength(outcome: str, basis: str, match: dict | None, substantiated: list[dict]) -> str:
    """strong: an authentic official record for this exact model; moderate: an official record for the same model
    elsewhere, or several independent reports; weak: a single report, a variant or a family-level notice; none."""
    if basis == "confirmed_recall" and match and match.get("authenticity") == "authentic":
        return "strong"
    if basis == "confirmed_recall":
        return "moderate"
    if basis in ("recalled_abroad_same_model", "local_recall_batch_unknown") or substantiated:
        return "moderate"
    if outcome == "potential_concern":
        return "weak"
    return "none"
