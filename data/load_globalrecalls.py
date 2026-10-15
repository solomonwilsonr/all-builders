# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32", "psycopg[binary]>=3.2"]
# ///
"""M1: load JAPAC recalls (Australia, Japan, Korea, Singapore, ASEAN, Taiwan) from the OECD GlobalRecalls portal into
data/raw/ and, with --db, into the recalls table next to the CPSC ones.

    uv run data/load_globalrecalls.py --from 2019 --summary
    uv run data/load_globalrecalls.py --db "$DATABASE_URL"

GlobalRecalls collects the regulators' own notices (ACCC, Consumer Affairs Agency, KATS, ...) behind an open JSON API,
so this works where productsafety.gov.au and meti.go.jp answer 403. New Zealand and India are not in it.
Notices are cached in raw/globalrecalls.jsonl by uri: a rerun only fetches new ones.
"""
import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RAW = Path(__file__).parent / "raw"
CACHE = RAW / "globalrecalls.jsonl"
API = "https://globalrecalls.oecd.org/ws"
PAGE = 20  # the API's fixed page size

# Country of the recall -> the regulator that issued it (as named in the notices' source links).
AUTHORITIES = {"AU": "ACCC", "JP": "CAA", "KR": "KATS", "SG": "CPSO", "TW": "BSMI", "MY": "ASEAN", "ID": "ASEAN",
               "TH": "ASEAN", "PH": "ASEAN", "VN": "ASEAN"}


def get(path: str, attempts: int = 4, **params) -> dict:
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(f"{API}/{path}", params=params, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt == attempts:
                raise
            time.sleep(3 * attempt)


def search(country: str, start: str, end: str) -> list[dict]:
    """Every notice recalled in one country between two dates (search results only: no hazard or models)."""
    query = f"(country-were-recalled:{country}) AND date GE {start} AND date LE {end}"
    found, offset, total = [], 0, None
    while total is None or offset < total:
        page = get("search.xqy", q=query, start=offset, end=offset + PAGE, lang="en", uiLang="en")
        total = page["total"]
        found += page["results"]
        if not page["results"]:
            break
        offset += PAGE
    return found


def detail(uri: str) -> dict:
    return get("getrecall.xqy", uri=uri, uiLang="en")["recall"]


def to_row(recall: dict) -> dict:
    """Shaped like a CPSC row, so engine/recalls.py reads it the same way. The model field is free text (JAN codes,
    lot numbers, "Model: GCV22-F"), so it goes in the description, where the notice reader picks out model numbers."""
    country = recall["countryId"]
    description = " ".join(x for x in (recall.get("product.modelAndVolume"), recall.get("product.desc")) if x)
    return {
        "id": f"oecd:{country}:{recall['id']}",
        "authority": AUTHORITIES.get(country, country),
        "notice_date": recall.get("date") or None,
        "title": recall.get("product.name"),
        "hazard": recall.get("hazard") or "",
        "scope_json": {
            "Products": [{"Name": recall.get("product.name"), "Description": description, "Model": "",
                          "Type": recall.get("product.type") or ""}],
            "Images": [{"URL": i.get("imageUri"), "Caption": ""} for i in recall.get("images") or []],
            "Manufacturers": [{"Name": recall["manufacturer.name"]}] if recall.get("manufacturer.name") else [],
            "Distributors": [{"Name": recall["distributor.name"]}] if recall.get("distributor.name") else [],
            "Injuries": recall.get("injuries"), "Action": recall.get("action"), "Country": recall.get("countryName"),
            "Source": "OECD GlobalRecalls",
        },
        "url": recall.get("extUrl") or recall.get("uri"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="start", type=int, default=2019)
    parser.add_argument("--to", dest="end", type=int, default=2026)
    parser.add_argument("--countries", default=",".join(AUTHORITIES), help="comma-separated ISO codes")
    parser.add_argument("--db", default=os.environ.get("DATABASE_URL"), help="Postgres URL; omit to write files only")
    parser.add_argument("--summary", action="store_true", help="print counts")
    parser.add_argument("--offline", action="store_true", help="reuse raw/globalrecalls.jsonl instead of the API")
    args = parser.parse_args()

    RAW.mkdir(exist_ok=True)
    cached = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            recall = json.loads(line)
            cached[recall["uri"]] = recall
    if not args.offline:
        uris = []
        for country in args.countries.split(","):
            found = search(country, f"{args.start}-01-01", f"{args.end}-12-31")
            print(f"{country}: {len(found)} notices")
            uris += [r["uri"] for r in found]
        todo = list(dict.fromkeys(u for u in uris if u not in cached))
        print(f"{len(todo)} new notices to fetch ({len(cached)} cached)")
        with CACHE.open("a") as f, ThreadPoolExecutor(8) as pool:
            for n, recall in enumerate(pool.map(detail, todo), 1):
                f.write(json.dumps(recall, ensure_ascii=False) + "\n")
                cached[recall["uri"]] = recall
                if n % 250 == 0:
                    print(f"  fetched {n}/{len(todo)}", flush=True)

    rows = list({row["id"]: row for row in map(to_row, cached.values())}.values())
    if args.summary:
        by_authority: dict[str, int] = {}
        for row in rows:
            by_authority[row["authority"]] = by_authority.get(row["authority"], 0) + 1
        print(f"total {len(rows)} · " + " · ".join(f"{k} {v}" for k, v in sorted(by_authority.items())))
        for row in sorted(rows, key=lambda r: r["notice_date"] or "", reverse=True)[:10]:
            print(f"  {row['notice_date']}  {row['id']:<24} {(row['title'] or '')[:80]}")

    if args.db:
        from load_cpsc import save_to_db

        save_to_db(rows, args.db)
        print(f"saved {len(rows)} recalls to the database")
    else:
        print(f"{len(rows)} recalls in raw/globalrecalls.jsonl; no database given (--db or DATABASE_URL), nothing saved")


if __name__ == "__main__":
    main()
