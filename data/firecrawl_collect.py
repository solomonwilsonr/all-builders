# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32"]
# ///
"""M1: collect data with Firecrawl, inside a hard credit budget. Data collection only, never live.

    uv run data/firecrawl_collect.py plan-recall-twins            # write jobs from the CPSC candidates
    uv run data/firecrawl_collect.py run --jobs data/raw/firecrawl_jobs.jsonl --max-credits 20 --dry-run
    FIRECRAWL_API_KEY=fc-... uv run data/firecrawl_collect.py run --jobs ... --max-credits 20

Rules (TOOLS.md): test on ~10 pages first; scrape once, save, then always work from the saved copy;
no bulk marketplace review scraping; no getting around captchas; commit only extracted fields.
Every result is saved under data/raw/firecrawl/ and every credit spent goes into ledger.jsonl.
"""
import argparse
import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests

RAW = Path(__file__).parent / "raw"
OUT = RAW / "firecrawl"
LEDGER = OUT / "ledger.jsonl"
BASE = os.environ.get("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v2")

# Rough credit cost per job, for the budget check before anything is sent.
PACE_SECONDS = 6.5
COST = {"scrape": 1, "search": 1}  # search: per result returned (limit), scrape: per page


def estimate(job: dict) -> int:
    return COST[job["type"]] * (job.get("limit", 1) if job["type"] == "search" else 1)


def spent() -> int:
    if not LEDGER.exists():
        return 0
    return sum(json.loads(line)["credits"] for line in LEDGER.read_text().splitlines() if line)


def job_key(job: dict) -> str:
    return hashlib.sha1(json.dumps(job, sort_keys=True).encode()).hexdigest()[:12]


def call(job: dict, api_key: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    if job["type"] == "scrape":
        body = {"url": job["url"], "formats": job.get("formats", ["markdown"])}
        return requests.post(f"{BASE}/scrape", json=body, headers=headers, timeout=120).json()
    body = {"query": job["query"], "limit": job.get("limit", 5)}
    return requests.post(f"{BASE}/search", json=body, headers=headers, timeout=120).json()


PRIORITY = [
    ("power bank", "powerbank", "charger", "adapter", "charging", "battery"),
    ("heater", "heated", "heating", "extension cord", "surge", "power cable"),
    ("hoverboard", "scooter", "e-bike", "energy storage"),
]


def priority(job: dict) -> int:
    query = job["query"].lower()
    return next((rank for rank, words in enumerate(PRIORITY) if any(w in query for w in words)), len(PRIORITY))


def plan_recall_twins(limit: int) -> None:
    """Search queries for current listings that may match recalled products (real-world finding, M16)."""
    candidates = [json.loads(l) for l in (RAW / "cpsc_backtest_candidates.jsonl").read_text().splitlines()]
    jobs = []
    for recall in candidates:
        for product in (recall["scope_json"].get("Products") or [])[:1]:
            name = product.get("Name") or recall["title"]
            model = product.get("Model") or ""
            jobs.append({
                "type": "search",
                "query": f"{name} {model}".strip() + " buy",
                "limit": limit,
                "tag": "recall_twins",
                "recall_id": recall["id"],
            })
    jobs.sort(key=priority)  # spend credits on the demo's product types first
    path = RAW / "firecrawl_jobs.jsonl"
    path.write_text("".join(json.dumps(j) + "\n" for j in jobs))
    print(f"wrote {len(jobs)} jobs -> {path} (estimated {sum(map(estimate, jobs))} credits)")


def load_dotenv() -> None:
    """Read KEY=VALUE lines from the repo's .env into os.environ (shell values win)."""
    env = Path(__file__).resolve().parents[1] / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and not key.startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def run(jobs_path: str, max_credits: int, dry_run: bool) -> None:
    jobs = [json.loads(l) for l in Path(jobs_path).read_text().splitlines() if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    load_dotenv()
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not dry_run and not api_key:
        raise SystemExit("Set FIRECRAWL_API_KEY (keep it in .env, never commit it)")

    budget_left = max_credits
    for job in jobs:
        out = OUT / job.get("tag", "misc") / f"{job_key(job)}.json"
        if out.exists():
            continue  # scrape once, then always use the saved copy
        cost = estimate(job)
        if cost > budget_left:
            print(f"budget reached ({max_credits} credits this run); stopping")
            break
        label = job.get("query") or job.get("url")
        if dry_run:
            print(f"[dry-run] {job['type']:<6} ~{cost} credits  {label}")
        else:
            time.sleep(PACE_SECONDS)  # our plan allows about 10 requests a minute
            result = call(job, api_key)
            for _ in range(3):
                if not (isinstance(result, dict) and "rate limit" in str(result.get("error", "")).lower()):
                    break
                print("rate limited; waiting 60 s")
                time.sleep(60)
                result = call(job, api_key)
            if not (isinstance(result, dict) and result.get("success")):
                # Not saved, so the job is retried next run; failed calls aren't billed.
                error = result.get("error") if isinstance(result, dict) else result
                raise SystemExit(f"{job['type']} failed: {error}  ({label})")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"job": job, "result": result, "fetched_at": time.time()}))
            used = result.get("creditsUsed", cost) if isinstance(result, dict) else cost
            with open(LEDGER, "a") as ledger:
                ledger.write(json.dumps({"key": job_key(job), "credits": used, "at": time.time()}) + "\n")
            print(f"{job['type']:<6} {used} credits  {label}  ok={result.get('success')}")
        budget_left -= cost
    print(f"credits used so far (all runs): {spent()}")


