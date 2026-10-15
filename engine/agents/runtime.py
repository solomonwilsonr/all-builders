"""Models, the per-request run record and the ADK runner, shared by every agent.

Each request gets one Run (a ContextVar, so tools, callbacks and nested agents in the same request share it): the
steps shown to the shopper and the Lab, every evidence ID the agents actually read, and the investigation ID the
steps are written under (GET /v1/investigations/{id}/trace). A model that is slow or busy is replaced by the next one.
"""
import asyncio
import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from engine import gemini, trace
from engine.chat_core import EVIDENCE_ID

# Same order as engine/gemini.py: the newest models are often busy (503) or slow.
MODELS = [m.strip() for m in os.environ.get(
    "SAFESHELF_AGENT_MODELS", "gemini-3.5-flash,gemini-3-flash-preview,gemini-3.5-flash-lite").split(",") if m.strip()]
TURN_TIMEOUT_S = int(os.environ.get("SAFESHELF_AGENT_TURN_TIMEOUT", "20"))  # one model call
APP = "safeshelf"
log = logging.getLogger(__name__)
logging.getLogger("google_adk").setLevel(logging.ERROR)  # one line per failed model is logged here instead


def model(name: str) -> Gemini:
    """A Gemini 3.x model on Vertex AI (location global). One try per call: falling back to the next model is the retry."""
    return Gemini(model=name, retry_options=types.HttpRetryOptions(attempts=1),
                  client_kwargs={"vertexai": True, "project": gemini.PROJECT, "location": "global"})


def config(**extra) -> types.GenerateContentConfig:
    """Low thinking, as in engine/gemini.py: a tool-using turn takes about 3 s instead of 5 to 7 s."""
    return types.GenerateContentConfig(
        temperature=0.2, thinking_config=types.ThinkingConfig(thinking_level="low"),
        http_options=types.HttpOptions(timeout=TURN_TIMEOUT_S * 1000), **extra)


@dataclass
class Run:
    investigation_id: str | None = None
    steps: list[dict] = field(default_factory=list)
    seen: set[str] = field(default_factory=set)  # evidence IDs the agents read; answers may cite only these
    results: dict[str, object] = field(default_factory=dict)  # latest answer of each tool, by operationId


_run: ContextVar[Run | None] = ContextVar("agent_run", default=None)


def start(investigation_id: str | None = None) -> Run:
    run = Run(investigation_id)
    _run.set(run)
    return run


def current() -> Run:
    return _run.get() or start()


def new_id(prefix: str = "SS-I-") -> str:
    return prefix + uuid.uuid4().hex[:8].upper()


def saw(body) -> None:
    """Remember the evidence IDs in something an agent read."""
    current().seen.update(EVIDENCE_ID.findall(json.dumps(body, ensure_ascii=False, default=str)))


def step(agent: str, tool: str, summary: str, seconds: float, calls: list[dict] | None = None,
         body: dict | None = None) -> None:
    """One step for the shopper's step list and, with an investigation ID, the Lab trace."""
    run = current()
    calls = calls or []
    run.steps.append({"n": len(run.steps) + 1, "agent": agent, "tool": tool, "summary": summary[:300],
                      "model": ", ".join(sorted({c["model"] for c in calls})) or None, "seconds": round(seconds, 2)})
    if run.investigation_id:
        try:
            trace.record(run.investigation_id, f"{agent}.{tool}", seconds, calls, body or {}, summary=summary)
        except Exception as error:  # noqa: BLE001  the trace is a record, never a reason to fail the answer
            log.warning("trace step not written: %s", type(error).__name__)


def text_of(content: types.Content | None) -> str:
    return "".join(p.text or "" for p in (content.parts if content and content.parts else []) if not p.thought)


def after_model(model_name: str):
    """Records each model turn as a step: what the agent asked for, or that it wrote its answer."""
    def callback(callback_context, llm_response):
        meta = llm_response.usage_metadata
        calls = [{"model": model_name, "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                  "output_tokens": (getattr(meta, "candidates_token_count", 0) or 0)
                  + (getattr(meta, "thoughts_token_count", 0) or 0)}] if meta else []
        asked = [p.function_call.name for p in (llm_response.content.parts if llm_response.content else []) or []
                 if p.function_call]
        summary = f"Decided to call {', '.join(asked)}" if asked else "Wrote the answer"
        started = callback_context.state.get("temp:turn_started")
        step(callback_context.agent_name, "gemini", summary, time.monotonic() - started if started else 0, calls)
    return callback


def on_model_error(model_name: str, last_resort=None):
    """When a model call fails (timeout, 429, 5xx), the same request goes to the next model, so a busy model never
    re-runs the checks before it. If every model fails: last_resort(callback_context) -> text answers instead, or
    the error stands and the caller's own fallback answers."""
    async def callback(callback_context, llm_request, error):
        log.warning("agent model %s failed: %s", model_name, type(error).__name__)
        for name in [m for m in MODELS if m != model_name]:
            try:
                response = await asyncio.wait_for(gemini.client().aio.models.generate_content(
                    model=name, contents=llm_request.contents, config=llm_request.config), TURN_TIMEOUT_S + 5)
            except Exception as again:  # noqa: BLE001
                log.warning("agent model %s failed: %s", name, type(again).__name__)
                continue
            return LlmResponse.create(response)
        if last_resort:
            text = last_resort(callback_context)
            return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))
        return None
    return callback


def callbacks(model_name: str, last_resort=None) -> dict:
    """The callbacks every LlmAgent here uses: steps and tokens for the trace, and model fallback."""
    return {"before_model_callback": before_model, "after_model_callback": after_model(model_name),
            "on_model_error_callback": on_model_error(model_name, last_resort)}


def before_model(callback_context, llm_request):
    callback_context.state["temp:turn_started"] = time.monotonic()


_sessions = InMemorySessionService()


async def run(build, message: str, state: dict | None = None, timeout_s: float = 45) -> tuple[str, dict]:
    """build(model_name) -> agent. Runs it on one message in a fresh session, with the first model (on_model_error
    moves a failed call to the next). Returns the final text and the session state."""
    return await asyncio.wait_for(_execute(build(MODELS[0]), message, state), timeout_s)


async def _execute(agent, message: str, state: dict | None) -> tuple[str, dict]:
    runner = Runner(agent=agent, app_name=APP, session_service=_sessions, auto_create_session=True)
    session_id = uuid.uuid4().hex
    final = ""
    async for event in runner.run_async(
            user_id="shopper", session_id=session_id, state_delta=state or None,
            new_message=types.Content(role="user", parts=[types.Part(text=message)])):
        if event.is_final_response() and event.content:
            final = text_of(event.content) or final
    session = await _sessions.get_session(app_name=APP, user_id="shopper", session_id=session_id)
    await _sessions.delete_session(app_name=APP, user_id="shopper", session_id=session_id)
    return final, dict(session.state) if session else {}
