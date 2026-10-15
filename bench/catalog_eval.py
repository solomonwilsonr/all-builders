"""M14a test: a seeded catalog with known answers, scanned by engine.catalog, scored for precision and speed.

    cd engine && PYTHONPATH=.. uv run python ../bench/catalog_eval.py            # build (once) + scan + score

bench/catalog_test.csv (the catalog) and bench/catalog_truth.json (expected finding per row) are built from the
database: listings of really recalled products, rows naming a model number from a recall notice, TVs claiming two
more energy stars than the Australian registry records (and some claiming the right number), and normal products
from brands with no recall. The TV star claims are test inputs we wrote, not real listings.
Writes bench/catalog_results.json.
"""
import csv
import json
import random
import re
from pathlib import Path

from engine import catalog, recalls, store

HERE = Path(__file__).parent
CSV = HERE / "catalog_test.csv"
TRUTH = HERE / "catalog_truth.json"
OUT = HERE / "catalog_results.json"
FIELDS = ["title", "brand", "model", "price"]


def build(seed: int = 7) -> None:
    rng = random.Random(seed)
    conn = store.conn()
    rows: list[tuple[dict, str | None]] = []

    recalled = conn.execute(
        """SELECT DISTINCT ON (p.id) p.id, p.brand, p.model, l.title, l.raw->>'price' AS price
           FROM recall_products r JOIN products p ON p.id = r.product_id JOIN listings l ON l.product_id = p.id
           WHERE l.title IS NOT NULL ORDER BY p.id""").fetchall()
    for r in rng.sample(recalled, min(40, len(recalled))):
        rows.append(({"title": r["title"], "brand": r["brand"], "model": r["model"] or "", "price": r["price"] or ""},
                     "possible_recall_match"))

    # CPSC leaves the Model field empty; the model numbers are in the notice text, read once by Gemini
    # (recalls.notice_models, cached). Use electrical recalls whose notice names at least one model number.
    notices = conn.execute(
        """SELECT id, title, scope_json FROM recalls WHERE title ~* '(charger|power bank|heater|battery|adapter)'
           AND notice_date >= '2021-01-01' ORDER BY id""").fetchall()
    picked = 0
    for notice in rng.sample(notices, len(notices)):
        brand = (re.match(r"(?:\w+ )?(.+?) Recalls", notice["title"] or "") or [None, None])[1]
        if not brand or len(brand) > 25:
            continue
        models = sorted(recalls.notice_models(notice))
        if not models:
            continue
        product = (notice["scope_json"].get("Products") or [{}])[0].get("Name") or ""
        rows.append(({"title": f"{brand} {product} {models[0]}".strip(), "brand": brand, "model": models[0],
                      "price": ""}, "recall_match"))
        picked += 1
        if picked == 10:
            break

    tvs = conn.execute(
        """SELECT brand, model, star_rating FROM registry_energy_rating
           WHERE appliance_type = 'tv' AND star_rating BETWEEN 2 AND 7 AND NOT (raw ? 'demo') ORDER BY model""").fetchall()
    for i, tv in enumerate(rng.sample(tvs, 15)):
        claimed = tv["star_rating"] + 2 if i < 10 else tv["star_rating"]
        rows.append(({"title": f"{tv['brand']} {tv['model']} Smart TV, {claimed:g} Star Energy Rating",
                      "brand": tv["brand"], "model": tv["model"], "price": ""},
                     "certification_mismatch" if i < 10 else None))

    # Normal rows: brands that appear in no recall notice at all, so a finding on them is unexpected.
    notice_text = " ".join(r["t"] for r in conn.execute(
        "SELECT lower(coalesce(title, '') || ' ' || scope_json::text) AS t FROM recalls").fetchall())
    normal = conn.execute(
        """SELECT p.brand, p.model, l.title, l.raw->>'price' AS price FROM products p JOIN listings l ON l.product_id = p.id
           WHERE p.id LIKE 'SS-P-AMZ-%%' AND p.id NOT IN (SELECT product_id FROM recall_products)
           ORDER BY p.id""").fetchall()
    normal = [n for n in normal if len(n["brand"] or "") >= 3 and (n["brand"] or "").lower() not in notice_text]
    for n in rng.sample(normal, 500 - len(rows)):
        rows.append(({"title": n["title"], "brand": n["brand"] or "", "model": n["model"] or "",
                      "price": n["price"] or ""}, "none"))

    rng.shuffle(rows)
    with CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(r for r, _ in rows)
    # CSV row numbers start at 2 (row 1 is the header)
    TRUTH.write_text(json.dumps({str(i + 2): expected for i, (_, expected) in enumerate(rows)}, indent=0))
    print(f"wrote {len(rows)} rows -> {CSV}")


def score() -> None:
    truth = json.loads(TRUTH.read_text())
    answer = catalog.scan({"csv_text": CSV.read_text()})
    found = {str(r["row"]): r["finding"] for r in answer["results"]}
    expected = {row: f for row, f in truth.items() if f not in (None, "none")}
    hits = {row for row in found if row in expected}
    exact = {row for row in hits if found[row] == expected[row]}
    unexpected = [r for r in answer["results"] if str(r["row"]) not in expected]
    per_kind = {kind: {"expected": sum(f == kind for f in expected.values()),
                       "found": sum(found.get(row) == kind for row in expected if expected[row] == kind)}
                for kind in sorted(set(expected.values()))}
    result = {
        "rows": answer["listings_checked"], "findings": len(found), "expected_findings": len(expected),
        "precision": round(len(hits) / max(len(found), 1), 2),
        "recall": round(len(hits) / max(len(expected), 1), 2),
        "same_finding_type": round(len(exact) / max(len(hits), 1), 2),
        "per_kind": per_kind,
        "unexpected_findings": [{k: r.get(k) for k in ("row", "listing_title", "finding", "reason")} for r in unexpected],
        "seconds": answer["seconds"], "seconds_per_1000_listings": answer["seconds_per_1000_listings"],
        "gemini_compares": answer["gemini_compares"], "summary": answer["summary"],
        "note": "Unexpected findings are not automatically wrong: a 'normal' product can carry real buyer hazard reports.",
    }
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in result.items() if k != "unexpected_findings"}, indent=1, ensure_ascii=False))
    for r in result["unexpected_findings"][:10]:
        print(f"  unexpected row {r['row']}: {r['finding']} | {r['listing_title'][:60]} | {r['reason'][:80]}")


if __name__ == "__main__":
    if not CSV.exists():
        build()
    score()
