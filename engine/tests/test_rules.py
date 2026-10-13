from engine.normalize import normalise
from engine.rules import decide, inherits_recall

CX65 = normalise({"brand": "ExampleBrand", "model": "CX-65", "category": "usb_charger",
                  "title": "ExampleBrand 65W GaN charger, 2 USB-C"})
CX65_COPY = normalise({"brand": "Example Brand", "model": "cx 65", "category": "usb_charger",
                       "title": "65W fast charger 2 USB-C"})
REBRAND = normalise({"brand": "VoltNova", "model": "VN-65PD", "category": "usb_charger",
                     "title": "VoltNova 65W charger, 2 USB-C"})
LOOKALIKE = normalise({"brand": "ChargeKing", "model": "CK-60", "category": "usb_charger",
                       "title": "ChargeKing 60W charger, 2 USB-C"})
NO_MODEL = normalise({"brand": "Generic", "category": "usb_charger", "title": "Fast charger 65W 2 USB-C"})


def test_same_brand_and_model_is_verified_exact_even_if_gemini_disagrees():
    d = decide(CX65, CX65_COPY, {"proposed_class": "visually_similar", "confidence": 0.4})
    assert (d.relationship, d.status) == ("exact_model", "verified")
    assert inherits_recall(d.relationship, d.status)


def test_different_model_numbers_are_never_exact():
    d = decide(CX65, LOOKALIKE, {"proposed_class": "exact_model", "confidence": 0.99})
    assert d.relationship == "visually_similar"
    assert not inherits_recall(d.relationship, d.status)
    assert any("power_watts" in r for r in d.reasons)


def test_rebrand_needs_human_review():
    d = decide(CX65, REBRAND, {"proposed_class": "rebranded_equivalent", "confidence": 0.9})
    assert (d.relationship, d.status) == ("rebranded_equivalent", "unverified")
    assert not inherits_recall(d.relationship, d.status)
    assert inherits_recall("rebranded_equivalent", "verified")  # after a human verifies it


def test_rebrand_with_conflicting_specs_is_only_similar():
    d = decide(CX65, LOOKALIKE, {"proposed_class": "rebranded_equivalent", "confidence": 0.9})
    assert d.relationship == "visually_similar"


def test_same_model_with_different_wattage_is_a_variant():
    other = normalise({"brand": "ExampleBrand", "model": "CX-65", "category": "usb_charger", "title": "45W"})
    d = decide(CX65, other, {"proposed_class": "exact_model"})
    assert (d.relationship, d.status) == ("model_variant", "unverified")


def test_missing_model_number_can_never_be_exact_or_verified():
    d = decide(CX65, NO_MODEL, {"proposed_class": "exact_model", "confidence": 0.95})
    assert d.relationship != "exact_model" and d.status == "unverified"


def test_unknown_class_from_gemini_falls_back_to_similar():
    d = decide(CX65, LOOKALIKE, {"proposed_class": "same_thing"})
    assert d.relationship == "visually_similar"
