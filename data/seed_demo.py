"""Seed the fixed demo products (contracts/demo_products.json) into the database and build their twins.

    cd engine && PYTHONPATH=.. uv run python ../data/seed_demo.py          # local database (make db-up)
    DATABASE_URL=... (Cloud SQL via cloud-sql-proxy) for the cloud database

All brands, models and shops are fictional demo data.
"""
import json

from engine import identity, marks, safety, store

CHARGER_LOOK = {"housing_shape": "rounded_rectangle", "port_layout": "2x USB-C stacked", "colour": "white",
                "plug": "foldable Type C pins"}
DEMO = {
    "SS-P-10291": ("SS-L-0001", {
        "url": "https://demo.safeshelf.app/product/cx-65", "marketplace": "demo",
        "brand": "Kelvo", "model": "CX-65", "category": "usb_charger",
        "title": "Kelvo CX-65 65W GaN Fast Charger, 2 USB-C PD, Foldable Plug",
        "description": "65W gallium nitride wall charger with two USB-C Power Delivery ports.",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model CX-65 | Input 100-240V~ 50/60Hz 1.5A | Output 5V3A 9V3A 15V3A 20V3.25A 65W max | R-41097318",
        "certifications_claimed": ["BIS R-41097318"], "price": 1399, "currency": "INR"}),
    "SS-P-20019": ("SS-L-0002", {
        "url": "https://demo.safeshelf.app/product/cx-65-reseller", "marketplace": "demo",
        "brand": "Kelvo", "model": "CX-65", "category": "usb_charger",
        "title": "Kelvo 65W Charger CX-65 (2-port USB-C) - Reseller Pack",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model CX-65 | Input 100-240V~ 50/60Hz 1.5A | Output 20V3.25A 65W max | R-41097318",
        "certifications_claimed": ["BIS R-41097318"], "price": 1449, "currency": "INR"}),
    "SS-P-30118": ("SS-L-0003", {
        "url": "https://demo.safeshelf.app/product/vn-65pd", "marketplace": "demo",
        "brand": "VoltNova", "model": "VN-65PD", "category": "usb_charger",
        "title": "VoltNova VN-65PD 65W GaN Charger, Dual USB-C, Foldable Pins",
        "description": "Compact 65W charger, two USB-C PD ports.",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": CHARGER_LOOK,
        "label_text": "Model VN-65PD | Input 100-240V~ 50/60Hz 1.5A | Output 5V3A 9V3A 15V3A 20V3.25A 65W max | R-41097318",
        "certifications_claimed": ["BIS R-41097318"], "price": 999, "currency": "INR"}),
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
    "SS-P-60002": ("SS-L-0006", {
        "url": "https://demo.safeshelf.app/product/sv-65", "marketplace": "demo",
        "brand": "SafeVolt", "model": "SV-65", "category": "usb_charger",
        "title": "SafeVolt SV-65 65W USB-C Charger, 2 Ports, Fixed Pins, Over-Temperature Cut-off",
        "description": "65W two-port USB-C PD wall charger in a matte black cube housing.",
        "attributes": {"power_watts": 65, "ports_usb_c": 2, "voltage": 20},
        "visual_features": {"housing_shape": "cube", "port_layout": "2x USB-C side by side", "colour": "black",
                            "plug": "fixed Type C pins"},
        "label_text": "Model SV-65 | Input 100-240V~ 50/60Hz 1.6A | Output 5V3A 9V3A 15V3A 20V3.25A 65W max",
        "price": 1599, "currency": "INR"}),
}

# Fictional reviews of the hero charger: a rising run of heat complaints, plus the traps the Radar must ignore.
HERO_REVIEWS = [(d, r, t) for d, r, t in [
    ("2026-05-04", 5, "Charges my laptop and phone together, compact and light."),
    ("2026-05-11", 5, "This charger is fire 🔥 best 65W brick I've owned"),
    ("2026-05-19", 4, "Works fine. Gets a little warm under full load, which is normal."),
    ("2026-05-28", 5, "No overheating at all, even charging two devices."),
    ("2026-06-03", 3, "Charging speed is ok, cable not included which is annoying."),
    ("2026-06-12", 5, "Great value at this price."),
    ("2026-06-20", 4, "Lit charger, does what it says."),
    ("2026-06-29", 2, "My friend said hers got really hot, mine has been ok so far."),
    ("2026-07-02", 1, "Overheats when charging my laptop. Too hot to touch and the USB-C port looks discoloured."),
    ("2026-07-09", 5, "Folding pins are handy for travel."),
    ("2026-07-15", 4, "Good charger, slightly bulky."),
    ("2026-07-24", 1, "Melted on the first day. The plastic around the top port is black and it smelled of burning."),
    ("2026-07-30", 5, "Fast charging for my Pixel and iPad."),
    ("2026-08-06", 3, "Stopped working after a month, no lights."),
    ("2026-08-12", 1, "Woke up to a burning smell. The charger was scorched around the port, unplugged it fast."),
    ("2026-08-18", 5, "Never gets hot, unlike my old one."),
    ("2026-08-25", 1, "Port melted while charging overnight. Photos attached. Do not leave this plugged in."),
    ("2026-08-30", 4, "Decent, but the second port charges slower."),
    ("2026-09-04", 1, "Sparks from the USB-C port when I plugged in my laptop cable, then it died."),
    ("2026-09-09", 5, "Perfect for my desk setup."),
    ("2026-09-15", 1, "Overheated and deformed after a week of normal use. Scary."),
    ("2026-09-21", 4, "Works as described."),
    ("2026-09-26", 1, "Smoke came out of it while charging my phone. Threw it away."),
    ("2026-10-01", 5, "Bought a second one for the office."),
]]


