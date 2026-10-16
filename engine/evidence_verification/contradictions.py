"""Contradiction and disconfirmation search (plan v2.2 J1, J3 step 5).

Looks through what was retrieved for: corrections and retractions, models or batches a notice says are NOT affected,
other models named where the shopper's product isn't, and alternative explanations for a hazard report (third-party
charger, misuse, water damage). "No report found" is missing evidence, never a contradiction.

    find(product, records, reviews=None) -> [{kind, record_id, text, effect}]   effect: retract | downgrade | note
"""
import re

from engine import locales

RETRACTION = re.compile(r"\b(retract\w*|withdrawn|rescind\w*|cancel+ed (?:recall|notice)|recall (?:is )?(?:closed|"
                        r"terminated))\b|取り下げ|撤回|取消", re.IGNORECASE)
CORRECTION = re.compile(r"\b(correction|corrected|amended|revised notice|update to (?:the )?(?:recall|notice))\b|訂正",
                        re.IGNORECASE)
NOT_AFFECTED = re.compile(
    r"(?:(?:are|is) not (?:affected|included|part of (?:this|the) recall|subject to (?:this|the) recall)|"
    r"not (?:affected|included) by (?:this|the) recall|unaffected|excluded from (?:this|the) recall|"
    r"対象外|対象ではありません|含まれません)", re.IGNORECASE)
ALTERNATIVE_CAUSE = re.compile(
    r"\b(third[- ]party (?:charger|cable|adapter)|non[- ]original (?:charger|cable)|wrong (?:charger|voltage)|"
    r"dropped|water damage|got wet|misuse|modified|counterfeit charger|left in (?:a|the) (?:hot )?car)\b|非純正|改造",
    re.IGNORECASE)
SENTENCE = re.compile(r"[^.。!?\n]+[.。!?\n]?")


def _sentences_with(text: str, pattern: re.Pattern) -> list[str]:
    return [s.strip() for s in SENTENCE.findall(text or "") if pattern.search(s)]


def find(product: dict, records: list[dict], reviews: list[dict] | None = None) -> list[dict]:
    model = locales.comparable_model(product.get("model"))
    batch = locales.comparable_model(product.get("batch"))
    out = []
    for r in records:
        text = " ".join(str(r.get(k) or "") for k in ("title", "hazard", "remedy", "original_text"))
        rid = r.get("record_id")
        if RETRACTION.search(r.get("title") or "") or r.get("record_type") == "correction" and RETRACTION.search(text):
            out.append({"kind": "retraction", "record_id": rid, "text": (r.get("title") or "")[:200],
                        "effect": "retract"})
        elif CORRECTION.search(r.get("title") or ""):
            out.append({"kind": "correction", "record_id": rid, "text": (r.get("title") or "")[:200],
                        "effect": "note"})
        for sentence in _sentences_with(text, NOT_AFFECTED):
            folded = locales.comparable_model(sentence)
            if model and len(model) >= 3 and model in folded:
                out.append({"kind": "unaffected_model", "record_id": rid, "text": sentence[:240],
                            "effect": "retract"})
            elif batch and len(batch) >= 3 and batch in folded:
                out.append({"kind": "unaffected_batch", "record_id": rid, "text": sentence[:240],
                            "effect": "retract"})
    for review in reviews or []:
        for sentence in _sentences_with(review.get("text") or "", ALTERNATIVE_CAUSE):
            out.append({"kind": "alternative_cause", "record_id": review.get("evidence_id") or review.get("id"),
                        "text": sentence[:240], "effect": "note"})
    return out


def retracted_records(found: list[dict]) -> set[str]:
    return {c["record_id"] for c in found if c["effect"] == "retract" and c["kind"] in ("retraction",)}


def excluded_records(found: list[dict]) -> set[str]:
    """Records that say the shopper's model or batch is not covered."""
    return {c["record_id"] for c in found if c["kind"] in ("unaffected_model", "unaffected_batch")}
