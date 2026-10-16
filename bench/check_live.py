"""After `make deploy-api`: is the deployed API giving plan v2.2 answers? Runs the JAPAC gate cases against API_URL
over HTTP and checks source health (Cloud Run's network may be treated differently from a laptop).

    API_URL=https://... python3 bench/check_live.py        (make check-live)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = os.environ.get("API_URL", "").rstrip("/")
GATE = Path(__file__).parent / "fixtures" / "japac" / "gate.json"
MUST_RUN = ("cpsc", "jp_caa", "oecd_globalrecalls", "india_notices", "stored_notices")


def call(path: str, body: dict | None = None) -> tuple[dict, str]:
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
                                 headers={"content-type": "application/json"}, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read()), res.headers.get("X-SafeShelf-Source") or "?"


def main() -> int:
    if not API:
        print("set API_URL")
        return 2
    failures = 0
    try:
        health, source = call("/v1/sources/health")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print("FAIL the deployed API is older than plan v2.2 (no /v1/sources/health): run make deploy-api")
            return 1
        raise
    enabled = {s["source"]: s for s in health.get("sources", [])}
    for sid in MUST_RUN:
        s = enabled.get(sid, {})
        ok = s.get("enabled")
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} source {sid:<20} enabled={s.get('enabled')} last={s.get('last_status')} "
              f"{s.get('why_not') or ''}")
    if source == "mock":
        print("FAIL the API answered with example data (MOCK=1?)")
        return 1
    for case in json.loads(GATE.read_text())["cases"]:
        started = time.monotonic()
        try:
            answer, src = call("/v1/investigations", case["request"])
        except Exception as error:  # noqa: BLE001
            print(f"FAIL {case['id']:<20} {error}")
            failures += 1
            continue
        ok = answer.get("outcome") == case["expected_outcome"] and \
            (not case.get("expected_basis") or answer.get("basis") == case["expected_basis"])
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {case['id']:<20} {answer.get('outcome')} / {answer.get('basis')} "
              f"({answer.get('source_mode')}, {time.monotonic() - started:.1f} s, {src})")
        if not ok:
            print(f"     expected {case['expected_outcome']}; coverage: {answer.get('coverage', {}).get('summary')}")
    print("all good" if not failures else f"{failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
