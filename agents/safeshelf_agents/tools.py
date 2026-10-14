"""Tools the agents may call. Every tool reads from the SafeShelf API, so the agent knows nothing the API doesn't."""
import os

import httpx

API_BASE = os.environ.get("SAFESHELF_API", "https://safeshelf-api-368488022657.asia-south1.run.app")
# The API answers some endpoints with made-up example data (x-safeshelf-source: mock). That must never reach the model.
ALLOW_MOCK = os.environ.get("SAFESHELF_ALLOW_MOCK") == "1"  # only the offline tests turn this on


def _get(path: str) -> dict:
    headers = {"X-API-Key": os.environ["API_KEY"]} if os.environ.get("API_KEY") else {}
    try:
        res = httpx.get(f"{API_BASE}{path}", headers=headers, timeout=15)
        res.raise_for_status()
        if res.headers.get("x-safeshelf-source") == "mock" and not ALLOW_MOCK:
            return {"unavailable": "no real data for this yet"}
        return res.json()
    except httpx.HTTPError as err:
        return {"error": f"SafeShelf API could not answer: {err}"}


def get_product(product_id: str) -> dict:
    """Get the identity of a product: brand, model, category and key attributes."""
    return _get(f"/v1/products/{product_id}")


def get_safety(product_id: str) -> dict:
    """Get the safety status of a product: official recalls checked, AI findings with evidence IDs, certification results."""
    return _get(f"/v1/products/{product_id}/safety")


def get_relationships(product_id: str) -> dict:
    """Get products that may be the same hardware or a copy of this one (exact model, rebrand, look-alike)."""
    return _get(f"/v1/products/{product_id}/relationships")


def get_history(product_id: str) -> dict:
    """Get how this product's safety picture changed over time."""
    return _get(f"/v1/products/{product_id}/history")


def get_certifications(product_id: str) -> dict:
    """Get certification and safety-mark checks (for example BIS or the Australian registry) for a product."""
    return _get(f"/v1/products/{product_id}/certifications")


def get_alternatives(product_id: str) -> dict:
    """Get safer genuine alternatives to this product from authorised sellers."""
    return _get(f"/v1/products/{product_id}/alternatives")


ALL_TOOLS = [get_product, get_safety, get_relationships, get_history, get_certifications, get_alternatives]
