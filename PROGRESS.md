# Progress log: Team Hashes

Everything done so far, newest at the bottom. Submission deadline: **18 Oct 2026, 11:59 PM IST** (we aim for 17 Oct).

## Status on 12 Oct 2026

| Area | Status |
|---|---|
| Product and technical design ([SAFESHELF.md](SAFESHELF.md) v1.1) | ✅ Done |
| Tools, rules, competitors, backtest plan | ✅ Done ([TOOLS.md](TOOLS.md), [HACKATHON.md](HACKATHON.md), [COMPETITOR_ENTRIES.md](COMPETITOR_ENTRIES.md), [BACKTEST.md](BACKTEST.md)) |
| Feasibility test (small backtest) | ✅ Done, mixed result (below) |
| Full backtest (25+ recalls) | ❌ Not started; needs Colab or a GCP VM |
| Vertex model check (Gemini 3.x, computer use) | ❌ Not done; `gcloud` isn't installed on Solomon's laptop |
| Code (backend, extension, agents, Lab) | ❌ Not started |
| PDF ([SafeShelf_Global.pdf](SafeShelf_Global.pdf)) | ⚠️ Out of date: doesn't include the agent layer or v1.1 |
| Deck, demo video | ❌ Not started (planned for 17 Oct) |

## 1. Design work (12 Oct)

### 1.1 Agent layer (commit `ce0d12c`)
Made SafeShelf agentic, using Google's Agent Development Kit (ADK):
- **Shopper Agent:** in the shopper's own tab, a Gemini computer-use model looks at screenshots and clicks through the listing: gallery, label zoom, 1-star reviews with photos, seller, specs.
- **Research Agent:** a headless browser on Cloud Run checks registries and recall sites that have no API. It stops at captchas.
- **Shelf Chat:** a chat in the extension side panel that answers with evidence IDs, in Hindi, and aloud.
- **Safer Alternative Finder**, **My Shelf** (recall alerts after purchase), **Scan what you own** (phone camera), **regulator form agent** (pre-fills the form and stops before Submit).
- **ADK structure:** a Concierge agent → a sequential pipeline with the five checks running in parallel → a verdict set by code. Also offered over MCP and A2A for other AI agents.
- **Safety rules:** read-only, code checks every click against a blocklist, page text can't change the verdict (prompt-injection defence), at most 15 steps.
- **Computer-use models** listed by Google: `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-3-flash-preview`. **Whether they're on Vertex is still to be confirmed.**

### 1.2 Score estimate
- Fully built: about **4.55 / 5**. Realistic: **4.0–4.3**. Today, with no code: about 1.
- The biggest factor is the backtest result (±0.4).

### 1.3 Top-5 plan (commit `925eeb6`)
Five things that set us apart:
1. **A real-world finding:** find twins of officially recalled products still on sale, and report them to the regulator.
2. **The backtest as the headline.**
3. **Cut scope:** one hero flow, built deep.
4. **Marketplace Catalog Scan** (module 19): the business side of the theme.
5. **Real people:** 3–5 user conversations, and a blind tester on video.

Plus: team split (Seshu: data, backtest, engine, API; Solomon: extension, agents, UI, video), video storyboard on 13 Oct, feature freeze on the evening of 16 Oct. Realistic ceiling: 4.7–4.8.

