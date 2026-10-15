# agents/ (Person B)

> **Status (15 Oct):** the live agents are now served by the SafeShelf API itself, from [engine/agents/](../engine/agents/__init__.py) (Google ADK 2.12 on Vertex AI). The extension, WhatsApp bot, Lab and other AI agents all reach them at `POST /v1/agent/sessions` (and over A2A at `/a2a/`). This folder's service is the earlier local-only Shelf Chat, kept for development.

| Mode | Agent (ADK) | What it does |
|---|---|---|
| `chat` | `shelf_chat` LlmAgent + tools, `safer_alternative_finder` as an AgentTool | Reads stored evidence through tools, answers with evidence IDs (English/Hindi); one-call chat is the fallback |
| `investigate` | `investigate` SequentialAgent: `page_reader` → `checks` ParallelAgent (is_it_real, safety_radar, twin_finder, recall_checker, cert_verifier, research_agent) → `verdict` (code) → `verdict_writer` LlmAgent | Is it safe? Is it real? Colours set by code; Gemini explains |
| `alternatives` | `safer_alternative_finder` | Safer products to buy instead, with reasons |
| `report_draft` | `investigation_copilot` (output schema) | Evidence pack + pre-filled regulator incident report; never submitted |
| `shopper_step` | Shopper Agent | Picks the next thing to open on the shopper's page; the extension (`extension/investigate.js`) does it |
| `research` | Research Agent ([research/](../research/browser.py), own Cloud Run service) | Headless Chromium on CPSC, EU Safety Gate, ACCC; stops at blocks and captchas |

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
