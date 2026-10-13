# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32"]
# ///
"""M1: stream Amazon Reviews 2023 from Hugging Face and keep only what we need.

The files are 4-31 GB each, so run this on Colab or a cloud VM, not a laptop. Nothing is stored
except the matching lines.

    # 1. find listings whose metadata matches brands/models (regex), per category
    uv run data/stream_reviews.py meta  --category Cell_Phones_and_Accessories --match "vrurc|mycharge"
    # 2. keep the reviews of chosen listings (parent_asin list, one per line or JSON targets file)
    uv run data/stream_reviews.py reviews --category Cell_Phones_and_Accessories --asins data/raw/asins.txt

In Colab: `!pip install requests` then `!python stream_reviews.py ...`.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

HF = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw"
RAW = Path(__file__).parent / "raw"


def stream_lines(url: str):
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        yield from response.iter_lines(chunk_size=1 << 20)


def read_asins(path: str) -> set[str]:
    text = Path(path).read_text()
    if path.endswith(".json"):  # feasibility/targets.json format
        return {a for target in json.loads(text).values() for a in target["asins"]}
    return {line.strip() for line in text.splitlines() if line.strip()}


def run(url: str, out: Path, keep) -> None:
    seen = kept = 0
    start = time.time()
    with open(out, "w") as f:
        for line in stream_lines(url):
            seen += 1
            if keep(line):
                f.write(line.decode() + "\n")
                kept += 1
            if seen % 1_000_000 == 0:
                print(f"  {seen:,} lines, {kept:,} kept, {time.time() - start:.0f}s", file=sys.stderr)
    print(f"done: {seen:,} lines read, {kept:,} kept -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["meta", "reviews"])
    parser.add_argument("--category", required=True, help="e.g. Cell_Phones_and_Accessories, Electronics")
    parser.add_argument("--match", help="meta mode: regex over the raw metadata line (case-insensitive)")
    parser.add_argument("--title-match", help="meta mode: regex over the title only (case-insensitive)")
    parser.add_argument("--min-ratings", type=int, default=0, help="meta mode: keep listings with this many ratings")
    parser.add_argument("--asins", help="reviews mode: file of parent_asin values (.txt) or targets .json")
    parser.add_argument("--out", help="output file (default data/raw/<mode>_<category>.jsonl)")
    args = parser.parse_args()

    RAW.mkdir(exist_ok=True)
    out = Path(args.out or RAW / f"{args.mode}_{args.category}.jsonl")
    if args.mode == "meta":
        if not (args.match or args.title_match):
            parser.error("meta mode needs --match or --title-match")
        pattern = re.compile((args.match or args.title_match).encode(), re.IGNORECASE)
        title = re.compile(args.title_match, re.IGNORECASE) if args.title_match else None

        def keep(line: bytes) -> bool:
            if not pattern.search(line):  # cheap test on the raw bytes first
                return False
            if not (title or args.min_ratings):
                return True
            row = json.loads(line)
            return (not title or bool(title.search(row.get("title") or ""))) and \
                int(row.get("rating_number") or 0) >= args.min_ratings

        run(f"{HF}/meta_categories/meta_{args.category}.jsonl", out, keep)
    else:
        if not args.asins:
            parser.error("reviews mode needs --asins")
        # Cheap substring test on the raw bytes before any JSON parsing.
        wanted = {f'"parent_asin": "{a}"'.encode() for a in read_asins(args.asins)}
        run(f"{HF}/review_categories/{args.category}.jsonl", out, lambda line: any(w in line for w in wanted))


if __name__ == "__main__":
    main()
