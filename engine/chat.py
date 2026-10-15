"""Shelf Chat: POST /v1/agent/sessions (operationId startAgentSession), mode "chat".

Person B's handler (agents/api_handler.py), moved into the engine so the extension talks to one backend.
Answers only from the product's stored evidence (safety, relationships, certifications) plus the check
result the shopper saw; code keeps only evidence IDs that really exist. Rules and prompt: engine/chat_core.py.
One Gemini call per question, under the same hard wall-clock limit as the rest of the engine.
"""
import json
import logging
import os

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from google.genai import types

from engine import chat_core, gemini, identity, marks, safety

# Newest models are often busy (503) or slow, so the order matches engine/gemini.py's.
CHAT_MODELS = [m.strip() for m in os.environ.get(
    "SAFESHELF_CHAT_MODELS", "gemini-3.5-flash,gemini-3-flash-preview,gemini-3.5-flash-lite").split(",") if m.strip()]
TIMEOUT_S = int(os.environ.get("SAFESHELF_CHAT_TIMEOUT", "20"))  # per model, then the next one is tried
log = logging.getLogger(__name__)


def _evidence(product_id: str) -> str:
    """Stored evidence for the matched product, as JSON. A part that cannot be read is left out."""
    data = {}
    for name, fn in (("safety", safety.safety), ("relationships", identity.relationships),
                     ("certifications", marks.certifications)):
        try:
            data[name] = fn(product_id)
        except Exception as error:  # noqa: BLE001  unknown product or a data error: that part is missing, the rest still answers
            log.info("chat evidence %s for %s unavailable: %s", name, product_id, type(error).__name__)
    return json.dumps(data, ensure_ascii=False, default=str)


def _generate(prompt: str) -> str:
    for model in CHAT_MODELS:
        thinking = None if "lite" in model else types.ThinkingConfig(thinking_level="low")
        try:
            response = gemini._bounded(
                gemini.client().models.generate_content, TIMEOUT_S + 5,
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=chat_core.INSTRUCTION, temperature=0.2, thinking_config=thinking,
                    http_options=types.HttpOptions(
                        timeout=TIMEOUT_S * 1000, retry_options=types.HttpRetryOptions(attempts=1))),
            )
        except Exception as error:  # noqa: BLE001  timeout (ours or the SDK's), 429, 5xx: try the next model
            log.warning("chat model %s failed: %s", model, type(error).__name__)
            continue
        gemini._record(model, response)
        return response.text or ""
    raise HTTPException(status_code=503, detail="The AI is busy right now. Please try again in a minute.")


def answer(body: dict) -> dict:
    if body.get("mode") != "chat":
        raise HTTPException(status_code=501, detail="Investigate is not built yet")
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Give a message")
    product_id = body.get("product_id")
    language = chat_core.language(body.get("language"), message)
    evidence = "{}" if chat_core.is_unmatched(product_id) else _evidence(product_id)
    prompt, seen = chat_core.prepare(product_id, message[:1000], language, evidence,
                                     body.get("context"), body.get("history"))
    return chat_core.result(product_id, language, body.get("session_id") or "SS-A-chat", _generate(prompt), seen)


async def start_agent_session(request: Request, params: dict) -> dict:
    return await run_in_threadpool(answer, await request.json())
