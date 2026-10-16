"""Prospective shadow evaluation (plan v2.2 workstream H track 4): every answer SafeShelf gives is logged before the
future is known (prediction_log, hash-chained), and resolved later against recalls published afterwards.

    cd engine && PYTHONPATH=.. uv run python ../bench/prospective.py       (make eval-prospective)

1. Verifies the hash chain (an edited or deleted row breaks it).
2. Resolves each open prediction: a recall published after the prediction that names the same brand and model.
3. Reports how earlier outcomes fared, including misses and false alarms. Nothing is ever edited above the
   resolution columns.
"""
import hashlib
import json

from bench import runlog
from engine import store


def verify_chain(rows: list[dict]) -> tuple[bool, int | None]:
    previous = ""
    for r in rows:
        stamp = r["predicted_at"].isoformat()
        expected = hashlib.sha256(f"{previous}|{r['snapshot_id']}|{r['product_key']}|{r['outcome']}|{stamp}".encode())
        if r["previous_hash"] != previous or r["entry_hash"] != expected.hexdigest():
            return False, r["id"]
        previous = r["entry_hash"]
    return True, None


def resolve(rows: list[dict]) -> int:
    resolved = 0
    for r in rows:
        if r["resolved_outcome"]:
            continue
        brand, model, _market = (r["product_key"].split("|") + ["", "", ""])[:3]
        if len(model) < 3:
            continue
        hit = store.conn().execute(
            """SELECT id, notice_date FROM recalls WHERE notice_date > %s::date
               AND regexp_replace(upper(title || ' ' || scope_json::text), '[^A-Z0-9]', '', 'g') LIKE %s
               AND lower(title || scope_json::text) LIKE %s ORDER BY notice_date LIMIT 1""",
            (r["predicted_at"], f"%{model}%", f"%{brand[:6]}%")).fetchone()
        if hit:
            store.conn().execute("UPDATE prediction_log SET resolved_outcome = 'recalled_later', resolved_at = now(), "
                                 "resolution_ref = %s WHERE id = %s", (hit["id"], r["id"]))
            resolved += 1
    return resolved


def main() -> None:
    rows = store.conn().execute("SELECT * FROM prediction_log ORDER BY id").fetchall()
    intact, broken_at = verify_chain(rows)
    newly = resolve(rows)
    rows = store.conn().execute("SELECT outcome, resolved_outcome FROM prediction_log").fetchall()
    table: dict[str, dict] = {}
    for r in rows:
        cell = table.setdefault(r["outcome"], {"predictions": 0, "recalled_later": 0})
        cell["predictions"] += 1
        cell["recalled_later"] += r["resolved_outcome"] == "recalled_later"
    results = {"predictions": len(rows), "chain_intact": intact, "chain_broken_at": broken_at,
               "newly_resolved": newly, "by_outcome": table,
               "note": "Predictions are logged when made; outcomes are only added later. Too early to judge until "
                       "months of recalls have been published after the predictions."}
    path = runlog.save("prospective", f"{len(rows)} logged predictions, chain {'intact' if intact else 'BROKEN'}",
                       results)
    print(json.dumps(results, indent=1, default=str), "->", path.name)


if __name__ == "__main__":
    main()