# Fictional reviews of the safer alternative: enough of them, none reporting a hazard.
ALTERNATIVE_REVIEWS = [(f"2026-{m:02d}-{d:02d}", r, t) for (m, d), r, t in zip(
    [(5, 2), (5, 9), (5, 16), (5, 23), (5, 30), (6, 6), (6, 13), (6, 20), (6, 27), (7, 4), (7, 11), (7, 18),
     (7, 25), (8, 1), (8, 8), (8, 15), (8, 22), (8, 29), (9, 5), (9, 12), (9, 19), (9, 26), (10, 3), (10, 8)],
    [5, 4, 5, 5, 3, 5, 4, 5, 4, 5, 5, 4, 2, 5, 4, 5, 5, 3, 5, 4, 5, 5, 4, 5],
    ["Charges my laptop and phone at full speed.", "Solid build, stays cool on my desk.",
     "Good charger, a bit heavy.", "Using it every day for three months, no issues.",
     "Works, but the box was damaged in delivery.", "Fast charging for my MacBook Air.",
     "Barely warm even with two devices.", "Great for travel, fits in my bag pocket.",
     "Does what it says, nothing more.", "Replaced my old brick with this one.",
     "Second port gives full power too.", "Nice matte finish, no fingerprints.",
     "Pins are not foldable, which I didn't like.", "Charges my Pixel quickly.",
     "Cable not included, otherwise fine.", "Reliable, bought one for my parents.",
     "Good value for 65W.", "Slight coil whine at night, otherwise ok.",
     "Works with my Dell laptop.", "Stays cool, solid feel.", "Quick and compact.",
     "No problems after daily use.", "Good charger for the price.", "Charges both devices at once without slowing down."])]


def seed_alternative() -> None:
    reviews = [{"id": f"demo-alt-{i:02d}", "date": d, "rating": r, "text": t}
               for i, (d, r, t) in enumerate(ALTERNATIVE_REVIEWS)]
    safety.add_reviews("SS-P-60002", reviews)
    answer = safety.safety("SS-P-60002")
    print(f"safety SS-P-60002: {answer['verdict']}, {answer['reviews_checked']} reviews, "
          f"{len(answer['ai_findings'])} findings")


def seed_reviews() -> None:
    reviews = [{"id": f"demo-{i:02d}", "date": d, "rating": r, "text": t} for i, (d, r, t) in enumerate(HERO_REVIEWS)]
    safety.add_reviews("SS-P-10291", reviews)
    answer = safety.safety("SS-P-10291")
    print(f"safety SS-P-10291: {answer['verdict']}, {answer['reviews_checked']} reviews")
    for f in answer["ai_findings"]:
        print(f"  {f['hazard_type']} {f['severity']} reports={f['independent_reports']} trend={f['trend']} "
              f"first={f['first_seen']} | {f['mechanism']}")


def seed_registry_demo() -> None:
    """One clearly marked demo row: the fictional ViewMax TV is registered at 3 stars (the listing claims 5)."""
    store.conn().execute(
        """INSERT INTO registry_energy_rating (registration_number, appliance_type, brand, model, star_rating, status, raw)
           VALUES ('ATV-DEMO-0001', 'tv', 'ViewMax', 'VM-55U8', 3, 'Approved', '{"demo": true}')
           ON CONFLICT (appliance_type, brand, model) DO NOTHING""")
    for check in marks.certifications("SS-P-50001")["checks"]:
        print(f"certification SS-P-50001: {check['authority']} {check['result']} {check.get('field') or ''} "
              f"claimed={check.get('claimed_value')} registry={check.get('registry_value')}")


def main() -> None:
    for product_id, (listing_id, listing) in DEMO.items():
        fp = identity.register(product_id, listing_id, listing)
        print(f"{product_id}  {fp['brand']:<12} {fp['model']:<8} fingerprint v{fp['version']}")
    result = identity.duplicates("SS-P-10291", refresh=True)
    for m in result["matches"]:
        print(f"  {m['product_id']}  {m['relationship']:<21} {m['status']:<10} {m['confidence']}")
    print(json.dumps(result["matches"][0], indent=1)[:600])
    seed_reviews()
    seed_alternative()
    seed_registry_demo()


if __name__ == "__main__":
    main()
