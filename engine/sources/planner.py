"""Source planner and retrieval: which sources to ask for this product and market, then ask them in parallel with
per-source timeouts, rate limits, circuit breakers and caching. One source failing never stops the others, and never
turns into "no recall": its coverage state says it could not be checked.

    plan(query, depth)          -> [{source, role, runnable, why}]
    retrieve(query, depth)      -> {"plan": [...], "results": [SourceResult...]}   (async)
    investigate(query, depth)   -> the same, from synchronous code
"""
import asyncio
import logging
import time

from engine.sources import cache, health, policy, registry
from engine.sources.base import (
    CIRCUIT_OPEN,
    ERROR,
    OK,
    RATE_LIMITED,
    TIMEOUT,
    SourceFailure,
    SourceQuery,
    SourceResult,
    now,
    payload_hash,
)

log = logging.getLogger(__name__)
MAX_PARALLEL = 6
BROWSER = {"browser_only"}  # slow sources: only on a deep investigation


def plan(query: SourceQuery, depth: str = "quick") -> list[dict]:
    """The market's own sources first, then global upstream signals; each with whether it may run and why not."""
    wanted: list[tuple[str, str]] = [(s, "local") for s in registry.local_sources(query.market_country)]
    wanted += [(s, "global") for s in registry.global_sources()]
    if query.source_country:
        wanted = [(s, r) for s, r in wanted
                  if registry.source(s)["jurisdiction"] in (query.source_country, "MULTI")]
    out, seen = [], set()
    for source_id, role in wanted:
        if source_id in seen:
            continue
        seen.add(source_id)
        entry = registry.source(source_id)
        may_run, why = registry.runnable(entry)
        if may_run and entry["access_status"] in BROWSER and depth != "deep":
            may_run, why = False, "searched only on a deep check (it needs a browser, about 30 s a site)"
        out.append({"source": source_id, "role": role, "name": entry["name"], "authority": entry["authority"],
                    "jurisdiction": entry["jurisdiction"], "runnable": may_run, "why": why or None,
                    "access_status": entry["access_status"]})
    return out


async def run_one(source_id: str, query: SourceQuery) -> SourceResult:
    entry = registry.source(source_id)
    qkey = query.key()
    hit = cache.get(source_id, qkey, int(entry.get("ttl_s") or 0))
    if hit:
        return cache.as_cached(hit)
    if not policy.breaker.allow(source_id):
        return SourceResult(source=source_id, status=CIRCUIT_OPEN, query_key=qkey,
                            detail="resting after repeated failures; tried again in a few minutes")
    if not policy.limiter.allow(source_id, int(entry.get("rate_per_min") or 30)):
        return SourceResult(source=source_id, status=RATE_LIMITED, query_key=qkey,
                            detail="SafeShelf's own rate limit for this source was reached; try again shortly")
    adapter = registry.adapter(source_id)
    started = time.monotonic()
    timeout = float(entry.get("timeout_s") or 8) * 2.5  # the adapter's timeout is per request; a search makes a few
    try:
        records = await asyncio.wait_for(adapter.search(query), timeout=timeout)
        result = SourceResult(source=source_id, status=OK, records=records, query_key=qkey,
                              mode="cache" if entry["role"] == "cache" or source_id == "india_notices" else "live",
                              raw_hash=payload_hash([r.raw_payload_hash for r in records]))
        fresh = getattr(adapter, "freshness", None)
        dates = [r.source_published_at for r in records if r.source_published_at]
        result.freshness = (max(v for v in fresh.values() if v) if isinstance(fresh, dict) and any(fresh.values())
                            else max(dates).date().isoformat() if dates else None)
    except TimeoutError:
        result = SourceResult(source=source_id, status=TIMEOUT, query_key=qkey,
                              detail=f"no answer within {timeout:g} s")
    except SourceFailure as failure:
        result = SourceResult(source=source_id, status=failure.status, query_key=qkey, detail=failure.detail)
    except Exception as error:  # noqa: BLE001  an adapter bug is a failed source, not a failed investigation
        log.warning("source %s failed: %s", source_id, type(error).__name__)
        result = SourceResult(source=source_id, status=ERROR, query_key=qkey,
                              detail=f"the check could not run ({type(error).__name__})")
    result.latency_ms = round(1000 * (time.monotonic() - started))
    result.retrieved_at = now()
    for r in result.records:
        r.retrieved_at = result.retrieved_at
    if result.status not in ("disabled", "not_configured"):
        policy.breaker.record(source_id, result.ok)
    health.record(result)
    cache.put(result)
    cache.log_fetch(result, source_id)
    return result


async def retrieve(query: SourceQuery, depth: str = "quick", only: list[str] | None = None) -> dict:
    steps = plan(query, depth)
    if only:
        steps = [s for s in steps if s["source"] in only]
    gate = asyncio.Semaphore(MAX_PARALLEL)

    async def bounded(source_id: str) -> SourceResult:
        async with gate:
            return await run_one(source_id, query)

    runnable = [s["source"] for s in steps if s["runnable"]]
    results = list(await asyncio.gather(*(bounded(s) for s in runnable))) if runnable else []
    return {"plan": steps, "results": results, "query": query}


def investigate(query: SourceQuery, depth: str = "quick", only: list[str] | None = None) -> dict:
    """retrieve() from synchronous code (pipeline checks and API handlers run in worker threads)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(retrieve(query, depth, only))
    # Called inside a running loop's thread (rare): run in a fresh loop on another thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        return pool.submit(lambda: asyncio.run(retrieve(query, depth, only))).result()
