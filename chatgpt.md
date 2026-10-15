# SafeShelf Global: where the agentic solution stands

A self-contained brief to paste into ChatGPT (or hand to anyone new to the project). Status as of **15 Oct 2026, late evening** (Day 4 of 6).

- Team **Hashes**: Seshu Madhavan (team leader) and Solomon Wilson R.
- Event: **AI Builder Cup 2026** (Google Cloud JAPAC, run by Hack2skill). Theme: **Retail & Commerce**.
- Deadline: **18 Oct 2026, 11:59 PM IST** (we aim for 17 Oct). Feature freeze: evening of 16 Oct.
- Required stack: Gemini models, a Google agentic platform (we use **Google ADK**), deployed on **Google Cloud** (Cloud Run).
- Judging: Technical merit and GenAI use 40%, problem alignment and impact 25%, innovation 25%, UX 10%.

---

## 1. The goal

SafeShelf checks any online product listing and answers two questions for the shopper:

1. **Is it safe?** Official recalls, hazards that buyers describe in reviews and review photos (often before any recall), and safety marks checked against official registries.
2. **Is it real?** Photos copied from the genuine product, a price far below anything the genuine product sells for, a brand-new website, specs that contradict the genuine model, and text hidden on the page to manipulate AI assistants.

Both answers sit on one **product identity engine** that recognises the same product under different listings and brand names. One rule runs through everything:

> **Only an exact model inherits a recall. A possible rebrand goes to a human. A look-alike never does.**

Other principles:
- **Code sets the verdict colours (red / amber / green / grey); Gemini only gathers, picks and explains.** Page text can never change a verdict (prompt-injection defence).
- Every claim cites an **evidence ID**; IDs the tools never returned are dropped in code.
- "Not enough evidence" is shown as grey, never as good news.
- Agents are read-only and never submit anything (no purchases, sign-ins or regulator forms) without a person.
- **JAPAC first:** India (Amazon.in, Flipkart, BIS/ISI mark, Hindi), Japan (Amazon.co.jp, Consumer Affairs Agency, PSE mark), Australia/NZ (Amazon.com.au, ACCC, RCM mark), Singapore/SE Asia (Shopee, Lazada, CPSO, Safety Mark).

The pitch moment we want: a grandmother who can't read English recall notices; her grandson sends her heater's photo to the WhatsApp bot; she hears in Hindi that it was recalled and to stop using it.

---

## 2. The agentic solution (what "agentic" means here)

All agents are built with **Google ADK 2.12 on Vertex AI (Gemini 3.x)**, live inside the API in `engine/agents/`, and are reached through one endpoint, `POST /v1/agent/sessions` (plus `/v1/agent/sessions/stream` for live steps, and A2A at `/a2a/`).

| Mode | Agent | What it does |
|---|---|---|
| `investigate` | **Investigate pipeline** (SequentialAgent) | `page_reader` → a **ParallelAgent** of checks (is_it_real, safety_radar, twin_finder, recall_checker, cert_verifier, research_agent) → **verdict set by code** → `verdict_writer` explains it |
| `chat` | **Shelf Chat / Concierge** (LlmAgent with tools) | Answers questions about one product only from stored evidence, with evidence IDs, in English or Hindi. Can read a pasted link or a screenshot. Hands off to the Safer Alternative Finder |
| `alternatives` | **Safer Alternative Finder** | Suggests a safer genuine product to buy instead, with reasons |
| `report_draft` | **Investigation copilot** | Builds an evidence pack and a pre-filled regulator incident report; **never submitted** by code |
| `shopper_step` | **Shopper Agent** | Picks the next thing to open on the shopper's own page (label zoom, 1-star reviews, seller); the extension carries it out. Click blocklist (no buy, no sign-in), at most 15 steps / 60 s, Esc stops it |
| `research` | **Research Agent** | Headless Chromium on its own Cloud Run service (`safeshelf-research`) searches official recall sites that have no API; stops at captchas and blocks and says so |

Shared safety rules live in `engine/agents/guard.py`. Model calls are **hedged**: if the first model hasn't answered after a fraction of its timeout, the next one starts and the first good answer wins.

