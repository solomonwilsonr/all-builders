# Progress log: Team Hashes

Everything done so far, newest at the bottom. Submission deadline: **18 Oct 2026, 11:59 PM IST** (we aim for 17 Oct).

## Status on 13 Oct 2026 (evening)

| Area | Status |
|---|---|
| Product and technical design ([SAFESHELF.md](SAFESHELF.md) v1.1) | ✅ Done |
| Tools, rules, competitors, backtest plan | ✅ Done ([TOOLS.md](TOOLS.md), [HACKATHON.md](HACKATHON.md), [COMPETITOR_ENTRIES.md](COMPETITOR_ENTRIES.md), [BACKTEST.md](BACKTEST.md)) |
| Google Cloud (Vertex AI, Cloud Run, Cloud SQL, bucket, Secret Manager) | ✅ Done (section 4.1) |
| Full backtest (25 recalls, 40 controls) | ✅ First result (section 4.4): SafeShelf 6/25 early, 5% false alarms |
| Person A engine: M3 copies, M4 Safety Radar, M5 recalls + safety marks, M6 "Is it real?" | ✅ Built and live on Cloud Run (section 4.2) |
| Real catalog: 27,492 Amazon + 286 Amazon.in/Flipkart products, 29,379 real reviews | ✅ Loaded locally and in Cloud SQL (section 4.5) |
| Live API on real data ([/docs](https://safeshelf-api-368488022657.asia-south1.run.app/docs)) | ✅ identify, duplicates, relationships, safety, certifications, trust-check |
| Person B (extension, agents, website, Lab) | ⏳ Teammate's track; real API ready for them |
| Real-world finding (M16) | ⏳ Candidates found (section 4.6), hand check on Day 5 |
| PDF ([SafeShelf_Global.pdf](SafeShelf_Global.pdf)) | ⚠️ Out of date |
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

## 3. Next steps (written 12 Oct; all done on 12–13 Oct, see section 4)
1. **Today:** someone with GCP access checks the Gemini 3.x and computer-use model IDs on Vertex.
2. **Full backtest on Colab:** 25+ recalls, Gemini review classification, rate-based alarm rule, never-recalled controls, twin pooling.
3. **Firecrawl data collection, by 14 Oct** (budget in TOOLS.md).
4. Book 3–5 user conversations. Find a real charger-fire news story from India.
5. **13 Oct:** storyboard the video, then follow the build plan (SAFESHELF.md section 25).
6. Regenerate the PDF before submission.

## 4. Build: Person A track (12–13 Oct)

All code is on the `person-1` branch. Tests: 38 engine + 19 API, all passing.

### 4.1 Google Cloud
- Project `project-03d8d835-d5c5-4ad4-bf8` (free-trial account). Vertex AI on; **Gemini 3.x only answers on location `global`**.
- Working models: `gemini-3.5-flash`, `gemini-3-flash-preview` (best for bulk jobs), `gemini-3.5-flash-lite`, `gemini-3.1-pro-preview`, `gemini-embedding-001`; computer use works on `gemini-3.8-flash`, `3.5-flash-lite`, `3-flash-preview`. `gemini-3.8-flash` took up to 244 s per call, so it is not used for the engine.
- **API on Cloud Run:** https://safeshelf-api-368488022657.asia-south1.run.app (`/docs` shows the contract with examples). Real engine on Cloud SQL; endpoints without an engine yet still return their example answers.
- **Cloud SQL** `safeshelf-db` (Postgres 16 + pgvector, smallest tier). Password only in Secret Manager. Connect locally with `cloud-sql-proxy --port 5443 ...`.
- **Bucket** `gs://safeshelf-data-03d8d835`: raw data, review files, catalog files.
- Throwaway VMs streamed the Amazon Reviews 2023 files (metadata scan, review scan, catalog scan) and were deleted afterwards.

### 4.2 Engine modules (`engine/`)
| Module | What it does | "Done when" |
|---|---|---|
| M3 Find copies (`identity.py`, `rules.py`) | Fingerprints, brand-blind look-alike search (pgvector), Gemini compares pairs, **code** decides the 5 classes | ✅ Demo charger: exact copy, rebrand for review, look-alike. Real: Nexzvolt 65 W → Avaxon rebrand for review |
| M4 Safety Radar (`radar.py`, `safety.py`) | Gemini reads reviews (own experience vs hearsay, joke, negation) and photos; code dedupes, rates, sets the verdict | ✅ 20/20 hand-labelled reviews; "melted on the first day" flagged, "this charger is fire" not |
| M5 Recalls + safety marks (`recalls.py`, `marks.py`) | Only an exact model number = recalled; family-only notices go to review. Marks checked against the Australian registry and a BIS mock | ✅ Demo TV claims 5 stars, registry 3 → mismatch |
| M6 Is it real? (`trust.py`) | Copied photos, impossible price, new website (RDAP), spec conflicts, hidden AI instructions; "Be careful", never "scam" | ✅ Fake shop gets all flags; real discount gets none |

### 4.3 Data collected
- CPSC recalls 2019–2026 (2,537) and the Australian energy-rating registry (8,470 TVs and fridges), local and in Cloud SQL.
- Amazon Reviews 2023: 9,598 listings from 47 recalled brands → **25 recalls matched to 289 listings that sold the recalled product**, plus 40 never-recalled same-brand controls, and their 57,431 reviews dated before the recalls.
- Firecrawl (about 510 of 21,119 credits used): 53 searches for recalled products still on sale, 20 catalog searches and 324 product pages from Amazon.in and Flipkart (product pages only, no review scraping).

### 4.4 Backtest result (`make bench`, `bench/results.json`)
| Method | Recalls flagged early | False alarms on controls |
|---|---|---|
| Keyword rules | 11/25 | 11/40 (28%) |
| Gemini alone | 6/25 | 6/40 (15%) |
| **SafeShelf** | **6/25** | **2/40 (5%)** |
| SafeShelf without twin pooling | 1/25 | 2/40 |
- **Honest headline:** SafeShelf catches as many recalls early as Gemini alone with a third of the false alarms, and twin pooling is what makes it work (6 vs 1).
- Test half only (settings tuned on the other half): 2/9 flagged, 0/14 false alarms.
- Many recalls had almost no reviews before the recall date; no method can catch those.
- Flags came early, e.g. Aduro surge protectors, Ancheer e-bikes, Bedsure blankets, Pearl River propane hoses: first clear warning more than a year before the recall. Quote examples, not the median (90+ weeks, inflated by long-running listings).
- Fix found on the way: the CPSC filter missed plural titles ("Portable Chargers"), which dropped the VRURC recall.

### 4.5 Real products (13 Oct)
- `data/load_catalog.py` loads 27,492 everyday Amazon products (chargers, power banks, heaters, cords, TVs, heated blankets), the recalled listings linked to their recalls, and 286 Indian listings; plus 29,379 real reviews with Safety Radar labels.
- Live results: **VRURC charger** (recalled July 2023) → amber, 2 fire reports and a photo Gemini confirmed shows melting; a fake **boAt** power-bank copy on an unknown site → price flag against the real Flipkart price.
- First safety check of a product takes ~1–1.5 min (photo checks); after that ~0.3 s. Warm up the demo products before recording.

### 4.6 Real-world finding candidates
- **Sunbeam heated blanket (B0BSKMH9GX, never recalled):** 74 own-experience fire/burn reports (3 with damage confirmed in photos) and 13 shock reports in 7,430 reviews. Strongest candidate; check by hand on Day 5 and report to the regulator.
- Recalled products still listed today (Firecrawl): e.g. the recalled AmazonBasics ceramic heater on amazon.com.

### 4.7 After the verdict: owners and reviewers (15 Oct)
- **Already bought it?** `GET /v1/products/{id}/owner-guidance` (`engine/owner.py`): numbered steps for someone who owns the product. Stop and get the remedy (recall), check yours for the reported problem (top 3 hazards), return it, report it, save to My Shelf, safer options. Only code rules on the safety answer, no new Gemini text; each step links its evidence IDs. Sunbeam blanket: amber, 7 steps, ~20 s the first time (safer options), then fast.
- **Case file:** `GET /v1/products/{id}/case-file` (`engine/case_file.py`): one exportable record built from the regulator evidence pack: verdict plus the code rule that set it ("Gemini read the reviews; it did not set the verdict"), findings with exact quotes and evidence IDs, recalls, same-hardware listings, where to file it, and `review_gate` (awaiting human review, never sent). Also returned as a printable Markdown copy.
- **Lab opens on a real product:** the explorer is pre-filled with the Sunbeam blanket, so a judge presses one button, with no setup or sign-in. New buttons: "Already bought it?", "Case file", "Download case file".
- Both endpoints are also MCP tools (`owner_guidance`, `case_file`) and in `make warm`.
- **Sunbeam check:** CPSC recall 23157 covers Sunbeam **Queen** blankets, model **32810027** (sold Sep 2022–Jan 2023 via Star Elite). Ours is the **Twin** Royal Ultra, model BSF9GTS-R595-13A00, so it is **not** that recall. The notice gives the model number only in a photo caption, so the recall check had marked it "possible match, under review". Fixed: `recalls.notice_models` now also reads model numbers from photo captions (added to what Gemini reads in the description, never instead of it). The stale link row was removed from the local database; **Cloud SQL still has it** (one row: `cpsc:23157` / `SS-P-AMZ-B0BSKMH9GX`, `needs_review`). Still hand-check the label photo on Day 5.

## 5. Next steps (from 13 Oct)
1. **Teammate:** switch the extension to the live API; send the demo page photos and the fake shop URL (`example-deals-store.test`).
2. **Agree with the teammate:** an optional `reviews` field so the extension can send the reviews on the page for a live Radar check.
3. **Day 4 (15 Oct):** MCP access for other AI agents, WhatsApp bot (M12), real-world finding search (M16), product history endpoint.
4. **Day 5 (16 Oct):** Catalog Scan backend (M14a), hand-check the Sunbeam candidate, final `make bench`.
5. Still open on Person A's track: M3 image embeddings; warm-up script for the demo products.
6. Regenerate the PDF before submission.
