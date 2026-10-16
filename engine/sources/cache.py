"""Source answers kept for each source's TTL, so a repeat check doesn't hit the regulator again. In memory always;
in Postgres (source_fetches) too when the database is there, so all API instances share it.

A cached answer is reported as checked_cache with its original retrieval time, never as a fresh live check.
"""
import json
import logging
import threading
import time

from engine.sources.base import SourceResult

log = logging.getLogger(__name__)
_memory: dict[str, tuple[float, SourceResult]] = {}
_lock = threading.Lock()


def key(source_id: str, query_key: str) -> str:
    return f"{source_id}:{query_key}"


def get(source_id: str, query_key: str, ttl_s: int) -> SourceResult | None:
    if ttl_s <= 0:
        return None
    with _lock:
        hit = _memory.get(key(source_id, query_key))
    if hit and time.time() - hit[0] < ttl_s:
        return hit[1]
    return None


def put(result: SourceResult) -> None:
    if result.ok:  # failures are never cached as answers; the circuit breaker handles repeats
        with _lock:
            _memory[key(result.source, result.query_key)] = (time.time(), result)


def as_cached(result: SourceResult) -> SourceResult:
    """The same records, marked as coming from the cache (retrieval time unchanged)."""
    records = []
    for r in result.records:
        r2 = type(r)(**{**r.__dict__, "mode": "cache"})
        records.append(r2)
    return SourceResult(source=result.source, status=result.status, records=records, mode="cache",
                        retrieved_at=result.retrieved_at, latency_ms=0, detail=result.detail,
                        query_key=result.query_key, raw_hash=result.raw_hash, freshness=result.freshness)


def log_fetch(result: SourceResult, adapter_id: str) -> None:
    """One row per real fetch in source_fetches (status, latency, raw hash), when the database is reachable."""
    try:
        from engine import store
        store.conn().execute(
            """INSERT INTO source_fetches (query_hash, adapter, fetched_at, status, latency_ms, raw_hash, record_ids,
                                           mode, detail)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (result.query_key, adapter_id, result.retrieved_at, result.status, result.latency_ms, result.raw_hash,
             json.dumps([r.record_id for r in result.records]), result.mode, result.detail[:300]))
    except Exception as error:  # noqa: BLE001  logging must never break an investigation
        log.debug("source fetch not logged: %s", type(error).__name__)


def clear() -> None:
    with _lock:
        _memory.clear()