Other ways in: an **MCP server** at `/mcp` (so other AI agents can use SafeShelf's tools), an **A2A agent card** at `/.well-known/agent-card.json`, a **Chrome extension**, and a **WhatsApp bot**.

---

## 3. What we have achieved

### 3.1 Live on Google Cloud
- **API on Cloud Run**: https://safeshelf-api-368488022657.asia-south1.run.app (`/docs` for the contract). 18 endpoints answer with real data, including `startAgentSession`, `trustCheck`, `catalogScan`, `getCaseFile`, `getOwnerGuidance`, `getEvidence`, `getTrace`.
- **Research Agent** deployed as its own Cloud Run service.
- **Cloud SQL** (Postgres 16 + pgvector), **Vertex AI** (Gemini 3.x on location `global`), **Cloud Storage**, **Secret Manager**. The public API is rate-limited.

### 3.2 Engine modules (Person A track)
| Module | What it does |
|---|---|
| M3 Find copies | Fingerprints + brand-blind look-alike search (pgvector); Gemini compares pairs, code decides the 5 match classes |
| M4 Safety Radar | Gemini reads reviews (own experience vs hearsay, jokes, negation) and photos; code dedupes, rates and sets the verdict. 20/20 on hand-labelled reviews |
| M5 Recalls + marks | Exact model number = recalled; family-only notices go to review. Australian energy registry is real; BIS is a mock |
| M6 Is it real? | Copied photos, impossible price, new website (RDAP), spec conflicts, hidden AI instructions. Says "Be careful", never "scam" |
| Owner guidance + case file | "Already bought it?" steps, and an exportable case file awaiting human review |
| M14a Catalog Scan | Business side: a CSV of listings → ranked findings. **Precision 1.00, recall 0.98** on a 500-row test |

### 3.3 Data
- **27,492 Amazon + 286 Amazon.in/Flipkart products**, **29,379 real reviews** with Safety Radar labels.
- **2,537 US CPSC recalls** plus **6,116 JAPAC recall notices** (Australia, Japan, Korea, Taiwan, Singapore, ASEAN) via the OECD GlobalRecalls API.
- **8,470 Australian energy-registry records** (TVs, fridges).

### 3.4 Measured results
**Backtest** (25 past CPSC recalls, 40 never-recalled controls; do reviews warn before the recall?):

| Method | Recalls flagged early | False alarms |
|---|---|---|
| Keyword rules | 11/25 | 11/40 (28%) |
| Gemini alone | 6/25 | 6/40 (15%) |
| **SafeShelf** | **6/25** | **2/40 (5%)** |
| SafeShelf without twin pooling | 1/25 | 2/40 |

Honest headline: SafeShelf catches as many recalls early as Gemini alone with a third of the false alarms, and pooling evidence across rebranded twins is what makes it work (6 vs 1).

**Agent test set** (`make eval-agents`, 18 JAPAC cases with known answers, live API, 15 Oct): **18/18 passed, 49/49 checks**. Cases include: fake shop is red with hidden text caught; unknown product never gets invented safety; Hindi question gets a Hindi answer; injection in the question gives no safety promise; report draft is never sent; Shopper Agent never picks buy or sign-in; Japan CAA finds the real Anker PowerCore 10000 recall; CPSC finds the Anker A1263 recall; no recall invented for a fictional product; ACCC block reported, not hidden.

**Speed (live, median)**: investigate 4.7 s (colours arrive in ~3 s), chat 5.4 s, report draft 5.7 s, Shopper step 1.4 s, Research Agent ~60 s per site.

### 3.5 Clients
- **Chrome extension** (MV3, v2.5.x): in-page check card, live agent steps, Shelf Chat with evidence quotes, Investigate overlay, report form, Judges' Lab page. Works on Amazon India, Japan, Australia, Singapore and Flipkart, with the right currency per shop; reads Amazon's current review markup and the critical-reviews page.
- **WhatsApp bot**: link or photo in, English or Hindi text plus a voice note out (Gemini TTS `gemini-3.1-flash-tts-preview`). Built and tested.
- **Chat test page** with image paste and live steps.

### 3.6 Real-world finding leads
- **Sunbeam heated blanket** (never recalled): 74 own-experience fire/burn reports (3 with damage confirmed in photos) and 13 shock reports in 7,430 reviews. Checked that CPSC recall 23157 covers a different model.
- Recalled products still listed today (e.g. a recalled AmazonBasics ceramic heater).

---

## 4. What is blocked

| Blocker | What it breaks | How we handle it |
|---|---|---|
| **Amazon blocks Cloud Run** from reading product pages (title only, no price or reviews) | A link pasted into chat or WhatsApp can't be fully checked by the server | The answer says price and reviews were not checked. We use the product name from the share text or the URL, accept **screenshots** (Gemini reads them), and point to the extension, which reads the page in the shopper's own browser |
| **Recall sites that block robots**: ACCC (productsafety.gov.au) and the Australian energy registry (Akamai/CloudFront 403), Singapore CPSO, Japan METI recall pages | Research Agent can't search them live | It reports "a person needs to look" instead of guessing. The OECD GlobalRecalls API covers AU, JP, KR, SG and ASEAN notices as stored data. India has no public recall database |
| **Gemini model issues**: `gemini-3.5-flash` timed out on every image request; `gemini-3.8-flash` computer use is slow (8–45 s a step) and returns 500 after ~9 steps; Gemini 2.5 retires on Vertex on 16 Oct | Slow or failed calls | Hedged calls across models, `gemini-3-flash-preview` first for images, computer-use mode optional. All 2.5 references removed |
| **No WhatsApp number** | The bot can't be shown working on a real phone | Needs a Meta test number connected (planned for 16 Oct) |
| **Production deploys need a person** | `make deploy-api` is blocked for the AI coding assistant in auto mode | Solomon runs the deploy; the assistant then verifies the new revision and tests the live API |
| **Real-world finding not hand-checked** | Can't claim it in the deck or video yet | A person checks the Sunbeam label photo and evidence before anything is reported |

---

## 5. What still needs to be done

### Agentic solution
- [ ] **Judge-accessible web entry point** (biggest gap): a web Lab on Cloud Run or Firebase where a judge pastes a link and sees the check card, the agent steps, the bench table and the trace. Today the Lab lives inside the extension and `web/` is empty.
- [ ] **My Shelf backend**: `shelf_items` table and `POST/GET/DELETE /v1/shelf/items` (still a mock), then flip `SHELF_SYNC` in the extension. Later: a daily recall re-check (Cloud Scheduler) and alerts after purchase.
- [ ] **Deploy the WhatsApp bot** and connect a Meta test number; record the Hindi voice-note moment.
- [ ] **Challenge cases in the Lab**: look-alike, hidden page text, review farm, plus the "not enough evidence" answer.
- [ ] Hand-check the real-world finding and write its evidence pack; send it to the regulator only after a person confirms (17 Oct).
- [ ] **"Still on sale" number**: count recalled products whose exact copies are still listed under other names (rebrands reported separately as "under review"; hand-check 20 rows).
- [ ] Final `make bench` and `make eval-agents` before freeze; `make warm` before recording.
- [ ] Accessibility pass: Lighthouse ≥ 95, keyboard walkthrough, Hindi summary.

### Not built (vision, after submission)
Image embeddings for copied photos (pHash only today), Agent Engine hosting, Pub/Sub workers, BigQuery, Firebase Auth and push messaging, phone-camera "scan what you own", ask by voice, a regulator form agent that fills the form and stops before Submit, Seller tab.

### Submission (17 Oct)
- [ ] 3-minute demo video following the hero script: backtest headline → fake shop page → copies tab → TV mark mismatch → Shelf Chat ("Is this OK in my kid's room?") → same answers over curl/MCP with the trace → Hindi and read-aloud → WhatsApp grandmother moment.
- [ ] Deck from the official 16-slide template (measured numbers only on the benchmark slide; limits stated), exported to PDF.
- [ ] Regenerate `SafeShelf_Global.pdf`; README with architecture diagram; make the GitHub repo public.
- [ ] Submit: deployed link, public repo, video, deck.

---

## 6. Where to look in the repo

| Path | What |
|---|---|
| `plan.md` | The single brief: architecture, low-level design, status, gaps, remaining plan |
| `engine/agents/` | The ADK agents (pipeline, concierge, copilot, shopper, research, a2a, guard, runtime) |
| `engine/` | Identity, safety radar, recalls, marks, trust, catalog scan, owner guidance, case file |
| `api/` | FastAPI app on Cloud Run, MCP server, contract routing |
| `research/` | Research Agent's headless-browser service |
| `extension/` | Chrome extension |
| `whatsapp/` | WhatsApp bot |
| `bench/` | Backtest, agent test set, catalog scan test |
| `contracts/openapi.yaml` | The API contract |
| `SAFESHELF.md`, `MODULES.md`, `IMPACT.md` | Full vision, the 19 modules, social-impact plan |
