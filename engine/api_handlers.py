"""Real handlers the API registers (api/app/main.py REAL_HANDLERS) when MOCK=0 and DATABASE_URL is set."""
from typing import Any

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from engine import identity, marks, safety


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


HANDLERS = {
    "identifyProduct": identify_product,
    "findDuplicates": find_duplicates,
    "getRelationships": get_relationships,
    "getSafety": get_safety,
    "getCertifications": get_certifications,
}
