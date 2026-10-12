"""Seed the fixed demo products (contracts/demo_products.json) into the database and build their twins.

    cd engine && PYTHONPATH=.. uv run python ../data/seed_demo.py          # local database (make db-up)
    DATABASE_URL=... (Cloud SQL via cloud-sql-proxy) for the cloud database

All brands, models and shops are fictional demo data.
"""
import json

from engine import identity

CHARGER_LOOK = {"housing_shape": "rounded_rectangle", "port_layout": "2x USB-C stacked", "colour": "white",
                "plug": "foldable Type C pins"}
DEMO = {
    "SS-P-10291": ("SS-L-0001", {
        "url": "https://demo.safeshelf.app/product/cx-65", "marketplace": "demo",
        "brand": "ExampleBrand", "model": "CX-65", "category": "usb_charger",
        "title": "ExampleBrand CX-65 65W GaN Fast Charger, 2 USB-C PD, Foldable Plug",
        "description": "65W gallium nitride wall charger with two USB-C Power Delivery ports.",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model CX-65 | Input 100-240V~ 50/60Hz 1.5A | Output 5V3A 9V3A 15V3A 20V3.25A 65W max | R-41XXXXXX",
        "certifications_claimed": ["BIS R-41XXXXXX"], "price": 1399, "currency": "INR"}),
    "SS-P-20019": ("SS-L-0002", {
        "url": "https://demo.safeshelf.app/product/cx-65-reseller", "marketplace": "demo",
        "brand": "ExampleBrand", "model": "CX-65", "category": "usb_charger",
        "title": "ExampleBrand 65W Charger CX-65 (2-port USB-C) - Reseller Pack",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model CX-65 | Input 100-240V~ 50/60Hz 1.5A | Output 20V3.25A 65W max | R-41XXXXXX",
        "certifications_claimed": ["BIS R-41XXXXXX"], "price": 1449, "currency": "INR"}),
    "SS-P-30118": ("SS-L-0003", {
        "url": "https://demo.safeshelf.app/product/vn-65pd", "marketplace": "demo",
        "brand": "VoltNova", "model": "VN-65PD", "category": "usb_charger",
        "title": "VoltNova VN-65PD 65W GaN Charger, Dual USB-C, Foldable Pins",
        "description": "Compact 65W charger, two USB-C PD ports.",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model VN-65PD | Input 100-240V~ 50/60Hz 1.5A | Output 5V3A 9V3A 15V3A 20V3.25A 65W max | R-41XXXXXX",
        "certifications_claimed": ["BIS R-41XXXXXX"], "price": 999, "currency": "INR"}),
    "SS-P-40007": ("SS-L-0004", {
        "url": "https://demo.safeshelf.app/product/ck-60", "marketplace": "demo",
        "brand": "ChargeKing", "model": "CK-60", "category": "usb_charger",
        "title": "ChargeKing CK-60 60W USB-C Charger, 2 Ports, Fast Charging",
        "attributes": {"power_watts": 60, "ports_usb_c": 2, "voltage": 20},
        "visual_features": {**CHARGER_LOOK, "plug": "fixed Type C pins"},
        "label_text": "Model CK-60 | Input 100-240V~ 1.6A | Output 20V3A 60W max",
        "price": 899, "currency": "INR"}),
    "SS-P-50001": ("SS-L-0005", {
        "url": "https://demo.safeshelf.app/product/vm-55u8", "marketplace": "demo",
        "brand": "ViewMax", "model": "VM-55U8", "category": "television",
        "title": "ViewMax VM-55U8 55-inch 4K UHD Smart TV, 5-Star Energy Rating",
        "attributes": {"screen_inches": 55},
        "certifications_claimed": ["Energy Rating 5 stars"], "price": 38999, "currency": "INR"}),
}


def main() -> None:
    for product_id, (listing_id, listing) in DEMO.items():
        fp = identity.register(product_id, listing_id, listing)
        print(f"{product_id}  {fp['brand']:<12} {fp['model']:<8} fingerprint v{fp['version']}")
    result = identity.duplicates("SS-P-10291", refresh=True)
    for m in result["matches"]:
        print(f"  {m['product_id']}  {m['relationship']:<21} {m['status']:<10} {m['confidence']}")
    print(json.dumps(result["matches"][0], indent=1)[:600])


if __name__ == "__main__":
    main()
