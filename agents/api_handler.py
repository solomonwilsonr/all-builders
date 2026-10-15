"""Shelf Chat as a handler for POST /v1/agent/sessions (operationId startAgentSession), for Person A's API.

It answers inside the API process, so the extension talks to ONE backend and nothing runs on a laptop.
It reads stored evidence straight from the engine modules (no HTTP) and calls Gemini through engine.gemini.client()
(Vertex AI, location "global"), trying the models in order and skipping slow or busy ones.

To switch it on (Person A, about 5 minutes):
  1. Copy agents/safeshelf_agents/chat_core.py to engine/chat_core.py and this file to engine/chat.py.
  2. In engine/api_handlers.py:   from engine import chat           and add   **chat.HANDLERS   to HANDLERS.
  3. Redeploy. GET /health should list "startAgentSession" under real_endpoints.
Cost: one Vertex Gemini call per question (see CHAT_MODELS), in the API's own Google Cloud project.
"""
import json
import os

from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from google.genai import types

from engine import gemini, identity, marks, safety

try:
    from . import chat_core  # when copied into engine/
except ImportError:
    from safeshelf_agents import chat_core  # when run from agents/

# Newest models are often busy (503) or slow, so the order matches engine/gemini.py's.
CHAT_MODELS = [m.strip() for m in os.environ.get("SAFESHELF_CHAT_MODELS", "gemini-3.5-flash,gemini-3-flash-preview,gemini-3.5-flash-lite").split(",") if m.strip()]
TIMEOUT_S = int(os.environ.get("SAFESHELF_CHAT_TIMEOUT", "20"))  # per model, then the next one is tried


def _evidence(product_id: str) -> str:
    """Stored evidence for the matched product, as JSON. A part that cannot be read is simply left out."""
    data = {}
    for name, fn in (("safety", safety.safety), ("relationships", identity.relationships), ("certifications", marks.certifications)):
        try:
            data[name] = fn(product_id)
        except Exception:  # noqa: BLE001  unknown product or a data error: that part is missing, the rest still answers
            continue
    return json.dumps(data, ensure_ascii=False, default=str)


def _generate(prompt: str) -> str:
    errors = []
    for model in CHAT_MODELS:
        thinking = None if "lite" in model else types.ThinkingConfig(thinking_level="low")
        try:
            response = gemini.client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=chat_core.INSTRUCTION, temperature=0.2, thinking_config=thinking,
                    http_options=types.HttpOptions(timeout=TIMEOUT_S * 1000)),
            )
            return response.text or ""
        except Exception as error:  # noqa: BLE001  timeout, 429, 5xx: try the next model
            errors.append(f"{model}: {type(error).__name__}")
    raise HTTPException(status_code=503, detail="The AI is busy right now. Please try again in a minute.")


async def start_agent_session(request: Request, params: dict) -> dict:
    body = await request.json()
    if body.get("mode") != "chat":
        raise HTTPException(status_code=501, detail="Investigate is not built yet")
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Give a message")
    product_id = body.get("product_id")
    language = chat_core.language(body.get("language"), message)
    evidence = "{}" if chat_core.is_unmatched(product_id) else await run_in_threadpool(_evidence, product_id)
    prompt, seen = chat_core.prepare(product_id, message, language, evidence, body.get("context"), body.get("history"))
    text = await run_in_threadpool(_generate, prompt)
    return chat_core.result(product_id, language, body.get("session_id") or "SS-A-chat", text, seen)


HANDLERS = {"startAgentSession": start_agent_session}