### 1.4 Version 1.1 (commit `925eeb6`)
Added sections 23A–23G to SAFESHELF.md:
- **SafeShelf Lab** (`/lab`, the judges' entry point, a 5-step guided path),
- **Challenge SafeShelf** (7 hard cases, plus a "not enough evidence" answer),
- **SafeShelfBench** (keyword rules vs Gemini alone vs SafeShelf, `make bench`),
- **original algorithms** (counterfactual matching, active evidence acquisition, evidence-change notes),
- **transparency** (traces, audit report export),
- **WhatsApp and shared account** (after submission),
- **real-world validation.**

## 2. Feasibility test (12 Oct)

**Question:** do hazard reviews appear on Amazon before official CPSC recalls?
**Scripts:** [feasibility/](feasibility/) (`run.sh`, `analyse.py`, `targets.json`).

### 2.1 Data checks

| Check | Result |
|---|---|
| CPSC Recalls API | ✅ Works. 1,333 recalls in 2019–2023; 421 mention Amazon; 161 of those are fire, burn or shock; **about 60 are electrical and dated before Aug 2023** (the dataset ends around Sep 2023). Enough for 25+ |
| Amazon Reviews 2023 | ✅ / ⚠️ No search API (the Hugging Face viewer is disabled). Files are 9–31 GB per category. Streaming 9.3 GB took **12.5 minutes** on Solomon's laptop. **Run the full backtest on Colab or a GCP VM, or in BigQuery** |
| Finding recalled products | ✅ / ⚠️ VRURC and myCharge are in Cell Phones & Accessories. The Anker 535 (A1366) isn't, so it's probably under Electronics. One brand has dozens of listings, so matching needs the twin engine plus a manual check |
| Australian energy-rating registry | ✅ / ⚠️ Works (e.g. TVs: 5,017 models with brand, model, stars, registration number). **But it covers appliances only (TVs, fridges, air conditioners, washers, monitors), not chargers.** The certification demo has to use an appliance |
| RDAP (domain age) | ✅ Works |
| Vertex AI models | ❓ Not checked |

### 2.2 Early-warning result
Rule: flag when there are 3 reviews containing hazard keywords within 90 days.

| Product | Recalled? | Reviews before recall | Hazard reviews | Result |
|---|---|---|---|---|
| VRURC OD-B7 wall-plug charger | Yes, 6 Jul 2023 | 147 | 4 (2 with photos) | ✅ Real warnings before the recall: "Overheats when charging" (17 Mar) and **"Melted on the first day", with a photo (26 Apr)**, about **10 weeks early** |
| myCharge Adventure family | Yes, 27 Oct 2021 | 157 | 0 | ❌ Missed (or the wrong listings were matched) |
| Anker 325 PowerCore Essential 20K | No (control) | 2,623 | 31 | ❌ False alarm. The keywords matched happy reviews ("without overheat", "fire season") |
| VRURC 10000 mAh LED power bank | No (control) | 510 | 7 (2 with photos) | ⚠️ Real danger reviews ("SWOLLEN BATTERY", "Fire hazard") but never recalled. **A possible missed hazard**, a candidate for the real-world finding |

### 2.3 What we learned
1. **The signal exists but is thin:** a few reviews out of hundreds. Caught in 1 of 2 recalls.
2. **Keyword matching doesn't work.** Gemini has to read each review (real hazard? own experience? does the photo show damage?). This is also a strong SafeShelfBench comparison.
3. **Use rates, not counts.** Popular products collect more scary reviews just from volume.
4. **Some "false alarms" may be real hazards that were never recalled.** The precision measurement needs a human check, and these cases feed the real-world finding.
5. **Not a pass yet.** Two recalls is too few. Don't claim "N weeks early" until the full run is done.

### 2.4 Changes needed in the plan
- The certification step of the hero flow should use **an appliance (TV or fridge)** against the Australian registry, not the charger. Or use a BIS mock connector for the charger.
- Run the backtest on **Colab or a GCP VM**, over several categories (Cell Phones, Electronics, Home & Kitchen, Tools).
- Add **Gemini review classification** and **rate normalisation** to the alarm rule.

## 2.5 Decision: Firecrawl for data collection only (12 Oct)
- 21,119 Firecrawl credits are available but expire on 21 Oct 2026.
- Use them **only to collect data**, finishing the main collection by 14 Oct (top-ups until 20 Oct): current listings for the real-world finding, ACCC/OECD recalls, identity pairs, "Is it real?" reference data, a seeded catalog, and frozen test snapshots. Budget about 7,250 credits ([TOOLS.md](TOOLS.md)).
- **Not** used live in the Lab, extension or agents. Everything is saved to Cloud Storage and Cloud SQL.

## 3. Next steps
1. **Today:** someone with GCP access checks the Gemini 3.x and computer-use model IDs on Vertex.
2. **Full backtest on Colab:** 25+ recalls, Gemini review classification, rate-based alarm rule, never-recalled controls, twin pooling.
3. **Firecrawl data collection, by 14 Oct** (budget in TOOLS.md).
4. Book 3–5 user conversations. Find a real charger-fire news story from India.
5. **13 Oct:** storyboard the video, then follow the build plan (SAFESHELF.md section 25).
6. Regenerate the PDF before submission.
