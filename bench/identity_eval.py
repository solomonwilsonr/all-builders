"""Product-identity benchmark (plan v2.2 workstream C/H track 1): the engine's pair decisions against people's labels.

    cd engine && PYTHONPATH=.. uv run python ../bench/identity_eval.py            (make bench-identity)
    cd engine && PYTHONPATH=.. uv run python ../bench/identity_eval.py --sample 400   write pairs for people to label

Labels come only from people (identity_pairs, written by POST /v1/identity/feedback or bench/label_pairs.py). With no
labels the report says so; it never invents them. Reports precision, recall and false merges of "same product"
decisions, annotator agreement, and the numbers per market. --sample writes a stratified candidate set (exact,
rebrand, variant, look-alike, unresolved) to bench/fixtures/identity_candidates.jsonl.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from bench import runlog
from engine import safety, store

HERE = Path(__file__).parent
SAME = {"exact_model"}               # what the engine calls the same product (recall can pass)
SAME_LABELS = {"exact"}


def engine_decisions() -> dict[str, str]:
    """pair id -> the engine's own relationship decision (from pair_compare evidence, never a reviewer's edit)."""
    rows = store.conn().execute(
        "SELECT source_ref, content FROM evidence WHERE source_type = 'pair_compare'").fetchall()
    out = {}
    for r in rows:
        a, b = r["source_ref"].split(":", 1)
        decision = (json.loads(r["content"]).get("decision") or {})
        out["|".join(sorted([a, b]))] = decision.get("relationship") or "none"
    return out


def evaluate() -> dict:
    labels = store.conn().execute("SELECT pair_id, label, annotator, market FROM identity_pairs").fetchall()
    if not labels:
        return {"labelled_pairs": 0, "status": "no human labels yet",
                "next_step": "label pairs with bench/label_pairs.py or POST /v1/identity/feedback; two annotators "
                             "for high-impact pairs"}
    by_pair: dict[str, list[dict]] = defaultdict(list)
    for row in labels:
        by_pair[row["pair_id"]].append(row)
    decisions = engine_decisions()
    agree = sum(len({r["label"] for r in rows}) == 1 for rows in by_pair.values() if len(rows) > 1)
    multi = sum(len(rows) > 1 for rows in by_pair.values())
    per_market: dict[str, Counter] = defaultdict(Counter)
    for pair, rows in by_pair.items():
        if len({r["label"] for r in rows}) > 1 or pair not in decisions:
            continue  # disagreements wait for adjudication; pairs the engine never compared are not scored
        truth = rows[0]["label"] in SAME_LABELS
        said = decisions[pair] in SAME
        market = rows[0]["market"] or "unknown"
        for key in (market, "all"):
            per_market[key]["tp" if truth and said else "fp" if said else "fn" if truth else "tn"] += 1
    report = {}
    for market, c in per_market.items():
        n = sum(c.values())
        report[market] = {"pairs": n, **c,
                          "precision": round(c["tp"] / (c["tp"] + c["fp"]), 3) if c["tp"] + c["fp"] else None,
                          "recall": round(c["tp"] / (c["tp"] + c["fn"]), 3) if c["tp"] + c["fn"] else None,
                          "false_merges": c["fp"], "small_sample": n < 30}
    return {"labelled_pairs": len(by_pair), "annotators": len({r["annotator"] for r in labels}),
            "double_annotated": multi, "agreement": round(agree / multi, 3) if multi else None,
            "by_market": report, "label_mix": dict(Counter(r["label"] for r in labels))}


def sample(n: int) -> int:
    """Candidate pairs for labelling, stratified by the engine's relationship class and the products' markets."""
    rows = store.conn().execute(
        """SELECT DISTINCT ON (source_id, target_id) source_id, target_id, relationship_type, status
           FROM product_relationships ORDER BY source_id, target_id, version DESC""").fetchall()
    by_class: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["source_id"] < r["target_id"]:
            by_class[r["relationship_type"]].append(r)
    per = max(1, n // max(len(by_class), 1))
    out = HERE / "fixtures" / "identity_candidates.jsonl"
    written = 0
    with out.open("w") as f:
        for cls, items in by_class.items():
            for r in items[:per]:
                market = safety.market_of_product(r["source_id"])
                f.write(json.dumps({"source_id": r["source_id"], "target_id": r["target_id"], "engine": cls,
                                    "engine_status": r["status"], "market": market}) + "\n")
                written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", type=int, default=0)
    args = parser.parse_args()
    if args.sample:
        print(f"wrote {sample(args.sample)} candidate pairs to bench/fixtures/identity_candidates.jsonl")
        return
    results = evaluate()
    by_market = results.get("by_market", {})
    (HERE / "identity_by_country.json").write_text(json.dumps(by_market, indent=1) + "\n")
    summary = (f"{results['labelled_pairs']} labelled pairs" + (
        f"; precision {by_market.get('all', {}).get('precision')}, false merges "
        f"{by_market.get('all', {}).get('false_merges')}" if by_market else f" ({results.get('status')})"))
    path = runlog.save("identity", summary, results)
    print(summary, "->", path.name)


if __name__ == "__main__":
    main()
