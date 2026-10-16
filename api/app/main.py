"""SafeShelf API: the single front door for every screen, agent and bot.

Routes come from contracts/openapi.yaml. Each endpoint answers with its real handler
if one is registered in REAL_HANDLERS, otherwise with its example from contracts/mock/.
MOCK=1 forces every endpoint to the mock, so the screens always have something to show.
The X-SafeShelf-Source response header says which one answered (real or mock).
Other AI agents use the same answers as MCP tools at /mcp (app/mcp_server.py) and talk to the SafeShelf agent
over A2A at /a2a/ (engine/agents/a2a.py, real engine only).
"""
import copy
import json
import logging
import os
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app import mcp_server

CONTRACTS_DIR = Path(os.environ.get("CONTRACTS_DIR", Path(__file__).resolve().parents[2] / "contracts"))
MOCK = os.environ.get("MOCK", "1") == "1"
API_KEY = os.environ.get("API_KEY")  # unset = no key check (local development)
MAX_BODY = 1_000_000  # bytes; listings and reports are small
MAX_AGENT_BODY = 9_000_000  # the chat takes a screenshot: 6 MB of image is 8 MB as base64
# The API is public (the extension and the judges call it without a key), so engine calls that can spend Gemini
# credit are rate-limited per caller and capped per day per instance (deploy uses --max-instances 3).
RATE_PER_MIN = int(os.environ.get("SAFESHELF_RATE_PER_MIN", "30"))
DAILY_CAP = int(os.environ.get("SAFESHELF_DAILY_CAP", "3000"))
# Engine calls that only read the database: browsing the Recall Catalog must not use up the AI-check limit.
UNMETERED = {"listRecalls", "getRecall", "getSourcesHealth", "getInvestigation", "getInvestigationSources",
             "getRadarCandidates", "getCrossBorderCandidates", "getBenchRuns", "getBenchEvidence", "listWatchlists",
             "deleteWatchlist", "getReviewQueue", "getCase", "getDeveloperUsage", "getTimeline"}

log = logging.getLogger("safeshelf.api")
logging.basicConfig(level=logging.INFO, format="%(message)s")

Handler = Callable[[Request, dict[str, Any]], Awaitable[Any]]

# operationId -> real handler. Engine modules (M3-M6) register here as they finish.
REAL_HANDLERS: dict[str, Handler] = {}
if not MOCK and (os.environ.get("DATABASE_URL") or os.environ.get("CLOUD_SQL_INSTANCE")):
    from engine.api_handlers import HANDLERS  # needs the database and Vertex AI

    REAL_HANDLERS.update(HANDLERS)

spec = yaml.safe_load((CONTRACTS_DIR / "openapi.yaml").read_text())
app = FastAPI(title=spec["info"]["title"], version=spec["info"]["version"])


@app.middleware("http")
async def guard_and_log(request: Request, call_next):
    """Body size and API key checks (also for /mcp), then one JSON log line per request for Cloud Logging.
    Logs the path and outcome only, never request bodies."""
    started = time.monotonic()
    limit = MAX_AGENT_BODY if request.url.path.startswith("/v1/agent/sessions") else MAX_BODY
    if int(request.headers.get("content-length") or 0) > limit:
        response = JSONResponse({"detail": f"Request body too large (at most {limit // 1_000_000} MB)"},
                                status_code=413)
    elif API_KEY and request.url.path.startswith(("/mcp", "/a2a")) and request.headers.get("x-api-key") != API_KEY:
        response = JSONResponse({"detail": "Missing or wrong X-API-Key"}, status_code=401)
    elif request.url.path.startswith("/a2a") and request.method == "POST" and (reason := a2a_limit(request)):
        response = JSONResponse({"detail": reason}, status_code=429, headers={"Retry-After": "60"})
    else:
        response = await call_next(request)
    log.info(json.dumps({
        "severity": "WARNING" if response.status_code >= 500 else "INFO",
        "method": request.method, "path": request.url.path, "status": response.status_code,
        "ms": round(1000 * (time.monotonic() - started)), "source": response.headers.get("x-safeshelf-source"),
        "investigation_id": request.headers.get("x-investigation-id")}))
    return response


# Added after guard_and_log, so it is the outer layer: refusals (413, 401, 429) carry CORS headers too, and a
# browser shows their reason instead of "Failed to fetch".
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def load_mock(name: str) -> Any:
    return json.loads((CONTRACTS_DIR / "mock" / name).read_text())


def mock_answer(name: str, path_params: dict[str, Any]) -> Any:
    body = load_mock(name)
    # Echo the requested product so the screens show the ID they asked for.
    if "product_id" in path_params and isinstance(body, dict) and "product_id" in body:
        body["product_id"] = path_params["product_id"]
    return body


