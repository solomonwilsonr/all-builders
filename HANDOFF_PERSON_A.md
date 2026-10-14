# Handoff: what Person B (extension and chat) needs from the API

For Person A, who owns `engine/` and `api/`. Everything here is written so you can act on it without asking me.
Status date: 14 Oct 2026. Live API checked: `https://safeshelf-api-368488022657.asia-south1.run.app`.

## 1. Where things stand

The Chrome extension talks **only** to your live API (no local service, no example data). It asks `/health` which endpoints are real and shows "Not live on the SafeShelf API yet" for the rest, so every endpoint you make real lights up in the UI by itself.

| Endpoint | Live on your server | Used by the extension |
|---|---|---|
| `trust-check`, `safety`, `certifications`, `relationships`, `duplicates`, `identify` | yes | Check card, Marks, Copies, Details |
| `products/{id}`, `history`, `alternatives`, `reports`, `bench/results` | yes (new since 13 Oct) | Details, History, Safer options, Report, Judges' Lab |
| `agent/sessions` | **no, returns an example** | the chat under the result |
| `shelf/items` | **no, returns an example**; no GET | Save (kept in the browser for now) |
| `evidence` | **no, 404** (my addition to the contract) | evidence quotes under chat answers |
| `catalog/scan`, `investigations/{id}/trace` | no | Judges' Lab |

What the extension needs next, in order of value: **A. chat, B. evidence, C. latency, D. product on demand, E. shelf.**

## 2. A. Switch on the chat (about 5 minutes)

`agents/api_handler.py` is a ready handler for `POST /v1/agent/sessions`. It reads stored evidence straight from `safety`, `identity` and `marks`, calls Gemini through your `engine.gemini.client()` (Vertex, location `global`), tries your model order with a 20 s limit each, and keeps only evidence IDs that exist in the data.

1. Copy `agents/safeshelf_agents/chat_core.py` to `engine/chat_core.py`, and `agents/api_handler.py` to `engine/chat.py`.
2. In `engine/api_handlers.py`: `from engine import chat`, and add `**chat.HANDLERS` to `HANDLERS`.
3. Redeploy. `GET /health` should list `startAgentSession` under `real_endpoints`.

Request fields beyond the contract (all optional): `session_id`, `context` (the check result the shopper just saw), `history` (earlier turns, `[{role, text}]`). `product_id` may be `"unmatched"`; then the answer uses only `context`.
Cost: one Vertex Gemini call per question, in your project. Tests (no Google calls): `cd agents && uv run pytest`.

## 3. B. `GET /v1/evidence?ids=EV-1,EV-2` (needs your data)

Contract and a mock are already in `contracts/` (`/v1/evidence`, schema `Evidence`). The extension shows, under each chat answer, what each cited ID points to, with a "Show on page" button that scrolls to the quote.
Your `evidence` table already has what is needed. Return one object per ID:

| Field | From |
|---|---|
| `evidence_id` | `evidence.id` |
| `type` | `source_type` (review, review_photo, recall, registry...) |
| `source` | a plain-words label, e.g. "Customer review on Amazon.in" |
| `date` | `observed_at` (date only) |
| `rating` | from `content`, if it is a review |
| `quote` | **the exact review text from `content`**. The extension finds it on the page by matching this text, so do not paraphrase or trim the start. |
| `url` | `source_ref` when it is a link, else null |

## 4. C. Latency of `trust-check` (it blocks the demo)

Measured on the live API, same listing: **112 s, 75 s, 42 s** (`safety` takes about 10 s). A shopper will not wait that long. Suggestions: `--min-instances 1` (cold start), and look at the look-alike path (embeddings plus Gemini compare). The extension waits up to 150 s and says "can take up to a minute", but that is not a good experience.

## 5. D. Products that are not in the catalog

For a listing not in the catalog, `trust-check` returns `matched_by: look_alike` with the nearest *similar* product's ID. The extension treats that as "no exact match": no safety claim, no Save to the API, no report. Two things would fix most pages:
- An **"add on demand"**: when nothing matches, create a catalog product for the listing and return its ID with `matched_by: "created"`.
- Or an explicit `exact: true|false` in the answer instead of inferring it from `matched_by` (`url` and `model_number` count as exact today).

## 6. E. The shelf (`/v1/shelf/items`)

Today `POST` answers with the same example item whatever you send, stores nothing, and `GET` gives 405. The extension keeps the shelf in the browser (`SHELF_SYNC = false` in `extension/config.js`); flip it to `true` when this works.
Suggested shape (adapt to `data/schema.sql`):

```sql
CREATE TABLE IF NOT EXISTS shelf_items (
    item_id       TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,                 -- a random install id today ("install-7f3a9c"), Firebase uid later
    product_id    TEXT REFERENCES products(id),  -- may be NULL (listing not in the catalog)
    listing_url   TEXT,
    title         TEXT,
    added_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    recall_status TEXT NOT NULL DEFAULT 'not_checked',
    last_checked  TIMESTAMPTZ,
    next_check    TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS shelf_items_once ON shelf_items (user_id, COALESCE(product_id, listing_url));
```
- `POST /v1/shelf/items` `{product_id?, listing_url?, title?, user_id}`: store, safe to repeat (update, do not duplicate); accept a listing without `product_id`.
- `GET /v1/shelf/items?user_id=...`: list. `DELETE /v1/shelf/items/{item_id}`: remove.
- Later: a daily Cloud Scheduler job fills `recall_status` and `next_check` from your recalls data.

## 7. What the extension sends and shows (so you can sanity-check it)

- `trust-check` body: `url` (tracking parameters removed; Amazon becomes `/dp/ASIN`), `title`, `price`, `currency`, `seller`, up to 8 product `image_urls`, and `page_text` (product sections only, up to 4,200 characters, technical details first). Name, address, pincode, emails and phone numbers are filtered out before sending.
- The colour is set in code from your fields: `flag` counts, `unknown` is never shown as good news (it becomes a grey "Not enough evidence yet"), and a look-alike match makes no safety claim.
- Every AI-backed action (`trust-check`, `identify`, `duplicates`, chat) first shows an estimated cost in rupees. **Please tell me your real per-call token numbers** so the estimates stop being guesses (currently: check ₹1 to ₹5, identify ₹0.2 to ₹1, duplicates ₹1 to ₹5, chat ₹0.6).

## 8. What I changed in shared folders

- `contracts/openapi.yaml`: added `GET /v1/evidence` and the `Evidence` schema. `contracts/mock/evidence.json`: its example. Nothing removed, 19 API tests pass.
- Nothing in `api/`, `engine/` or `data/`.

## 9. Running and testing my side

- `make test-extension`: 5 test files in plain Node (no Chrome, no network, no credits).
- `cd agents && uv run pytest`: 12 tests (handler, shared core, tools), all with stand-ins.
- **Not tested:** the handler against your real database and Vertex project. After you deploy it, ask one real question and check the answer cites real IDs.
- Load the extension: `chrome://extensions` → Developer mode → Load unpacked → the `extension/` folder. Demo shop pages: `make demo-pages`.

## 10. Questions for you

1. Real per-call cost (tokens or rupees) of `trust-check`, `identify` and `duplicates`?
2. Where do review quotes live: `evidence.content` (JSON keys?) or somewhere else?
3. Can `trust-check` return an explicit `exact` flag, and can unmatched listings be created on demand?
4. When can `shelf/items` and `agent/sessions` go live?