CATALOG_QUERIES = ["65W GaN charger", "20W USB C fast charger", "33W fast charger type c", "power bank 20000mAh",
                   "power bank 10000mAh fast charging", "room heater", "fan heater 2000W", "extension board surge protector",
                   "smart TV 43 inch", "smart TV 55 inch 4K"]
CATALOG_SITES = {"amazon.in": re.compile(r"amazon\.in/.*/?dp/[A-Z0-9]{10}"),
                 "flipkart.com": re.compile(r"flipkart\.com/.+/p/itm\w+")}


def plan_catalog(limit: int) -> None:
    """Indian marketplace searches for the hero categories (catalog for identify, price and photo checks)."""
    jobs = [{"type": "search", "query": f"site:{site} {query}", "limit": limit, "tag": "catalog_search"}
            for query in CATALOG_QUERIES for site in CATALOG_SITES]
    path = RAW / "firecrawl_catalog_search.jsonl"
    path.write_text("".join(json.dumps(j) + "\n" for j in jobs))
    print(f"wrote {len(jobs)} jobs -> {path} (estimated {sum(map(estimate, jobs))} credits)")


def plan_catalog_scrapes(max_pages: int) -> None:
    """Product pages found by the catalog searches, one scrape each (listing pages only, never reviews)."""
    urls: list[str] = []
    for saved in sorted((OUT / "catalog_search").glob("*.json")):
        result = json.loads(saved.read_text())["result"]
        data = result.get("data")
        for item in data.get("web", []) if isinstance(data, dict) else (data or []):
            url = (item.get("url") or "").split("?")[0].split("/ref=")[0]
            if any(p.search(url) for p in CATALOG_SITES.values()) and url not in urls:
                urls.append(url)
    jobs = [{"type": "scrape", "url": url, "tag": "catalog_pages"} for url in urls[:max_pages]]
    path = RAW / "firecrawl_catalog_pages.jsonl"
    path.write_text("".join(json.dumps(j) + "\n" for j in jobs))
    print(f"{len(urls)} product pages found; wrote {len(jobs)} scrape jobs -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    plan = sub.add_parser("plan-recall-twins")
    plan.add_argument("--limit", type=int, default=5, help="search results per recall")
    cat = sub.add_parser("plan-catalog")
    cat.add_argument("--limit", type=int, default=20, help="search results per query")
    pages = sub.add_parser("plan-catalog-scrapes")
    pages.add_argument("--max-pages", type=int, default=800)
    go = sub.add_parser("run")
    go.add_argument("--jobs", required=True)
    go.add_argument("--max-credits", type=int, required=True, help="hard cap for this run")
    go.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.cmd == "plan-recall-twins":
        plan_recall_twins(args.limit)
    elif args.cmd == "plan-catalog":
        plan_catalog(args.limit)
    elif args.cmd == "plan-catalog-scrapes":
        plan_catalog_scrapes(args.max_pages)
    else:
        run(args.jobs, args.max_credits, args.dry_run)


if __name__ == "__main__":
    main()
