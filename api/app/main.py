"""SafeShelf API: the single front door for every screen, agent and bot.

Routes come from contracts/openapi.yaml. Each endpoint answers with its real handler
if one is registered in REAL_HANDLERS, otherwise with its example from contracts/mock/.
MOCK=1 forces every endpoint to the mock, so the screens always have something to show.
The X-SafeShelf-Source response header says which one answered (real or mock).
"""
import copy
import json
import os
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

CONTRACTS_DIR = Path(os.environ.get("CONTRACTS_DIR", Path(__file__).resolve().parents[2] / "contracts"))
MOCK = os.environ.get("MOCK", "1") == "1"
API_KEY = os.environ.get("API_KEY")  # unset = no key check (local development)

Handler = Callable[[Request, dict[str, Any]], Awaitable[Any]]

# operationId -> real handler. Engine modules (M3-M6) register here as they finish.
REAL_HANDLERS: dict[str, Handler] = {}

spec = yaml.safe_load((CONTRACTS_DIR / "openapi.yaml").read_text())
app = FastAPI(title=spec["info"]["title"], version=spec["info"]["version"])
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
    if API_KEY and request.headers.get("x-api-key") != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or wrong X-API-Key")


def make_route(operation_id: str, mock_name: str, status: int) -> Handler:
    async def route(request: Request) -> JSONResponse:
        check_key(request)
        params = dict(request.path_params)
        real = None if MOCK else REAL_HANDLERS.get(operation_id)
        if real:
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
                status, response = next(iter(op["responses"].items()))
                content = response.setdefault("content", {}).setdefault("application/json", {})
                content["example"] = load_mock(op["x-mock"])
        app.openapi_schema = doc
    return app.openapi_schema


app.openapi = contract_openapi


# Not /healthz: Cloud Run reserves paths ending in "z".
@app.get("/health", include_in_schema=False)
def health() -> dict[str, Any]:
    return {"ok": True, "mock": MOCK, "real_endpoints": sorted(REAL_HANDLERS)}
