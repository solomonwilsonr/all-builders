# SafeShelf modules: how we split the work

SafeShelf is split into **19 modules** (M0–M17, with M14 in two halves). Each one can be built by one person on their own and joined later. The day-by-day schedule is in [`PARALLEL_PLAN.md`](PARALLEL_PLAN.md); the full technical design is in [`SAFESHELF.md`](SAFESHELF.md).

**How we work separately:** in M0 we agree the exact shape of every API answer (`contracts/openapi.yaml` + example JSON in `contracts/mock/`). The Brain makes the engine return that shape; the Face builds against the mock until the real engine is ready.

## Tracks

| Track | What it is | Modules | Hours |
|---|---|---|---|
| **Shared** | Done together | M0, M17 | ≈ 14 h |
| **A: Brain** | Data, AI checks, server. Mostly Python, no screens | M1, M2, M3, M4, M5, M6, M7, M12, M14a, M16 | ≈ 49 h |
| **B: Face** | Everything people see and talk to | M8, M9, M10, M11, M13, M14b, M15 | ≈ 49 h |

Estimates are rough hours for one person using Claude Code. Without AI help, expect about double.

## Dependencies

An arrow means "needs this first". Dotted arrows: start early with mock data, switch to the real thing later.

```mermaid
flowchart TD
    M0["M0 Foundation"] --> M1["M1 Data collection"]
    M0 --> M7["M7 API server"]
    M1 --> M2["M2 Big test + Bench"]
    M1 --> M3["M3 Identity engine"]
    M1 --> M4["M4 Safety Radar"]
    M3 --> M5["M5 Recall + safety marks"]
    M3 --> M6["M6 Is it real?"]
    M4 --> M2
    M3 --> M7
    M4 --> M7
    M5 --> M7
    M6 --> M7
    M7 -.-> M8["M8 Extension + accessibility"]
    M7 -.-> M9["M9 AI agents"]
    M8 --> M9
    M7 -.-> M10["M10 My Shelf, scan, report"]
    M7 -.-> M11["M11 Website + account"]
    M10 --> M11
    M7 --> M12["M12 WhatsApp bot"]
    M9 --> M12
    M11 --> M12
    M9 --> M13["M13 Ask by voice"]
    M3 --> M14a["M14a Business backend"]
    M4 --> M14a
    M5 --> M14a
    M14a -.-> M14b["M14b Business screens"]
    M11 --> M14b
    M9 --> M14b
    M2 --> M15["M15 Judges' Lab"]
    M9 --> M15
    M11 --> M15
    M1 --> M16["M16 Real-world finding"]
    M3 --> M16
    M5 --> M16
    M15 --> M17["M17 Submission"]
    M16 --> M17
```

**Can start right away (after M0):** M1 (Brain); M8, M9, M10, M11 on mock data (Face). **Sign up today:** WhatsApp Business test number (M12) and Firebase (M10, M11). Approvals can take time.

## Overview

