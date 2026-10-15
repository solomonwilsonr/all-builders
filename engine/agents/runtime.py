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
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import partial

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
    listener: Callable[[dict], None] | None = None  # live events for a streaming screen; must be thread-safe


def publish(event: dict) -> None:
    """Sends one live event (a step starting or finishing, the verdict) to a streaming screen, if one listens.
    Safe from worker threads: the ContextVar travels with asyncio.to_thread and the listener is thread-safe."""
    run = _run.get()
    if run and run.listener:
        run.listener(event)


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
    done = {"n": len(run.steps) + 1, "agent": agent, "tool": tool, "summary": summary[:300],
            "model": ", ".join(sorted({c["model"] for c in calls})) or None, "seconds": round(seconds, 2)}
    run.steps.append(done)
    publish({"type": "step", **done})
    if run.investigation_id:
        try:
            trace.record(run.investigation_id, f"{agent}.{tool}", seconds, calls, body or {}, summary=summary)
        except Exception as error:  # noqa: BLE001  the trace is a record, never a reason to fail the answer
            log.warning("trace step not written: %s", type(error).__name__)


def text_of(content: types.Content | None) -> str:
    return "".join(p.text or "" for p in (content.parts if content and content.parts else []) if not p.thought)


HEDGE_AFTER_S = float(os.environ.get("SAFESHELF_HEDGE_AFTER", "5"))  # no answer yet: start the next model too
COOL_S = 60  # a model that was slow or failed is tried last for this long
_cooling: dict[str, float] = {}


def _for_model(config: types.GenerateContentConfig, name: str) -> types.GenerateContentConfig:
    """Flash-Lite takes no thinking settings."""
    return config.model_copy(update={"thinking_config": None}) if "lite" in name and config.thinking_config else config


async def hedged(llm_request, models: list[str]) -> tuple[object, str]:
    """The same request to the first model; if it has not answered within HEDGE_AFTER_S, also to the next, and so
    on. The first good answer wins. Latency on one model swings from 3 s to minutes (13-15 Oct), so waiting out a
    timeout before falling back made answers take 20 s or more. Calls run in the engine's worker threads and a slow
    one is abandoned, never awaited: the SDK sometimes ignores both its own timeout and cancellation (14 Oct)."""
    loop = asyncio.get_running_loop()
    now = time.monotonic()
    queue = sorted(dict.fromkeys(models), key=lambda m: _cooling.get(m, 0) > now)  # cooling models go last
    running: dict[asyncio.Future, tuple[str, float]] = {}
    errors: list[str] = []

    def launch() -> None:
        name = queue.pop(0)
        call = partial(gemini.client().models.generate_content, model=name, contents=llm_request.contents,
                       config=_for_model(llm_request.config, name))
        running[loop.run_in_executor(gemini._calls, call)] = (name, time.monotonic())

    launch()
    first = next(iter(running.values()))[0]
    while running or queue:
        if not running:
            launch()
        now = time.monotonic()
        overdue = min(started + TURN_TIMEOUT_S for _, started in running.values()) - now
        wait_s = max(0.05, min(overdue, HEDGE_AFTER_S) if queue else overdue)
        done, _ = await asyncio.wait(running, timeout=wait_s, return_when=asyncio.FIRST_COMPLETED)
        for future in done:
            name, _ = running.pop(future)
            try:
                response = future.result()
            except Exception as error:  # noqa: BLE001  429, 5xx: this model sits out a while
                errors.append(f"{name}: {type(error).__name__}")
                _cooling[name] = time.monotonic() + COOL_S
                continue
            if name != first:  # the first model was slower than a backup: start with another next time
                _cooling[first] = time.monotonic() + COOL_S
            return response, name
        now = time.monotonic()
        for future, (name, started) in list(running.items()):
            if now - started >= TURN_TIMEOUT_S:  # abandoned: its thread finishes in the background
                running.pop(future)
                errors.append(f"{name}: no answer in {TURN_TIMEOUT_S}s")
                _cooling[name] = now + COOL_S
        if not done and queue and running:
            launch()
    raise RuntimeError("every model failed: " + "; ".join(errors))


def callbacks(model_name: str, last_resort=None) -> dict:
    """Every LlmAgent here calls Gemini through hedged() (ADK skips its own call when the callback answers) and records
    each turn as a step. If every model fails: last_resort(callback_context) -> text, or the error goes to the caller,
    whose own fallback answers."""
    async def before_model(callback_context, llm_request):
        started = time.monotonic()
        try:
            response, used = await hedged(llm_request, [model_name, *MODELS])
        except RuntimeError as error:
            log.warning("agent %s: %s", callback_context.agent_name, error)
            if not last_resort:
                raise
            text = last_resort(callback_context)
            step(callback_context.agent_name, "gemini", "No model answered; used the code's own words",
                 time.monotonic() - started)
            return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=text)]))
        answer = LlmResponse.create(response)
        meta = response.usage_metadata
        calls = [{"model": used, "input_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                  "output_tokens": (getattr(meta, "candidates_token_count", 0) or 0)
                  + (getattr(meta, "thoughts_token_count", 0) or 0)}] if meta else [{"model": used, "input_tokens": 0,
                                                                                      "output_tokens": 0}]
        asked = [p.function_call.name for p in (answer.content.parts if answer.content else []) or [] if p.function_call]
        step(callback_context.agent_name, "gemini", f"Decided to call {', '.join(asked)}" if asked else "Wrote the answer",
             time.monotonic() - started, calls)
        return answer
    return {"before_model_callback": before_model}


_sessions = InMemorySessionService()


async def run(build, message: str, state: dict | None = None, timeout_s: float = 45) -> tuple[str, dict]:
    """build(model_name) -> agent. Runs it on one message in a fresh session (each model call is hedged across the
    models, see hedged()). Returns the final text and the session state."""
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
