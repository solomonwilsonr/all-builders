"""Label product pairs for the identity gold set (plan v2.2 workstream C): shows both products side by side and
stores your label through engine.identity.feedback (one row per annotator; agreeing decisive labels write an edge).

    cd engine && PYTHONPATH=.. uv run python ../bench/label_pairs.py --annotator <your-initials> [--limit 20]

Reads bench/fixtures/identity_candidates.jsonl (make it with identity_eval.py --sample 400). Labels: e exact,
r rebrand, v regional variant, l look-alike, c counterfeit suspect, d distinct, u unresolvable, s skip, q quit.
"""
import argparse
import json
from pathlib import Path

from engine import identity, store, tenancy

KEYS = {"e": "exact", "r": "rebrand", "v": "regional_variant", "l": "lookalike", "c": "counterfeit_suspect",
        "d": "distinct", "u": "unresolvable"}
CANDIDATES = Path(__file__).parent / "fixtures" / "identity_candidates.jsonl"


def show(pid: str) -> str:
    fp = store.latest_fingerprint(pid) or {}
    view = fp.get("view") or {}
    listings = store.product_listings(pid)
    return (f"{pid}: {fp.get('brand')} {fp.get('model')} ({fp.get('category')})\n   {view.get('title', '')[:150]}\n"
            f"   {listings[0]['url'] if listings else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--annotator", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    who = tenancy.owner_hash(f"annotator:{args.annotator}")
    done = {r["pair_id"] for r in store.conn().execute("SELECT pair_id FROM identity_pairs WHERE annotator = %s",
                                                       (who,)).fetchall()}
    n = 0
    for line in CANDIDATES.read_text().splitlines():
        pair = json.loads(line)
        if "|".join(sorted([pair["source_id"], pair["target_id"]])) in done or n >= args.limit:
            continue
        print("\n" + show(pair["source_id"]) + "\n" + show(pair["target_id"]))
        print(f"   engine said: {pair['engine']} ({pair['engine_status']})  — your label? [e r v l c d u / s q]")
        key = input("> ").strip().lower()[:1]
        if key == "q":
            break
        if key not in KEYS:
            continue
        why = input("why (one sentence): ").strip() or "label set in the labelling tool"
        out = identity.feedback(pair["source_id"], pair["target_id"], KEYS[key], who, why.ljust(10, "."),
                                pair.get("market"))
        print("   stored;", "edge " + out["edge"]["relationship"] if out["edge"] else out.get("note") or "no edge")
        n += 1
    print(f"{n} pairs labelled")


if __name__ == "__main__":
    main()
