"""Tools the agents may call: thin wrappers over the engine, so an agent knows nothing the API doesn't.

Each call runs in a worker thread (the engine is synchronous), becomes one step of the run, and adds the evidence
IDs it returned to what the answer may cite. An unknown product is an answer ({"error": ...}), not a crash.
"""
import asyncio
import logging
import time

from google.adk.tools import ToolContext

from engine import evidence, gemini, identity, marks, passport, safety, trace
from engine.agents import runtime

log = logging.getLogger(__name__)


async def call(agent: str, operation_id: str, fn, *args) -> dict:
    def work():
        calls = gemini.track()
        try:
            return fn(*args), calls
        except KeyError as missing:
            return {"error": f"SafeShelf has no product {missing}"}, calls
        except Exception as error:  # noqa: BLE001  one tool failing must not end the conversation
            log.warning("tool %s failed: %s", operation_id, type(error).__name__)
            return {"error": f"this check could not run ({type(error).__name__})"}, calls

    started = time.monotonic()
    body, calls = await asyncio.to_thread(work)
    runtime.saw(body)
    runtime.current().results[operation_id] = body
    summary = body["error"] if isinstance(body, dict) and "error" in body else trace.summarize(
        operation_id, body if isinstance(body, dict) else {"items": body})
    runtime.step(agent, trace.TOOLS.get(operation_id, operation_id), summary, time.monotonic() - started, calls,
                 body if isinstance(body, dict) else {"items": body})
    return body


async def get_product(product_id: str, tool_context: ToolContext) -> dict:
    """The product's identity: brand, model, category, key attributes and its listings."""
    return await call(tool_context.agent_name, "getProduct", passport.product, product_id)


async def get_safety(product_id: str, tool_context: ToolContext) -> dict:
    """Safety status: official recall status, AI hazard findings from reviews (with evidence IDs), safety-mark checks."""
    return await call(tool_context.agent_name, "getSafety", safety.safety, product_id)


async def get_relationships(product_id: str, tool_context: ToolContext) -> dict:
    """Products that are the same hardware or a copy: exact model, possible rebrand, variant, look-alike."""
    return await call(tool_context.agent_name, "getRelationships", identity.relationships, product_id)


async def get_history(product_id: str, tool_context: ToolContext) -> dict:
    """Everything that changed about the product over time, and the recall notices linked to it."""
    return await call(tool_context.agent_name, "getHistory", passport.history, product_id)


async def get_certifications(product_id: str, tool_context: ToolContext) -> dict:
    """Safety and energy marks the listing claims, checked against official registries."""
    return await call(tool_context.agent_name, "getCertifications", marks.certifications, product_id)


async def get_alternatives(product_id: str, tool_context: ToolContext) -> dict:
    """Similar products with no recall and no hazard reports in enough reviews read, from authorised sellers."""
    return await call(tool_context.agent_name, "getAlternatives", passport.alternatives, product_id)


async def get_evidence(evidence_ids: list[str], tool_context: ToolContext) -> dict:
    """The source, date and exact quote behind evidence IDs (for example EV-1F3B0227)."""
    items = await call(tool_context.agent_name, "getEvidence", evidence.lookup, ",".join(evidence_ids[:20]))
    return {"items": items} if isinstance(items, list) else items


EVIDENCE_TOOLS = [get_product, get_safety, get_relationships, get_history, get_certifications, get_evidence]
