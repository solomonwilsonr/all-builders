"""POST /v1/agent/sessions (operationId startAgentSession): one endpoint, one mode per agent.

    chat           Shelf Chat (Concierge, tools over stored evidence)
    investigate    the Investigate pipeline (page_reader -> parallel checks -> code verdict -> verdict_writer)
    alternatives   the Safer Alternative Finder
    report_draft   the regulator report copilot (never submits)
    shopper_step   the Shopper Agent's next step on the shopper's page
    research       the Research Agent on official recall sites (headless browser service)

Every step is returned in "steps" and written to the investigation trace under the session's investigation ID
(the X-Investigation-Id header, else a new SS-I- ID), so the Lab shows what each agent did, with time and cost.
"""
import asyncio

from fastapi import HTTPException, Request

from engine import passport, trace
from engine.agents import concierge, copilot, pipeline, research, runtime, shopper


async def research_session(body: dict) -> dict:
    pid = body.get("product_id")
    if pid and not (body.get("brand") or body.get("model")):  # a known product: its own brand and model number
        try:
            product = await asyncio.to_thread(passport.product, pid)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown product {pid}") from None
        body = {**body, "brand": product.get("brand"), "model": product.get("model"),
                "kind": body.get("kind") or product.get("category")}
    if not (body.get("brand") or body.get("model")):
        raise HTTPException(status_code=422, detail="Give a product_id, or a brand and a model number")
    mode = "computer_use" if body.get("computer_use") else "scripted"
    result = await asyncio.to_thread(research.check, body.get("brand") or "", body.get("model") or "",
                                     body.get("kind") or "", body.get("sources"), mode)
    if result.get("skipped"):
        raise HTTPException(status_code=503, detail="The Research Agent is not deployed on this server")
    runtime.saw(result)
    runtime.step("research_agent", "browser", research.summary(result), result.get("seconds") or 0)
    lines = research.reasons(result)
    return {"session_id": runtime.current().investigation_id, "mode": "research", "product_id": body.get("product_id"),
            "messages": [{"role": "assistant", "text": " ".join(f"{t}." for t, _ in lines) or research.summary(result),
                          "evidence_ids": [i for _, ids in lines for i in ids if i]}],
            "research": result, "steps": runtime.current().steps}


MODES = {"chat": concierge.chat_session, "investigate": pipeline.investigate,
         "alternatives": concierge.alternatives_session, "report_draft": copilot.draft,
         "shopper_step": lambda body: asyncio.to_thread(shopper.next_step, body), "research": research_session}


async def start_agent_session(request: Request, params: dict) -> dict:
    body = await request.json()
    mode = body.get("mode")
    if mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of: {', '.join(MODES)}")
    investigation_id = request.headers.get("x-investigation-id") or (
        body.get("session_id") if mode in ("investigate", "shopper_step") and body.get("session_id") else None
    ) or runtime.new_id()
    if not trace.VALID_ID.match(investigation_id):
        raise HTTPException(status_code=422, detail="session_id: letters, digits and ._:- only")
    runtime.start(investigation_id)
    result = await MODES[mode](body)
    result.setdefault("investigation_id", investigation_id)
    return result
