"""Shelf Chat: answers questions about one product, only from SafeShelf evidence.

One model call per question: the product's evidence is fetched first (in parallel), then Gemini answers from it.
Google's models are sometimes busy (503), so each model gets a short time limit and the next one is tried.
"""
import asyncio
import json
import logging
import os
import time
import uuid

from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import errors as genai_errors
from google.genai import types

from . import chat_core, tools
from .chat_core import EVIDENCE_ID, INSTRUCTION

# ADK prints a long traceback for every busy-model error; we handle those ourselves and log one line.
logging.getLogger("google_adk").setLevel(logging.CRITICAL)
log = logging.getLogger("shelf_chat")

# Tried in order. Newest models are often busy (503), so a quick stable one comes first.
MODELS = [m.strip() for m in os.environ.get("SAFESHELF_MODEL", "gemini-3.6-flash,gemini-3.5-flash,gemini-3-flash-preview").split(",") if m.strip()]
MODEL_TIMEOUT = float(os.environ.get("SAFESHELF_MODEL_TIMEOUT", "15"))  # seconds per model before trying the next
HEDGE_AFTER = float(os.environ.get("SAFESHELF_HEDGE_AFTER", "6"))  # seconds before the next model is started in parallel
COOLDOWN = 60  # seconds a busy model is skipped
QUOTA_COOLDOWN = 120  # seconds a rate-limited (429) model is skipped
_cooling: dict[str, float] = {}
APP = "safeshelf-chat"

_sessions = InMemorySessionService()
_runners: dict[str, Runner] = {}


def _build(model: str) -> tuple[Agent, Runner]:
    agent = Agent(
        # one try per call: our own loop decides when to move to the next model
        model=Gemini(model=model, retry_options=types.HttpRetryOptions(attempts=1)),
        name="shelf_chat",
        description="Answers a shopper's questions about one product, grounded in SafeShelf evidence.",
        instruction=INSTRUCTION,
    )
    return agent, Runner(agent=agent, app_name=APP, session_service=_sessions, auto_create_session=True)


agent, _runners[MODELS[0]] = _build(MODELS[0])  # the primary agent (also used by tests)


def _runner(model: str) -> Runner:
    if model not in _runners:
        _runners[model] = _build(model)[1]
    return _runners[model]


async def _context(product_id: str) -> tuple[str, set[str]]:
    """Fetch all evidence for the product at once. Returns it as JSON text plus the evidence IDs it contains."""
    names = ["product", "safety", "relationships", "history", "certifications", "alternatives"]
    fns = [tools.get_product, tools.get_safety, tools.get_relationships, tools.get_history, tools.get_certifications, tools.get_alternatives]
    results = await asyncio.gather(*(asyncio.to_thread(fn, product_id) for fn in fns))
    data = {n: r for n, r in zip(names, results) if "unavailable" not in r and "error" not in r}  # only real answers
    text = json.dumps(data, ensure_ascii=False, default=str)
    return text, set(EVIDENCE_ID.findall(text))


async def _run(model: str, session_id: str, prompt: str) -> str:
    text = ""
    async for event in _runner(model).run_async(
        user_id="shopper",
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content:
            text += "".join(p.text or "" for p in event.content.parts or [])
    return text


def _busy(err: BaseException) -> bool:
    return isinstance(err, (genai_errors.ServerError, asyncio.TimeoutError)) or getattr(err, "code", None) == 429


async def _race(models: list[str], session_id: str, prompt: str) -> str:
    """Start the first model; if it is slow or fails, start the next in parallel. The first answer wins."""
    queue = list(models)
    running: dict[asyncio.Task, str] = {}
    last_error: BaseException | None = None

    def start() -> None:
        model = queue.pop(0)
        running[asyncio.create_task(asyncio.wait_for(_run(model, f"{session_id}-{model}", prompt), MODEL_TIMEOUT))] = model

    start()
    try:
        while running:
            done, _ = await asyncio.wait(running, timeout=HEDGE_AFTER if queue else None, return_when=asyncio.FIRST_COMPLETED)
            if not done:  # still waiting on the first model: hedge with the next one
                start()
                continue
            for task in done:
                model = running.pop(task)
                try:
                    return task.result()
                except Exception as err:  # busy or slow: remember it and move on; anything else is a real error
                    if not _busy(err):
                        raise
                    quota = getattr(err, "code", None) == 429
                    _cooling[model] = time.monotonic() + (QUOTA_COOLDOWN if quota else COOLDOWN)
                    log.warning("%s busy (%s), skipping it for %ss", model, type(err).__name__, QUOTA_COOLDOWN if quota else COOLDOWN)
                    last_error = err
            if queue and not running:
                start()
        raise last_error or RuntimeError("no model configured")
    finally:
        for task in running:
            task.cancel()


async def _race(models: list[str], session_id: str, prompt: str) -> str:
    """Start the first model; if it is slow or fails, start the next in parallel. The first answer wins."""
    queue = list(models)
    running: dict[asyncio.Task, str] = {}
    last_error: BaseException | None = None

    def start() -> None:
        model = queue.pop(0)
        running[asyncio.create_task(asyncio.wait_for(_run(model, f"{session_id}-{model}", prompt), MODEL_TIMEOUT))] = model

    start()
    try:
        while running:
            done, _ = await asyncio.wait(running, timeout=HEDGE_AFTER if queue else None, return_when=asyncio.FIRST_COMPLETED)
            if not done:  # still waiting on the first model: hedge with the next one
                start()
                continue
            for task in done:
                model = running.pop(task)
                try:
                    return task.result()
                except Exception as err:  # busy or slow: remember it and move on; anything else is a real error
                    if not _busy(err):
                        raise
                    quota = getattr(err, "code", None) == 429
                    _cooling[model] = time.monotonic() + (QUOTA_COOLDOWN if quota else COOLDOWN)
                    log.warning("%s busy (%s), skipping it for %ss", model, type(err).__name__, QUOTA_COOLDOWN if quota else COOLDOWN)
                    last_error = err
            if queue and not running:
                start()
        raise last_error or RuntimeError("no model configured")
    finally:
        for task in running:
            task.cancel()


UNMATCHED = {"", "unmatched", "unknown", "none"}


def _history_text(history: list[dict] | None) -> str:
    lines = [f"{'Shopper' if h.get('role') == 'user' else 'SafeShelf'}: {str(h.get('text', ''))[:500]}" for h in (history or [])[-6:]]
    return "\n".join(lines)


async def ask(product_id: str, message: str, language: str = "en", session_id: str | None = None,
              context: dict | None = None, history: list[dict] | None = None) -> dict:
    """Ask one question. `context` is the check result the shopper just saw; `history` the earlier turns of this chat.
    Returns the contract shape: text plus only the evidence IDs the data really contains."""
    session_id = session_id or f"SS-A-{uuid.uuid4().hex[:8]}"
    evidence = "{}" if chat_core.is_unmatched(product_id) else (await _context(product_id))[0]  # no stored evidence for an unmatched listing
    prompt, seen = chat_core.prepare(product_id, message, language, evidence, context, history)
    now = time.monotonic()
    order = [m for m in MODELS if _cooling.get(m, 0) <= now] or MODELS  # skip models that just failed, unless all did
    text = await _race(order, session_id, prompt)
    return chat_core.result(product_id, language, session_id, text, seen)