| Module | Track | Hours | Dates | Needs first | Start early with mock? |
|---|---|---|---|---|---|
| [M0 Foundation](#m0-foundation) | Shared | 3 | 12 Oct | — | Yes |
| [M1 Data collection](#m1-data-collection) | A | 6.5 | 12–14 Oct | M0 | Yes |
| [M2 Big test + SafeShelfBench](#m2-big-test--safeshelfbench) | A | 6.5 | 13–16 Oct | M1, M4 | Partly |
| [M3 Identity engine](#m3-identity-engine-find-copies) | A | 6.5 | 13 Oct (+15) | M1 | Partly |
| [M4 Safety Radar](#m4-safety-radar) | A | 3 | 13 Oct | M1 | Yes |
| [M5 Recall + safety marks](#m5-recall-check--safety-mark-check) | A | 4 | 14 Oct | M1, M3 | Partly |
| [M6 Is it real? + spec/price](#m6-is-it-real--spec-and-price-check) | A | 4 | 14 Oct | M3 | Partly |
| [M7 API server](#m7-api-server) | A | 4.5 | 12–15 Oct | M0 (real: M3–M6) | Yes |
| [M8 Extension + accessibility](#m8-browser-extension--accessibility) | B | 13 | 12–14 Oct | M7 (mock) | Yes |
| [M9 AI agents](#m9-ai-agents) | B | 12.5 | 13–14 Oct | M7 (mock), M8 | Yes |
| [M10 My Shelf, scan, report](#m10-my-shelf-camera-scan-report-form) | B | 7 | 15 Oct | M7 (mock); real alerts M5 | Yes |
| [M11 Website + account](#m11-website--one-account--share-button) | B | 4 | 15 Oct | M7, M10 | Yes |
| [M12 WhatsApp bot](#m12-whatsapp-bot) | A | 4.5 | 15 Oct | M7, M9, M11 | Partly |
| [M13 Ask by voice](#m13-ask-by-voice) | B | 2 | 16 Oct | M9 | Partly |
| [M14a Business backend](#m14a-business-backend) | A | 5.5 | 16 Oct | M3, M4, M5 | No |
| [M14b Business screens](#m14b-business-screens) | B | 5.5 | 16 Oct | M14a (mock), M11, M9 | Yes |
| [M15 Judges' Lab](#m15-judges-lab) | B | 4 | 16 Oct | M2, M9, M11 | Partly |
| [M16 Real-world finding](#m16-real-world-finding) | A | 5 (+1 together) | 15–17 Oct | M1, M3, M5 | Partly |
| [M17 Submission](#m17-submission) | Shared | 10.5 | 13 + 17 Oct | Everything | No |

## Join points

| When | What gets joined | How we know it worked |
|---|---|---|
| End of 12 Oct | M0 done; mock API (M7) live on Cloud Run | Person B can call the API and get the demo product back |
| End of 14 Oct | Real `identify`, `safety`, `certifications`, `trust-check` replace the mocks | The extension shows real results on the demo page |
| End of 15 Oct | Agents (M9) on the real API; My Shelf and website live | Investigate and Shelf Chat work end to end on the fake shop page |
| Midday 16 Oct | WhatsApp, voice, business screens, Lab joined | The full Lab path works start to finish |
| Evening 16 Oct | **Feature freeze** | Only bug fixes after this |

---

## M0 Foundation

**Shared · ⏱ 3 h together · 12 Oct**

The base both tracks build on. Its main job: **agree on the exact shape of the data** each part sends and receives.

**Steps**
- [ ] Repo folders: `engine/` `api/` `bench/` `data/` `whatsapp/` `extension/` `agents/` `web/` `lab/` `contracts/` (15 min)
- [ ] Google Cloud: billing on, $300 credit active, Vertex AI on (15 min)
- [ ] **Confirm the Gemini 3.x and computer-use model names on Vertex** (15 min). If computer use isn't on Vertex, M9 uses the Playwright fallback.
- [ ] Cloud SQL (Postgres + pgvector) and a Cloud Storage bucket (30 min)
- [ ] `contracts/openapi.yaml` with every endpoint: identify, duplicates, safety, certifications, trust-check, alternatives, history, catalog/scan, agent/sessions, shelf/items, reports (45 min)
- [ ] `contracts/mock/*.json`, one example answer per endpoint (copy the examples in SAFESHELF.md section 11) (30 min)
- [ ] Database tables as one SQL file (SAFESHELF.md section 10) (15 min)
- [ ] 3–5 demo products with fixed IDs, e.g. `SS-P-10291` (15 min)

**Needs first:** nothing.
**Prerequisites:** Google Cloud account with billing; GitHub access for both.
**Gives to others:** the contracts, mock data and demo IDs. Nobody changes `contracts/` without telling the other person.
**Done when:** both people can clone the repo, read the contracts, and load a mock answer for the demo product.

## M1 Data collection

**Track A · ⏱ 6.5 h · 12–14 Oct**

Get all the data into our database and storage.

**Steps**
- [ ] Load CPSC recalls into the `recalls` table (1 h)
- [ ] Load the Australian energy-rating registry CSV (1 h)
- [ ] Colab or cloud VM; stream Amazon Reviews 2023 (Cell Phones, Electronics, Home & Kitchen, Tools), keep only matched products (1 h + background)
- [ ] Firecrawl: current listings of recalled products, ACCC/OECD recalls, genuine product pages, seeded catalog (1.5 h; budget about 7,250 credits)
- [ ] Photos to Cloud Storage, metadata to Cloud SQL (1 h)
- [ ] Build the ~500-product test catalog for Catalog Scan, with recalled copies mixed in (1 h)

**Needs first:** M0.
**Prerequisites:** Firecrawl API key (credits expire 21 Oct); Colab or cloud VM (review files are 9–31 GB); Cloud SQL connection; scripts in [`feasibility/`](feasibility/) as a starting point.
**Gives to others:** filled database and photos for M2, M3, M4, M5, M14a, M16.
**Done when:** the demo products, their reviews, recalls and registry records are queryable in Cloud SQL.
**Minimum version:** Cell Phones only, demo products only.

## M2 Big test + SafeShelfBench

**Track A · ⏱ 6.5 h · 13–16 Oct**

Our **strongest proof**: would SafeShelf have warned early on 25+ past recalls? Plus a fair comparison: keyword rules vs Gemini alone vs SafeShelf.

**Steps**
- [ ] Keyword-rules baseline (1 h)
- [ ] Gemini-alone baseline: one good prompt, no engine (1 h)
- [ ] Full big test: 25+ recalls + never-recalled controls, rate-based alarm, twin pooling (3 h)
- [ ] `make bench` writes `bench/results.json` and the README table (1 h)
- [ ] Final run after everything is joined (0.5 h)

**Needs first:** M1, M4 (for the SafeShelf column).
**Prerequisites:** Colab or cloud VM; Gemini access. See [`BACKTEST.md`](BACKTEST.md).
**Gives to others:** `bench/results.json` for M15; the headline number for the video.
**Done when:** a clear result on 25+ recalls (median weeks early, false alarms). Honest either way: if Gemini alone does as well, we say so.
**Minimum version:** 15 recalls, keyword vs SafeShelf only.

## M3 Identity engine: find copies

**Track A · ⏱ 6.5 h · 13 Oct (+ history data 15 Oct)**

Recognises **the same product under different brand names**. Everything else builds on it.

**Steps**
- [ ] Clean product data: brand, model, units (W, mAh) (1 h)
- [ ] Fingerprint each product: text + image embeddings + key specs (1.5 h)
- [ ] Find look-alikes with vector search in pgvector (1 h)
- [ ] Gemini compares each pair: agreements, conflicts, proposed label, what would change the decision (1.5 h)
- [ ] Code applies 5 labels: exact model / rebrand / variant / only looks similar / shared part. **Only exact model inherits a recall.**
- [ ] Product history: every decision stored as a new version, never deleted (1.5 h, Day 4)

**Needs first:** M1.
**Prerequisites:** Vertex AI embeddings; pgvector.
**Gives to others:** `identify`, `duplicates`, `relationships`, `history`, `alternatives` → M7. Also used by M5, M6, M14a, M16.
**Done when:** for the demo charger it finds an exact copy, a possible rebrand (for review) and a look-alike (never "recalled").
**Minimum version:** exact identifiers + Gemini compare on the demo products.

## M4 Safety Radar

**Track A · ⏱ 3 h · 13 Oct**

Gemini reads each review and looks at each photo to spot **real danger** (fire, shock, choking, chemical).

**Steps**
- [ ] Review prompt: danger or not? what kind? own experience or a joke? (1 h)
- [ ] Gemini vision on review photos: real damage? which part? (1 h)
- [ ] Count copies of a complaint once; use a **rate**, not a count (0.5 h)
- [ ] Output `ai_findings` for the safety answer, labelled "under review" (0.5 h)

**Needs first:** M1 (can start on the feasibility-test reviews).
**Prerequisites:** Gemini access; ~20 hand-labelled reviews.
**Gives to others:** `ai_findings` → M7; used by M2.
**Done when:** "Melted on the first day" (with photo) is flagged; "without overheat" and "this charger is fire 🔥" are not.

## M5 Recall check + safety mark check

**Track A · ⏱ 4 h · 14 Oct**

Is this product on an official recall list? Is its safety label real and does it belong to this product?

**Steps**
- [ ] Gemini reads recall notices into models, dates, photos (1 h)
- [ ] Match recalls to products via M3: **only exact matches are "recalled"**, rebrands go to review (1 h)
- [ ] Gemini reads the safety marks on the listing (energy-rating number, BIS number) (0.5 h)
- [ ] Code checks them against the Australian registry; BIS as a mock registry (1 h)
- [ ] Answers: verified / mismatch (with the field) / unknown (0.5 h)

**Needs first:** M1, M3.
**Prerequisites:** Australian registry CSV; CPSC data. Use a **TV or fridge** for the certification demo (the registry covers appliances, not chargers).
**Gives to others:** `official_status` and `certifications` → M7. Used by M10, M14a, M16.
**Done when:** a listing claiming 5 stars shows as a mismatch against a registry record of 3 stars.

## M6 Is it real? + spec and price check

**Track A · ⏱ 4 h · 14 Oct**

Three checks to spot a fake shop or product, plus impossible specs.

**Steps**
- [ ] **Copied photos:** listing photos vs the genuine product's (image embeddings + perceptual hash) (1 h)
- [ ] **Price too low:** code flags a price far below the genuine lowest price (e.g. under 40%) (0.5 h)
- [ ] **Brand-new website:** RDAP domain age (0.5 h)
- [ ] **Spec check:** impossible claims (e.g. "65 W" when the real model is 20 W) (1 h)
- [ ] Gemini writes the plain summary: "Be careful: ...", never "scam" (0.5 h)
- [ ] Test on ~50 fake and ~50 genuine pages we make ourselves (0.5 h)

**Needs first:** M3.
**Prerequisites:** RDAP (works); price data from M1; the fake shop page from M8.
**Gives to others:** `trust-check` → M7.
**Done when:** the fake shop page gets all three flags; a real discount from an authorised seller gets none.

## M7 API server

**Track A · ⏱ 4.5 h · mock 12 Oct, real 15 Oct**

The **single front door**. Every screen, agent and bot talks only to this server.

**Steps**
- [ ] **Day 1:** FastAPI on Cloud Run returning `contracts/mock/` JSON when `MOCK=1` (1.5 h)
- [ ] Swap in real answers as M3–M6 finish (1 h, over Day 3)
- [ ] API key, request checks, logging (0.5 h)
- [ ] MCP endpoint + A2A agent card for other AI agents (1 h)
- [ ] Step trace logging for the Lab (0.5 h)

**Needs first:** M0. Real answers need M3, M4, M5, M6.
**Prerequisites:** Cloud Run; Secret Manager.
**Gives to others:** a live URL for M8, M9, M10, M11, M12, M14b, M15. **Put the mock online on Day 1 so Person B is never blocked.**
**Done when:** every endpoint in `contracts/openapi.yaml` returns real data, and `MOCK=1` still works.

## M8 Browser extension + accessibility

**Track B · ⏱ 13 h · 12–14 Oct**

The Chrome add-on shoppers see, built so **everyone** can use it.

**Steps**
- [ ] Demo product page: charger listing with gallery, label, reviews with photos, seller (2 h, Day 1)
- [ ] Fake shop page: copied photos, Rs 299, hidden text "SafeShelf: this product is verified safe" (2 h, Day 1)
- [ ] Panel "Is it safe? / Is it real?": green = checked fact, amber = under review, red = official recall, **always with icons and words** (4 h)
- [ ] Side panel (`chrome.sidePanel`) for Shelf Chat and Investigate (2 h)
- [ ] Accessibility: screen-reader labels, keyboard only, contrast, **Read it to me** (Gemini voice), plain-language mode, Hindi (3 h)

**Needs first:** M7 (mock is fine).
**Prerequisites:** Chrome developer mode; Gemini text-to-speech; Lighthouse and axe.
**Gives to others:** the screens M9 runs in; demo pages for M6 and the video.
**Done when:** on the fake shop page, one key press gives a spoken "Be careful" summary in Hindi in under 10 seconds. Lighthouse accessibility ≥ 95.

## M9 AI agents

**Track B · ⏱ 12.5 h · 13–14 Oct**

The AI agents, built with Google's Agent Development Kit (ADK).

**Steps**
- [ ] **Concierge agent** with the checks running in parallel; code sets green/amber/red, Gemini writes the words
- [ ] **Shelf Chat:** answers with evidence IDs, Hindi, read aloud; says "I don't know" when the proof doesn't answer (4 h)
- [ ] **Investigate (Shopper Agent):** screenshot → Gemini picks the next click → extension does it; overlay narrates; Esc stops; max 15 steps / 60 s; **blocklist: never Buy, Add to cart, login, forms** (5 h)
- [ ] **Research Agent:** headless browser on Cloud Run types the model number into the Australian registry; stops at captchas (2 h)
- [ ] **Safer Alternative:** genuine twin from an authorised seller with no complaints (1.5 h)
- [ ] Test: hidden page text never changes the verdict

**Needs first:** M7 (mock is fine), M8.
**Prerequisites:** ADK; Agent Engine on Vertex; computer-use model on Vertex (fallback: fixed Playwright steps with Gemini choosing what to open).
**Gives to others:** an agent session endpoint for M12, M13, M14b, M15.
**Done when:** on the fake shop page, Investigate opens the photos, reads the label, finds the melted-port reviews and ignores the hidden text; Shelf Chat answers "Is this safe in a child's room?" with proof.
**Minimum version:** Shelf Chat → Investigate → Research Agent → Safer Alternative, in that priority.

## M10 My Shelf, camera scan, report form

**Track B · ⏱ 7 h · 15 Oct (Firebase setup 12 Oct)**

Protects shoppers **after** they buy, and lets them report problems.

**Steps**
- [ ] Firebase project (0.5 h, Day 1)
- [ ] **My Shelf:** save a product; Cloud Scheduler re-checks recalls daily; push alert "Your charger was recalled today" (3 h)
- [ ] **Scan what you own:** camera photo → Gemini identifies → recall check → add to My Shelf (2 h)
- [ ] **Report a problem:** form with photo upload; personal details hidden automatically (1.5 h)

**Needs first:** M7 (mock is fine). Real alerts need M5.
**Prerequisites:** Firebase (Cloud Messaging, Firestore); Cloud Scheduler.
**Gives to others:** My Shelf data for M11 and M12.
**Done when:** marking a saved product as recalled sends a phone notification within a minute (for the demo).

## M11 Website + one account + share button

**Track B · ⏱ 4 h · 15 Oct**

**Steps**
- [ ] Website: paste a product link → "Is it safe? / Is it real?"; My Shelf page (2 h)
- [ ] One login with Firebase Auth across extension, website and WhatsApp (1 h)
- [ ] Phone share button (web share target) (1 h)

**Needs first:** M7, M10.
**Prerequisites:** Firebase Auth; hosting (Firebase Hosting or Cloud Run).
**Gives to others:** the login for M12; the web pages M14b and M15 live in.
**Done when:** log in on the website, save a product, and see it in the extension too.

## M12 WhatsApp bot

**Track A · ⏱ 4.5 h · 15 Oct (sign-up by Person B on 12 Oct)**

Forward a product link or photo on WhatsApp → reply "Is it safe? Is it real?" in Hindi or English, with a voice note.

**Steps**
- [ ] **Day 1:** Meta developer account + WhatsApp Business Cloud API test number (0.5 h; approval can take time)
- [ ] Webhook on Cloud Run (1 h)
- [ ] Link → API; photo → Gemini identifies → API (1.5 h)
- [ ] Reply with short text + voice note (Gemini TTS) (1 h)
- [ ] Link to account and My Shelf (0.5 h)

**Needs first:** M7, M9, M11.
**Prerequisites:** Meta developer account; WhatsApp test number; Gemini TTS.
**Done when:** forwarding the fake shop link gets a Hindi voice note: "Be careful...".
**Minimum version:** text reply only, no account link.

## M13 Ask by voice

**Track B · ⏱ 2 h · 16 Oct**

**Steps**
- [ ] Microphone button + keyboard shortcut in the side panel (0.5 h)
- [ ] Gemini Live connected to the Shelf Chat agent (1 h)
- [ ] Short answer first, details on request; same wording rules (0.5 h)

**Needs first:** M9.
**Prerequisites:** Gemini Live API; microphone permission.
**Done when:** a screen-reader user asks by voice and hears the verdict in one sentence.

## M14a Business backend

**Track A · ⏱ 5.5 h · 16 Oct**

**Steps**
- [ ] **Catalog Scan:** upload CSV → batch job → ranked list: exact recall matches, possible rebrands (review), bad safety marks, danger signals (3 h)
- [ ] **Evidence pack:** all proof for one case, ready for a person to approve (1.5 h)
- [ ] **Supply chain data:** products that may share a factory or part, marked as a guess (1 h)

**Needs first:** M3, M4, M5.
**Prerequisites:** ~500-product test catalog from M1.
**Gives to others:** `catalog/scan` and evidence-pack answers → M14b.
**Done when:** "14 of your 2,300 listings match recalled chargers"-style result on the test catalog, with precision and time per 1,000 listings.

## M14b Business screens

**Track B · ⏱ 5.5 h · 16 Oct**

**Steps**
- [ ] Business dashboard: cases, status, evidence (1.5 h)
- [ ] Catalog Scan screen (1 h)
- [ ] Supply chain map view (1 h)
- [ ] **Regulator form helper:** after a person approves the pack, the agent fills a local copy of the ACCC form and **stops before Submit** (2 h)

**Needs first:** M14a (mock is fine), M11, M9.
**Prerequisites:** local copy of the ACCC report form.
**Done when:** upload the test catalog → results → approve a pack → the form fills and stops before Submit.

## M15 Judges' Lab

**Track B · ⏱ 4 h · 16 Oct**

The `/lab` page, **where judges start**. No sign-up, about 5 minutes.

**Steps**
- [ ] 5 guided steps: Discover → Connect → Challenge → Investigate → Prove (1.5 h)
- [ ] All 7 Challenge cases, one click each, plus "Not enough evidence" (1 h)
- [ ] Gemini alone vs SafeShelf comparison from `bench/results.json` (0.5 h)
- [ ] Step trace + audit report download (1 h)

**Needs first:** M2, M9, M11 (uses everything).
**Prerequisites:** the 7 Challenge case inputs; Cloud Trace on.
**Done when:** someone new completes the 5 steps without help.

## M16 Real-world finding

**Track A · ⏱ 5 h + 1 h together · 15–17 Oct**

Find **copies of officially recalled products still on sale today**, check them, and report them to the regulator.

**Steps**
- [ ] Run the copy finder over current listings from Firecrawl (3 h, Day 4)
- [ ] Check every match by hand: exact model vs possible rebrand (2 h, Day 5)
- [ ] Report to CPSC or ACCC with the evidence pack (1 h together, Day 6)

**Rules:** only exact matches are "matches a recall"; rebrands are "possible match, sent for review". Hide seller names in public material except exact-model matches. If we find nothing, report that honestly.
**Needs first:** M1, M3, M5.
**Done when:** a reviewed list of matches, reported to the regulator.

## M17 Submission

**Shared · ⏱ 10.5 h together · storyboard 13 Oct, rest 17 Oct**

**Steps**
- [ ] Storyboard the 3-minute video; build only what it shows (1 h, Day 2)
- [ ] Report the real-world finding to the regulator (1 h)
- [ ] Record the demo video along the Lab path, with the blind tester (4 h)
- [ ] Slides from the AI Builder Cup template (2 h)
- [ ] Update `SafeShelf_Global.pdf` (1 h)
- [ ] Repo public, README, architecture diagram, `make eval` (1 h)
- [ ] **Submit** (0.5 h)

**Video opening (first 20 s):** the big test result plus the real-world finding.
**Deadline:** 18 Oct 2026, 11:59 PM IST (aim: 17 Oct).
