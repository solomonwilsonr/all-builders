# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32", "psycopg[binary]>=3.2"]
# ///
"""M1: load the Australian energy-rating registry (official, open data) for the safety-mark check (M5).

    uv run data/load_au_registry.py                 # TVs and fridges -> data/raw/au_*.csv
    uv run data/load_au_registry.py --types tv rf ac --db "$DATABASE_URL"

File names on data.gov.au change every day, so the latest CSV is looked up through the CKAN API.
The registry covers appliances (TVs, fridges, air conditioners, washers, monitors), not chargers.
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path

import requests

RAW = Path(__file__).parent / "raw"
CKAN = "https://data.gov.au/data/api/3/action/package_show?id=energy-rating-for-household-appliances"

# Resource names start with these words; the short code is the CSV prefix (tv_2026_10_12.csv).
TYPES = {
    "tv": "Televisions",
    "rf": "Fridges and Freezers",
    "ac": "Air Conditioners",
    "cw": "Clothes Washers",
    "cd": "Clothes Dryers",
    "dw": "Dishwashers",
    "mo": "Computer Monitors",
}

# Column names differ between appliance types.
BRAND_COLUMNS = ("Brand_Reg", "Brand")
MODEL_COLUMNS = ("Model_No", "Model No")
STAR_COLUMNS = ("Star2", "Star2009", "Star", "Star Rating (old)")


def latest_csv_urls() -> dict[str, str]:
    resources = requests.get(CKAN, timeout=60).json()["result"]["resources"]
    urls = {}
    for code, name in TYPES.items():
        for resource in resources:
            if resource["format"].upper() == "CSV" and resource["name"].strip().startswith(name):
                urls[code] = resource["url"]
                break
    return urls


def first(row: dict, columns: tuple[str, ...]) -> str | None:
    for column in columns:
        value = (row.get(column) or "").strip()
        if value and value.upper() not in ("N/A", "-"):
            return value
    return None


def to_row(code: str, row: dict) -> dict | None:
    brand, model = first(row, BRAND_COLUMNS), first(row, MODEL_COLUMNS)
    if not brand or not model:
        return None
    star = first(row, STAR_COLUMNS)
    try:
        star_rating = float(star) if star else None
    except ValueError:
        star_rating = None
    return {
        "registration_number": row.get("Registration Number"),
        "appliance_type": code,
        "brand": brand,
        "model": model,
        "star_rating": star_rating,
        "status": row.get("SubmitStatus"),
        "raw": row,
    }


def save_to_db(rows: list[dict], db_url: str) -> None:
    import psycopg
    from psycopg.types.json import Jsonb

    with psycopg.connect(db_url) as conn:
        conn.cursor().executemany(
            """INSERT INTO registry_energy_rating
                   (registration_number, appliance_type, brand, model, star_rating, status, raw)
               VALUES (%(registration_number)s, %(appliance_type)s, %(brand)s, %(model)s,
                       %(star_rating)s, %(status)s, %(raw)s)
               ON CONFLICT (appliance_type, brand, model) DO UPDATE SET
                   registration_number = EXCLUDED.registration_number,
                   star_rating = EXCLUDED.star_rating, status = EXCLUDED.status, raw = EXCLUDED.raw""",
            [{**r, "raw": Jsonb(r["raw"])} for r in rows],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--types", nargs="+", default=["tv", "rf"], choices=sorted(TYPES))
    parser.add_argument("--db", default=os.environ.get("DATABASE_URL"), help="Postgres URL; omit to write files only")
    args = parser.parse_args()

    RAW.mkdir(exist_ok=True)
    urls = latest_csv_urls()
    for code in args.types:
        text = requests.get(urls[code], timeout=300).content.decode("utf-8-sig", errors="replace")
        (RAW / f"au_{code}.csv").write_text(text)
        rows = [r for r in map(lambda row: to_row(code, row), csv.DictReader(io.StringIO(text))) if r]
        # Keep one row per brand + model (the latest registration wins).
        unique = {(r["brand"], r["model"]): r for r in rows}
        rated = sum(r["star_rating"] is not None for r in unique.values())
        print(f"{code}: {len(unique)} models, {rated} with a star rating")
        if args.db:
            save_to_db(list(unique.values()), args.db)
            print(f"  saved to the database")
        sample = next(iter(unique.values()), None)
        if sample:
            print("  e.g.", json.dumps({k: sample[k] for k in ("brand", "model", "star_rating", "registration_number")}))


if __name__ == "__main__":
    main()
