"""Real handlers the API registers (api/app/main.py REAL_HANDLERS) when MOCK=0 and DATABASE_URL is set."""
import time
from typing import Any

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from engine import (
    case_file,
    catalog,
    evidence,
    gemini,
    identity,
    marks,
    owner,
    page_safety,
    passport,
    recall_catalog,
    safety,
    trace,
    trust,
)
from engine.agents import handler as agent_handler


async def identify_product(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title", "page_text", "image_urls")):
        raise HTTPException(status_code=422, detail="Give at least a url, title, page_text or image_urls")
    return await run_in_threadpool(identity.identify, listing)


async def find_duplicates(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    try:
        return await run_in_threadpool(identity.duplicates, body["product_id"], bool(body.get("refresh")))
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def get_relationships(request: Request, params: dict[str, Any]) -> dict:
    return await run_in_threadpool(identity.relationships, params["product_id"])


async def get_safety(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(safety.safety, params["product_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def get_certifications(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(marks.certifications, params["product_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def trust_check(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title", "page_text", "image_urls")):
        raise HTTPException(status_code=422, detail="Give at least a url, title, page_text or image_urls")
    return await run_in_threadpool(trust.trust_check, listing)


async def listing_safety_check(request: Request, params: dict[str, Any]) -> dict:
    listing = await request.json()
    if not any(listing.get(k) for k in ("url", "title")):
        raise HTTPException(status_code=422, detail="Give at least a url or title")
    return await run_in_threadpool(page_safety.listing_safety, listing)


async def get_evidence(request: Request, params: dict[str, Any]) -> list[dict]:
    ids = request.query_params.get("ids") or ""
    if not ids.strip():
        raise HTTPException(status_code=422, detail="Give ids, e.g. ?ids=EV-1F3B0227,EV-08E9C38D")
    return await run_in_threadpool(evidence.lookup, ids)


def by_product(fn):
    """GET /v1/products/{product_id}/... handler: unknown product -> 404."""
    async def handler(request: Request, params: dict[str, Any]) -> dict:
        try:
            return await run_in_threadpool(fn, params["product_id"])
        except KeyError as missing:
            raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None
    return handler


async def create_report(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    if not body.get("product_id") or not body.get("description"):
        raise HTTPException(status_code=422, detail="Give a product_id and a description")
    try:
        # The reporter is stored only as a hash (Firebase uid or WhatsApp number from the calling screen or bot).
        return await run_in_threadpool(passport.create_report, body, request.headers.get("x-reporter-ref"))
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown product {missing}") from None


async def bench_results(request: Request, params: dict[str, Any]) -> dict:
    return passport.bench_results()


async def get_trace(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(trace.get_trace, params["investigation_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown investigation {missing}") from None


def traced(operation_id: str, handler):
    """With an X-Investigation-Id header, the answer is also recorded as a step of that investigation."""
    async def wrapper(request: Request, params: dict[str, Any]) -> dict:
        investigation_id = request.headers.get("x-investigation-id")
        if not investigation_id:
            return await handler(request, params)
        if not trace.VALID_ID.match(investigation_id):
            raise HTTPException(status_code=422, detail="X-Investigation-Id: letters, digits and ._:- only")
        calls = gemini.track()  # copied into the worker thread by run_in_threadpool
        started = time.monotonic()
        body = await handler(request, params)
        await run_in_threadpool(trace.record, investigation_id, operation_id, time.monotonic() - started, calls, body)
        return body
    return wrapper


async def list_recalls(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(recall_catalog.search, dict(request.query_params))
    except ValueError as problem:
        raise HTTPException(status_code=422, detail=str(problem)) from None


async def get_recall(request: Request, params: dict[str, Any]) -> dict:
    try:
        return await run_in_threadpool(recall_catalog.recall, params["recall_id"])
    except KeyError as missing:
        raise HTTPException(status_code=404, detail=f"Unknown recall {missing}") from None


async def catalog_scan(request: Request, params: dict[str, Any]) -> dict:
    body = await request.json()
    try:
        return await run_in_threadpool(catalog.scan, body)
    except ValueError as problem:  # missing or unreadable CSV, no title column
        raise HTTPException(status_code=422, detail=str(problem)) from None


HANDLERS = {
    "identifyProduct": identify_product,
    "findDuplicates": find_duplicates,
    "getRelationships": get_relationships,
    "getSafety": get_safety,
    "getCertifications": get_certifications,
    "trustCheck": trust_check,
    "listingSafetyCheck": listing_safety_check,
    "getProduct": by_product(passport.product),
    "getHistory": by_product(passport.history),
    "getAlternatives": by_product(passport.alternatives),
    "getCaseFile": by_product(case_file.case_file),
    "getOwnerGuidance": by_product(owner.owner_guidance),
    "createReport": create_report,
    "getBenchResults": bench_results,
    "startAgentSession": agent_handler.start_agent_session,
    "getEvidence": get_evidence,
    "catalogScan": catalog_scan,
    "listRecalls": list_recalls,
    "getRecall": get_recall,
}
HANDLERS = {op: traced(op, handler) for op, handler in HANDLERS.items()}
HANDLERS["getTrace"] = get_trace
