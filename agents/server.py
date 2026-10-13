"""Agent service: same contract as POST /v1/agent/sessions in contracts/openapi.yaml.

Run: make agents   (needs GOOGLE_API_KEY in agents/.env, and the API on SAFESHELF_API)
Later the API can serve this endpoint itself; the extension won't notice.
"""
from typing import Literal

from dotenv import load_dotenv

load_dotenv()  # reads agents/.env before ADK looks for the key

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from safeshelf_agents.shelf_chat import _busy as busy  # noqa: E402
from safeshelf_agents.shelf_chat import ask  # noqa: E402

app = FastAPI(title="SafeShelf agents")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class SessionRequest(BaseModel):
    mode: Literal["chat", "investigate"]
    product_id: str  # "unmatched" when the listing could not be matched to a known product
    message: str = ""
    language: Literal["en", "hi"] = "en"
    session_id: str | None = None
    context: dict | None = None  # the check result the shopper just saw
    history: list[dict] | None = None  # earlier turns of this chat: {role, text}


@app.post("/v1/agent/sessions")
async def start_session(req: SessionRequest) -> JSONResponse:
    if req.mode != "chat":
        return JSONResponse({"detail": "Investigate is not built yet"}, status_code=501)
    try:
        body = await ask(req.product_id, req.message, req.language, req.session_id, req.context, req.history)
    except Exception as err:
        if busy(err):  # every model is rate-limited or overloaded: tell the shopper to retry, don't pretend
            return JSONResponse({"detail": "The AI is busy right now. Please try again in a minute."}, status_code=503)
        return JSONResponse({"detail": f"Shelf Chat could not answer: {type(err).__name__}: {err}"}, status_code=502)
    return JSONResponse(body, headers={"X-SafeShelf-Source": "real"})


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
