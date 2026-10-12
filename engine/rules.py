"""M3 step 06: code, not the model, decides the relationship class (SAFESHELF.md 7.1 and 7.4).

Gemini proposes a class with agreements and conflicts. These rules decide, so an LLM never moves a
recall from one product to another on its own:
- exact_model needs a matching authoritative identifier (GTIN or model number);
- different model numbers are never exact_model;
- rebranded_equivalent is always unverified until a human verifies it;
- only exact_model (verified) and human-verified rebranded_equivalent inherit a recall.
"""
from dataclasses import dataclass, field

CLASSES = ("exact_model", "rebranded_equivalent", "model_variant", "visually_similar", "shared_component")
# Attributes where any difference means "not the same model".
KEY_ATTRIBUTES = ("power_watts", "capacity_mah", "voltage", "ports_usb_c", "ports_usb_a")


@dataclass
class Decision:
    relationship: str
    status: str  # verified | unverified | rejected
    confidence: float
    reasons: list[str] = field(default_factory=list)


def attribute_conflicts(a: dict, b: dict) -> list[str]:
    out = []
    for key in KEY_ATTRIBUTES:
        va, vb = a.get(key), b.get(key)
        if va is not None and vb is not None and float(va) != float(vb):
            out.append(f"{key} differs ({va} vs {vb})")
    return out


def decide(a: dict, b: dict, proposal: dict) -> Decision:
    """a, b: normalised fingerprints (engine.normalize.normalise). proposal: Gemini's comparison."""
    proposed = proposal.get("proposed_class") if proposal.get("proposed_class") in CLASSES else "visually_similar"
    confidence = float(proposal.get("confidence") or 0.5)
    conflicts = attribute_conflicts(a["attributes"], b["attributes"])
    same_brand = bool(a["brand_norm"]) and a["brand_norm"] == b["brand_norm"]
    gtin_match = bool(a.get("gtin")) and a.get("gtin") == b.get("gtin")
    models_known = bool(a["model_norm"]) and bool(b["model_norm"])
    model_match = models_known and a["model_norm"] == b["model_norm"]

    if gtin_match or (model_match and same_brand):
        if conflicts:
            return Decision("model_variant", "unverified", min(confidence, 0.8),
                            ["same identifier but key specs differ", *conflicts])
        return Decision("exact_model", "verified", max(confidence, 0.95),
                        ["same GTIN" if gtin_match else f"same brand and model number {a['model_norm']}"])

    if models_known and not model_match:
        if proposed == "rebranded_equivalent" and not same_brand and not conflicts:
            return Decision("rebranded_equivalent", "unverified", min(confidence, 0.85),
                            ["different brand and model number, same hardware proposed: needs human review"])
        if proposed == "model_variant" and same_brand:
            return Decision("model_variant", "unverified", min(confidence, 0.8), ["same brand, different model"])
        if proposed == "shared_component":
            return Decision("shared_component", "unverified", min(confidence, 0.7), ["shared part proposed"])
        return Decision("visually_similar", "unverified", min(confidence, 0.6),
                        [f"model numbers differ ({a['model_norm']} vs {b['model_norm']})", *conflicts])

    # Identifier missing on one side: never verified, and exact_model can't be proven.
    if proposed == "exact_model":
        proposed = "visually_similar" if conflicts else ("model_variant" if same_brand else "rebranded_equivalent")
    if proposed == "rebranded_equivalent" and (same_brand or conflicts):
        proposed = "model_variant" if same_brand else "visually_similar"
    return Decision(proposed, "unverified", min(confidence, 0.7), ["model number missing: needs human review", *conflicts])


def inherits_recall(relationship: str, status: str) -> bool:
    return status == "verified" and relationship in ("exact_model", "rebranded_equivalent")
