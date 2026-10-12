# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32", "psycopg[binary]>=3.2"]
# ///
"""M1: load CPSC recalls (US recall list) into data/raw/ and, with --db, into the recalls table.

    uv run data/load_cpsc.py --from 2019 --to 2026 --summary
    uv run data/load_cpsc.py --db "$DATABASE_URL"

Also writes data/raw/cpsc_backtest_candidates.jsonl: recalls that mention Amazon, are fire/burn/shock
hazards in electrical products, and are dated before Aug 2023 (Amazon Reviews 2023 ends around Sep 2023).
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

import requests

RAW = Path(__file__).parent / "raw"
API = "https://www.saferproducts.gov/RestWebServices/Recall"

FIRE = re.compile(r"\b(fire|burn|overheat\w*|melt\w*|shock|electrocution|explo\w*|smok\w*)", re.I)
ELECTRICAL = re.compile(
    r"\b(charger|power ?bank|battery|batteries|adapter|cable|heater|hoverboard|e-?bike|scooter|"
    r"extension cord|power strip|lithium|usb|outlet|lamp|light)\b",
    re.I,
)
BACKTEST_CUTOFF = "2023-08-01"


def fetch_year(year: int, attempts: int = 6) -> list[dict]:
    params = {"format": "json", "RecallDateStart": f"{year}-01-01", "RecallDateEnd": f"{year}-12-31"}
    for attempt in range(1, attempts + 1):
        # The CPSC server rejects the default python-requests User-Agent with 403.
        response = requests.get(API, params=params, timeout=120, headers={"User-Agent": "SafeShelf-research/0.1"})
        response.raise_for_status()
        recalls = [r for r in response.json() if r.get("RecallNumber")]
        # The API sometimes answers a whole year with one empty record; CPSC issues 200+ a year.
        if len(recalls) >= 50:
            return recalls
        print(f"  {year}: only {len(recalls)} recalls (attempt {attempt}/{attempts}); retrying")
        time.sleep(10 * attempt)
    raise SystemExit(f"CPSC API kept returning an incomplete {year}; nothing was saved, try again later")


def text_of(recall: dict) -> str:
    parts = [recall.get("Title") or "", recall.get("Description") or ""]
    for key in ("Products", "Hazards", "Retailers"):
        parts += [json.dumps(item) for item in recall.get(key) or []]
    return " ".join(parts)


def hazard_of(recall: dict) -> str:
    return "; ".join(h.get("Name", "") for h in recall.get("Hazards") or [])


def is_backtest_candidate(recall: dict) -> bool:
    text = text_of(recall)
    return (
        "amazon" in text.lower()
        and bool(FIRE.search(hazard_of(recall) or text))
        and bool(ELECTRICAL.search(text))
        and (recall.get("RecallDate") or "") < BACKTEST_CUTOFF
    )


def to_row(recall: dict) -> dict:
    return {
        "id": f"cpsc:{recall['RecallNumber']}",
        "authority": "CPSC",
        "notice_date": (recall.get("RecallDate") or "")[:10] or None,
        "title": recall.get("Title"),
        "hazard": hazard_of(recall),
        "scope_json": {
            k: recall.get(k)
            for k in ("Products", "Images", "Retailers", "Manufacturers", "Importers", "Distributors", "Injuries")
        },
        "url": recall.get("URL"),
    }


def save_to_db(rows: list[dict], db_url: str) -> None:
    import psycopg
    from psycopg.types.json import Jsonb

    with psycopg.connect(db_url) as conn:
        conn.cursor().executemany(
            """INSERT INTO recalls (id, authority, notice_date, title, hazard, scope_json, url)
               VALUES (%(id)s, %(authority)s, %(notice_date)s, %(title)s, %(hazard)s, %(scope_json)s, %(url)s)
               ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, hazard = EXCLUDED.hazard,
                   scope_json = EXCLUDED.scope_json, url = EXCLUDED.url""",
            [{**r, "scope_json": Jsonb(r["scope_json"])} for r in rows],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="start", type=int, default=2019)
    parser.add_argument("--to", dest="end", type=int, default=2026)
    parser.add_argument("--db", default=os.environ.get("DATABASE_URL"), help="Postgres URL; omit to write files only")
    parser.add_argument("--summary", action="store_true", help="print counts")
    args = parser.parse_args()

    RAW.mkdir(exist_ok=True)
    recalls = []
    for year in range(args.start, args.end + 1):
        batch = fetch_year(year)
        print(f"{year}: {len(batch)} recalls")
        recalls += batch

    with open(RAW / "cpsc_recalls.jsonl", "w") as f:
        for recall in recalls:
            f.write(json.dumps(recall) + "\n")
    candidates = [r for r in recalls if is_backtest_candidate(r)]
    with open(RAW / "cpsc_backtest_candidates.jsonl", "w") as f:
        for recall in candidates:
            f.write(json.dumps(to_row(recall)) + "\n")

    if args.summary:
        amazon = sum("amazon" in text_of(r).lower() for r in recalls)
        print(f"total {len(recalls)} · mention Amazon {amazon} · backtest candidates {len(candidates)}")
        for row in [to_row(r) for r in candidates][:10]:
            print(f"  {row['notice_date']}  {row['id']:<12} {row['title'][:90]}")

    if args.db:
        save_to_db([to_row(r) for r in recalls], args.db)
        print(f"saved {len(recalls)} recalls to the database")


if __name__ == "__main__":
    main()
