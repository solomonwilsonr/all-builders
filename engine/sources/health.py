"""Source health for GET /v1/sources/health: for each source, whether it may run here, its last outcome and latency,
and its circuit-breaker state. Public and redacted: no keys, tokens or internal addresses.
"""
import threading
import time

from engine.sources import policy, registry
from engine.sources.base import SourceResult

_last: dict[str, dict] = {}
_lock = threading.Lock()


def record(result: SourceResult) -> None:
    with _lock:
        prev = _last.get(result.source, {"successes": 0, "failures": 0})
        entry = {**prev, "last_status": result.status, "last_at": result.retrieved_at.isoformat(),
                 "last_latency_ms": result.latency_ms, "last_detail": result.detail[:160]}
        entry["successes" if result.ok else "failures"] = prev.get("successes" if result.ok else "failures", 0) + 1
        if result.ok:
            entry["last_ok_at"] = result.retrieved_at.isoformat()
        _last[result.source] = entry


def report() -> dict:
    out = []
    for entry in registry.all_sources():
        may_run, why = registry.runnable(entry)
        with _lock:
            seen = dict(_last.get(entry["id"], {}))
        out.append({
            "source": entry["id"], "name": entry["name"], "authority": entry["authority"],
            "jurisdiction": entry["jurisdiction"], "markets": entry.get("markets", []),
            "access_method": entry["access_method"], "access_status": entry["access_status"],
            "access_checked_at": str(entry.get("checked_at") or ""), "enabled": may_run,
            "why_not": why or None, "circuit": policy.breaker.state(entry["id"]),
            "last_status": seen.get("last_status"), "last_at": seen.get("last_at"),
            "last_ok_at": seen.get("last_ok_at"), "last_latency_ms": seen.get("last_latency_ms"),
            "successes": seen.get("successes", 0), "failures": seen.get("failures", 0),
            "terms": entry.get("terms"), "official_url": entry.get("official_url") or None,
        })
    return {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sources": out,
            "note": "Health since this server started. A source that is not enabled is reported in every answer as "
                    "'not supported' or 'source unavailable', never as 'no recall'."}
