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
import json
import logging
import threading

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse

from engine import passport, region, trace
from engine.agents import concierge, copilot, pipeline, research, runtime, shopper

log = logging.getLogger(__name__)


async def research_session(body: dict) -> dict:
    pid = body.get("product_id")
    if pid and not (body.get("brand") or body.get("model")):  # a known product: its own brand and model number
        try:
            product = await asyncio.to_thread(passport.product, pid)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown product {pid}") from None
        where = next((m for m in (region.of(row.get("url")) for row in product.get("listings", [])) if m), None)
        body = {**body, "brand": product.get("brand"), "model": product.get("model"),
                "kind": body.get("kind") or product.get("category"),
                "sources": body.get("sources") or region.recall_sources(where)}
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


def _prepare(body: dict, headers) -> tuple[str, str]:
    """(mode, investigation_id), or 422."""
    mode = body.get("mode")
    if mode not in MODES:
        raise HTTPException(status_code=422, detail=f"mode must be one of: {', '.join(MODES)}")
    investigation_id = headers.get("x-investigation-id") or (
        body.get("session_id") if mode in ("investigate", "shopper_step", "research") and body.get("session_id")
        else None) or runtime.new_id()
    if not trace.VALID_ID.match(investigation_id):
        raise HTTPException(status_code=422, detail="session_id: letters, digits and ._:- only")
    return mode, investigation_id


async def start_agent_session(request: Request, params: dict) -> dict:
    body = await request.json()
    mode, investigation_id = _prepare(body, request.headers)
    runtime.start(investigation_id)
    result = await MODES[mode](body)
    result.setdefault("investigation_id", investigation_id)
    return result


def _sse(event: dict) -> str:
    return f"event: {event.get('type', 'message')}\ndata: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"


async def stream_agent_session(request: Request) -> StreamingResponse:
    """POST /v1/agent/sessions/stream: the same agents, with each step sent as it happens (server-sent events).
    Events: open, start (a check began), step (one finished), verdict (the colours, before the explanation is
    written), done (the full answer, same JSON as POST /v1/agent/sessions), error. Comment lines keep it alive."""
    body = await request.json()
    mode, investigation_id = _prepare(body, request.headers)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    run = runtime.start(investigation_id)
    loop_thread = threading.get_ident()

    def listen(event: dict) -> None:
        # Straight into the queue from the event loop's own thread, so events keep their order (a cached answer
        # finishes without waiting); worker threads hand theirs to the loop.
        if threading.get_ident() == loop_thread:
            queue.put_nowait(event)
        else:
            loop.call_soon_threadsafe(queue.put_nowait, event)

    run.listener = listen

    async def work() -> None:
        try:
            result = await MODES[mode](body)
            result.setdefault("investigation_id", investigation_id)
            queue.put_nowait({"type": "done", "result": result})
        except HTTPException as problem:
            queue.put_nowait({"type": "error", "status": problem.status_code, "detail": problem.detail})
        except Exception as error:  # noqa: BLE001  the screen always gets an ending
            log.warning("agent stream failed: %s", type(error).__name__)
            queue.put_nowait({"type": "error", "status": 500, "detail": "The agent could not finish. Please try again."})
        finally:
            queue.put_nowait(None)

    task = asyncio.create_task(work())  # copies this context, so the agents publish to this run

    async def events():
        yield _sse({"type": "open", "mode": mode, "investigation_id": investigation_id})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), 15)
            except TimeoutError:
                yield ": still working\n\n"
                continue
            if event is None:
                break
            yield _sse(event)
        await task

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
