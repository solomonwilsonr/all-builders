from engine.passport import mask_pii


def test_mask_pii_hides_contact_details_and_names():
    text = "Hi, my name is Ravi Kumar, call +91 98765 43210 or ravi.k@example.com. It melted."
    masked = mask_pii(text)
    assert "Ravi" not in masked and "98765" not in masked and "example.com" not in masked
    assert masked.endswith("It melted.")


def test_mask_pii_keeps_product_numbers():
    text = "Input 100-240V 1.5A, model CX-65, output 20V3.25A, R-41001234"
    assert mask_pii(text) == text