def check_key(request: Request) -> None:
    """With API_KEY set, only that key or a tenant key (ssk_..., checked against its hash by the engine) passes."""
    key = request.headers.get("x-api-key") or ""
    if API_KEY and key != API_KEY and not (key.startswith("ssk_") and REAL_HANDLERS):
        raise HTTPException(status_code=401, detail="Missing or wrong X-API-Key")


class Limiter:
    """Sliding one-minute window per caller plus a daily total. In memory: per instance, reset on restart."""

    def __init__(self, per_minute: int, per_day: int):
        self.per_minute, self.per_day = per_minute, per_day
        self.hits: dict[str, deque] = defaultdict(deque)
        self.day, self.today = "", 0

    def check(self, caller: str, now: float) -> str | None:
        """None if allowed, else the reason for a 429."""
        window = self.hits[caller]
        while window and now - window[0] > 60:
            window.popleft()
        day = time.strftime("%Y-%m-%d", time.gmtime(now))
        if day != self.day:
            self.day, self.today = day, 0
        if len(window) >= self.per_minute:
            return f"Too many requests: at most {self.per_minute} checks a minute. Try again shortly."
        if self.today >= self.per_day:
            return "The demo's daily limit of AI checks is reached. Try again tomorrow."
        window.append(now)
        self.today += 1
        return None


limiter = Limiter(RATE_PER_MIN, DAILY_CAP)


def rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for", "")
    caller = forwarded.split(",")[0].strip() or "internal"  # MCP tools call the routes in-process
    reason = limiter.check(caller, time.time())
    if reason:
        raise HTTPException(status_code=429, detail=reason, headers={"Retry-After": "60"})


def a2a_limit(request: Request) -> str | None:
    """A2A messages reach the agent (and Gemini) without passing make_route, so they share the same limiter."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return limiter.check(forwarded.split(",")[0].strip() or "internal", time.time())


def make_route(operation_id: str, mock_name: str, status: int) -> Handler:
    async def route(request: Request) -> JSONResponse:
        check_key(request)
        params = dict(request.path_params)
        real = None if MOCK else REAL_HANDLERS.get(operation_id)
        if real:
            if operation_id not in UNMETERED:
                rate_limit(request)  # only engine calls can spend Gemini credit; mocks are free
            body, source = await real(request, params), "real"
        else:
            body, source = mock_answer(mock_name, params), "mock"
        return JSONResponse(body, status_code=status, headers={"X-SafeShelf-Source": source})

    route.__name__ = operation_id
    return route


for path, methods in spec["paths"].items():
    for method, op in methods.items():
        status = int(next(iter(op["responses"])))
        app.add_api_route(
            path,
            make_route(op["operationId"], op["x-mock"], status),
            methods=[method.upper()],
            summary=op.get("summary"),
            operation_id=op["operationId"],
        )


def contract_openapi() -> dict[str, Any]:
    """/docs shows the contract itself (inputs, schemas) with each endpoint's mock as its example."""
    if app.openapi_schema is None:
        doc = copy.deepcopy(spec)
        doc["servers"] = [{"url": "/", "description": "This server"}]
        for methods in doc["paths"].values():
            for op in methods.values():
                _status, response = next(iter(op["responses"].items()))
                content = response.setdefault("content", {}).setdefault("application/json", {})
                content["example"] = load_mock(op["x-mock"])
        app.openapi_schema = doc
    return app.openapi_schema


app.openapi = contract_openapi


# Not /healthz: Cloud Run reserves paths ending in "z".
@app.get("/health", include_in_schema=False)
def health() -> dict[str, Any]:
    return {"ok": True, "mock": MOCK, "real_endpoints": sorted(REAL_HANDLERS)}


if REAL_HANDLERS:  # the A2A agent runs the real engine; with MOCK=1 there is nothing behind it
    from engine.agents import a2a

    @app.get("/.well-known/agent-card.json", include_in_schema=False)
    @app.get("/.well-known/agent.json", include_in_schema=False)
    def agent_card() -> RedirectResponse:
        return RedirectResponse("/a2a/.well-known/agent-card.json")

    app.mount("/a2a", a2a.mount)

    from engine.agents import handler as agent_handler

    @app.post("/v1/agent/sessions/stream", include_in_schema=False)
    async def agent_session_stream(request: Request):
        """The agents with live steps (server-sent events); same request body as POST /v1/agent/sessions."""
        check_key(request)
        rate_limit(request)
        return await agent_handler.stream_agent_session(request)

mcp_server.attach(app)  # last: it mounts at "/" behind every route above

if REAL_HANDLERS:
    _mcp_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def _lifespan(app_):
        async with _mcp_lifespan(app_), a2a.lifespan():
            yield

    app.router.lifespan_context = _lifespan
