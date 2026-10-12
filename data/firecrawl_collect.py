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
import time
from pathlib import Path

import requests

RAW = Path(__file__).parent / "raw"
OUT = RAW / "firecrawl"
LEDGER = OUT / "ledger.jsonl"
BASE = os.environ.get("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v2")

# Rough credit cost per job, for the budget check before anything is sent.
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
    path = RAW / "firecrawl_jobs.jsonl"
    path.write_text("".join(json.dumps(j) + "\n" for j in jobs))
    print(f"wrote {len(jobs)} jobs -> {path} (estimated {sum(map(estimate, jobs))} credits)")


def run(jobs_path: str, max_credits: int, dry_run: bool) -> None:
    jobs = [json.loads(l) for l in Path(jobs_path).read_text().splitlines() if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
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
            result = call(job, api_key)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"job": job, "result": result, "fetched_at": time.time()}))
            used = result.get("creditsUsed", cost) if isinstance(result, dict) else cost
            with open(LEDGER, "a") as ledger:
                ledger.write(json.dumps({"key": job_key(job), "credits": used, "at": time.time()}) + "\n")
            print(f"{job['type']:<6} {used} credits  {label}  ok={result.get('success')}")
        budget_left -= cost
    print(f"credits used so far (all runs): {spent()}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    plan = sub.add_parser("plan-recall-twins")
    plan.add_argument("--limit", type=int, default=5, help="search results per recall")
    go = sub.add_parser("run")
    go.add_argument("--jobs", required=True)
    go.add_argument("--max-credits", type=int, required=True, help="hard cap for this run")
    go.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.cmd == "plan-recall-twins":
        plan_recall_twins(args.limit)
    else:
        run(args.jobs, args.max_credits, args.dry_run)


if __name__ == "__main__":
    main()
