"""Analytics copy in BigQuery (plan v2.2 section 2 and 12): Cloud SQL stays the operational store; assessments,
coverage, source fetches, the claim passport and the prediction log go to BigQuery for analysis and benchmarks.

    cd engine && PYTHONPATH=.. uv run python ../data/export_bigquery.py                 # NDJSON in data/raw/bq/
    cd engine && PYTHONPATH=.. uv run python ../data/export_bigquery.py --load safeshelf_analytics
                                                                                       # also `bq load` each table

No personal data is in these tables (owners are hashed and watchlists are not exported). Loading replaces the table.
"""
import argparse
import json
import subprocess
from datetime import date, datetime
from pathlib import Path

from engine import store

OUT = Path(__file__).parent / "raw" / "bq"
TABLES = {
    "assessment_snapshots": "SELECT id, investigation_id, product_id, market, policy_version, source_cutoff, outcome, "
                            "source_mode, created_at, output->'coverage'->'summary' AS coverage_summary, "
                            "output->>'basis' AS basis, output->>'evidence_strength' AS evidence_strength, "
                            "output->>'identity_confidence' AS identity_confidence FROM assessment_snapshots",
    "coverage_checks": "SELECT investigation_id, source_id, country, state, mode, checked_at, freshness FROM "
                       "coverage_checks",
    "source_fetches": "SELECT adapter, fetched_at, status, latency_ms, mode FROM source_fetches",
    "evidence_claims": "SELECT claim_id, claim_type, jurisdiction, source_registry_id, source_record_id, "
                       "source_published_at, retrieved_at, verification_state, investigation_id FROM evidence_claims "
                       "WHERE source_record_id IS NOT NULL",
    "prediction_log": "SELECT snapshot_id, product_key, outcome, predicted_at, resolved_outcome, resolved_at FROM "
                      "prediction_log",
}


def plain(value):
    return value.isoformat() if isinstance(value, (datetime, date)) else value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--load", metavar="DATASET", help="BigQuery dataset to load into with the bq CLI")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for table, sql in TABLES.items():
        rows = store.conn().execute(sql).fetchall()
        path = OUT / f"{table}.ndjson"
        with path.open("w") as f:
            for row in rows:
                f.write(json.dumps({k: plain(v) for k, v in row.items()}, ensure_ascii=False, default=str) + "\n")
        print(f"{table}: {len(rows)} rows -> {path}")
        if args.load and rows:
            subprocess.run(["bq", "load", "--replace", "--autodetect", "--source_format=NEWLINE_DELIMITED_JSON",
                            f"{args.load}.{table}", str(path)], check=True)


if __name__ == "__main__":
    main()
