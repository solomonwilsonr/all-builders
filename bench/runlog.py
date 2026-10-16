"""One versioned record per benchmark run in bench/runs/ (served by GET /v1/bench/runs): what ran, with which policy
and source versions, when, and a one-line summary. Plan v2.2 workstream H: every run keeps its versions."""
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

RUNS = Path(__file__).parent / "runs"


def commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], check=False, capture_output=True, text=True,
                              cwd=Path(__file__).parent, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def save(benchmark: str, summary: str, results: dict) -> Path:
    from engine.evidence_verification import POLICY_VERSION
    now = datetime.now(UTC)
    run = {"run_id": f"{benchmark}-{now.strftime('%Y-%m-%dT%H%M')}", "benchmark": benchmark,
           "created_at": now.isoformat(timespec="seconds"), "policy_version": POLICY_VERSION, "commit": commit(),
           "summary": summary, "results": results}
    RUNS.mkdir(exist_ok=True)
    path = RUNS / f"{run['run_id']}.json"
    path.write_text(json.dumps(run, indent=1, ensure_ascii=False, default=str) + "\n")
    return path
