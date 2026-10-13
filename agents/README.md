# agents/ (Person B)

> **Status:** the extension's chat calls the live SafeShelf API, not this folder's service. Until Person A switches on `api_handler.py` (below), the live `/v1/agent/sessions` only returns an example answer and the extension shows "Shelf Chat is not live on the SafeShelf API yet". The ADK service in this folder is for local development only.

## Switching the chat on in the API (Person A, about 5 minutes)
`api_handler.py` is a ready-made handler for `POST /v1/agent/sessions`. It reads stored evidence straight from the engine modules, calls Gemini on Vertex through `engine.gemini.client()`, tries the models in order with a 20 s limit each, and keeps only evidence IDs that exist in the data.
1. Copy `agents/safeshelf_agents/chat_core.py` to `engine/chat_core.py` and `agents/api_handler.py` to `engine/chat.py`.
2. In `engine/api_handlers.py`: `from engine import chat`, and add `**chat.HANDLERS` to `HANDLERS`.
3. Redeploy. `GET /health` should list `startAgentSession` under `real_endpoints`.

Request fields beyond the contract (all optional, all additive): `session_id`, `context` (the check result the shopper just saw), `history` (earlier turns: `{role, text}`). Cost: one Vertex Gemini call per question. Tests (no Google calls): `cd agents && uv run pytest`.


Owned by Person B (Face). Built with Google's Agent Development Kit (ADK). See [MODULES.md](../MODULES.md) M9.

## Shelf Chat
Answers a shopper's question about one product, only from SafeShelf evidence, with evidence IDs, in English or Hindi. Says "I don't know" when the evidence doesn't answer.

- `safeshelf_agents/tools.py`: six tools that read the SafeShelf API (product, safety, relationships, history, certifications, alternatives).
- `safeshelf_agents/shelf_chat.py`: the agent and its rules. Cited IDs are checked in code: any ID the tools never returned is dropped.
- `server.py`: `POST /v1/agent/sessions` (same contract as `contracts/openapi.yaml`). `mode: investigate` answers 501 until it is built.

## Run
1. Get a key at https://aistudio.google.com/apikey and put it in `agents/.env` (git ignores it): `GOOGLE_API_KEY=...` (see `.env.example`).
2. `make agents` (this service on :8081). It reads the live SafeShelf API (Cloud Run); example answers from that API are dropped, never given to the model.
3. The extension's chat calls it. If this service isn't running, the chat says so.

Tests (no key needed): `cd agents && uv run --python 3.12 pytest`.

Switching to Vertex AI later is environment variables only: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`; drop the key.
