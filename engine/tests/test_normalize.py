from engine.normalize import attributes, brand_blind_text, model_candidates, norm_model, normalise


def test_model_numbers_compare_without_punctuation():
    assert norm_model("CX-65") == norm_model("cx 65") == "CX65"
    assert norm_model("CX-65") != norm_model("CX-650")


def test_units_and_ports():
    attrs = attributes("VRURC 10000mAh power bank, 22.5W PD, 2 USB-C + 1 USB-A, 5V")
    assert attrs == {"capacity_mah": 10000, "power_watts": 22.5, "voltage": 5, "ports_usb_c": 2, "ports_usb_a": 1}


def test_model_candidates_skip_units_and_standards():
    assert model_candidates("Anker 535 Power Bank (PowerCore 20K) A1366 65W USB-C PD") == ["A1366"]
    assert model_candidates("VRURC OD-B7 wall plug charger 20W") == ["ODB7"]


def test_explicit_fields_win_over_text():
    fp = normalise({"brand": "VoltNova", "model": "VN-65PD", "title": "charger 60W", "attributes": {"power_watts": 65}})
    assert fp["model_norm"] == "VN65PD" and fp["attributes"]["power_watts"] == 65


def test_brand_blind_text_drops_the_brand():
    listing = {"brand": "VoltNova", "title": "VoltNova 65W charger", "category": "usb_charger"}
    assert "voltnova" not in brand_blind_text(listing, normalise(listing)).lower()


def test_count_words_become_port_counts():
    assert attributes("VoltNova 65W GaN Charger Dual USB-C")["ports_usb_c"] == 2
