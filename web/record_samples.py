"""Record the judges' page samples: runs each listing in samples/presets.json through the live API's Investigate
stream and saves every event with its time (samples/<id>.json). The page replays these at real speed.

    python3 web/record_samples.py              # every sample
    python3 web/record_samples.py mark fake    # only these

Standard library only. The API answers a listing it checked in the last 10 minutes from memory; a recording of
that would show no real work, so it is not saved (run it again later).
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API = os.environ.get("API_URL", "https://safeshelf-api-368488022657.asia-south1.run.app").rstrip("/")
HERE = Path(__file__).parent / "samples"


def record(request: dict) -> list[dict]:
    req = urllib.request.Request(API + "/v1/agent/sessions/stream", data=json.dumps(request).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    started, events, block = time.monotonic(), [], []
    with urllib.request.urlopen(req, timeout=200) as res:
        for raw in res:
            line = raw.decode().rstrip("\n")
            if line:
                block.append(line)
                continue
            data = "\n".join(x[5:] for x in block if x.startswith("data:"))
            block = []
            if data:
                event = json.loads(data)
                event["_ms"] = round(1000 * (time.monotonic() - started))
                events.append(event)
    return events


def main() -> None:
    presets = json.loads((HERE / "presets.json").read_text())["presets"]
    wanted = set(sys.argv[1:])
    for preset in presets:
        if wanted and preset["id"] not in wanted:
            continue
        events = record(preset["request"])
        done = next((e for e in events if e["type"] == "done"), None)
        if not done:
            print(f"{preset['id']}: no answer ({events[-1] if events else 'nothing'}), not saved")
            continue
        if any(e.get("tool") == "cache" for e in events):
            print(f"{preset['id']}: answered from the 10-minute memory, not saved; run it again later")
            continue
        overall = done["result"]["verdict"]["overall"]
        ok = overall in preset["expect"]["overall"]
        (HERE / f"{preset['id']}.json").write_text(json.dumps(
            {"recorded_at": time.strftime("%Y-%m-%d %H:%M %Z"), "api": API, "events": events},
            ensure_ascii=False, indent=1))
        print(f"{preset['id']}: {overall} in {events[-1]['_ms'] / 1000:.1f} s"
              f"{'' if ok else '   ✗ expected ' + '/'.join(preset['expect']['overall'])}")


if __name__ == "__main__":
    main()
