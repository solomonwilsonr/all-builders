"""MCP endpoint (/mcp) so other AI agents can use SafeShelf as tools.

Each tool calls the REST API in-process, so agents get exactly what the screens get: the same real-or-mock answer,
the same API key check and, with investigation_id, the same Lab trace. Streamable HTTP, stateless and JSON
responses, so any Cloud Run instance can answer any request.
"""
import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
INSTRUCTIONS = """SafeShelf checks consumer products. Typical order: identify_product (from a listing) -> product_safety,
check_listing (is the shop real?), safety_marks, safer_alternatives. Verdict colours are set by code: red = official
recall, amber = AI findings under human review, green = checked and nothing found, not_enough_evidence. AI findings
are evidence for people, not regulatory determinations; say so when you pass them on. Never call a seller a scam."""

mcp = MCPServer("SafeShelf", instructions=INSTRUCTIONS, version="0.1.0")
_app = None  # the FastAPI app, set by attach()


async def _call(method: str, path: str, investigation_id: str | None = None, json: dict | None = None) -> Any:
    headers = {}
    if os.environ.get("API_KEY"):
        headers["x-api-key"] = os.environ["API_KEY"]
    if investigation_id:
        headers["x-investigation-id"] = investigation_id
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app), base_url="http://safeshelf",
                                 timeout=300) as client:
        response = await client.request(method, path, json=json, headers=headers)
    if response.status_code >= 400:
        raise ToolError(f"SafeShelf API {response.status_code}: {response.json().get('detail', response.text)}")
    return response.json()


def _listing(url, title, price, currency, seller, page_text, image_urls) -> dict:
    listing = {"url": url, "title": title, "price": price, "currency": currency, "seller": seller,
               "page_text": page_text, "image_urls": image_urls}
    return {k: v for k, v in listing.items() if v not in (None, "", [])}


@mcp.tool(annotations=READ_ONLY)
async def identify_product(url: str | None = None, title: str | None = None, price: float | None = None,
                           currency: str | None = None, seller: str | None = None, page_text: str | None = None,
                           image_urls: list[str] | None = None, investigation_id: str | None = None) -> dict:
    """Which product is this listing? Returns a SafeShelf product_id for the other tools. Give at least a url or title."""
    return await _call("POST", "/v1/products/identify", investigation_id,
                       _listing(url, title, price, currency, seller, page_text, image_urls))


@mcp.tool(annotations=READ_ONLY)
async def product_safety(product_id: str, investigation_id: str | None = None) -> dict:
    """Safety verdict: official recall status, hazard reports found in reviews and photos, safety-mark checks."""
    return await _call("GET", f"/v1/products/{product_id}/safety", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def check_listing(url: str | None = None, title: str | None = None, price: float | None = None,
                        currency: str | None = None, seller: str | None = None, page_text: str | None = None,
                        image_urls: list[str] | None = None, investigation_id: str | None = None) -> dict:
    """"Is it real?": copied photos, impossible price, brand-new website, conflicting specs, hidden AI instructions."""
    return await _call("POST", "/v1/listings/trust-check", investigation_id,
                       _listing(url, title, price, currency, seller, page_text, image_urls))


@mcp.tool(annotations=READ_ONLY)
async def find_copies(product_id: str, investigation_id: str | None = None) -> dict:
    """Same product under other listings or brands: exact model, possible rebrand, variant, look-alike, with reasons."""
    return await _call("POST", "/v1/products/duplicates", investigation_id, {"product_id": product_id})


@mcp.tool(annotations=READ_ONLY)
async def safety_marks(product_id: str, investigation_id: str | None = None) -> dict:
    """Safety and energy marks the listing claims, checked against official registries."""
    return await _call("GET", f"/v1/products/{product_id}/certifications", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def safer_alternatives(product_id: str, investigation_id: str | None = None) -> dict:
    """Similar products with no recall and no hazard reports in enough reviews read, with the reason for each."""
    return await _call("GET", f"/v1/products/{product_id}/alternatives", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def owner_guidance(product_id: str, investigation_id: str | None = None) -> dict:
    """For someone who already owns the product: what to do now (stop or take care, recall remedy, return, report)."""
    return await _call("GET", f"/v1/products/{product_id}/owner-guidance", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def case_file(product_id: str, investigation_id: str | None = None) -> dict:
    """Exportable case file: findings with evidence IDs and quotes, the code rule behind the verdict. Never sent."""
    return await _call("GET", f"/v1/products/{product_id}/case-file", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def product_history(product_id: str, investigation_id: str | None = None) -> dict:
    """Everything that ever changed about this product (identity, links, hazard findings, reports) and its recalls."""
    return await _call("GET", f"/v1/products/{product_id}/history", investigation_id)


@mcp.tool(annotations=READ_ONLY)
async def investigation_trace(investigation_id: str) -> dict:
    """Every step of an investigation: tool, model, time, tokens, estimated cost."""
    return await _call("GET", f"/v1/investigations/{investigation_id}/trace")


def attach(app) -> None:
    """Serve MCP at /mcp on the FastAPI app and run its session manager with the app."""
    global _app
    _app = app
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp", stateless_http=True, json_response=True,
        # Cloud Run gives a public HTTPS host; the DNS-rebinding guard is for servers on localhost.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    app.mount("/", mcp_app)  # after every API route, so only /mcp reaches it
    app.router.lifespan_context = mcp_app.router.lifespan_context
