# SafeShelf checklist

**Last updated:** 16 Oct 2026, night (Day 5 of 6) · **Score: 76/100** → 94 if the plan lands ([score](#-score-out-of-100))
**Deadline:** 18 Oct 2026, 11:59 PM IST · **Feature freeze:** evening of 16 Oct (after that, only fixes, data, measurements and the story)

Updated with every change. For the details behind each line, see [plan.md](plan.md).

**Contents:** [Must do](#-must-do-added-16-oct-after-the-ninth-competitor-scan) · [Plan](#-plan-work-through-in-order) · [Score](#-score-out-of-100) · [By region](#-by-region) · [Built, waiting for deploy](#-built-waiting-for-deploy) · [Done](#-done) · [Risks](#%EF%B8%8F-risks-and-heads-ups)

## In one line
The engine, agents and data are built. Judges can't see the latest work until it's deployed, and all our measured proof is from US data while the pitch is JAPAC. The plan fixes both: **deploy, then measure SafeShelf on JAPAC and Indian data, then tell that story.**

---

## 🚨 Must do (added 16 Oct, after the ninth competitor scan)
From where we stand against ≈267 public entries ([COMPETITOR_ENTRIES.md](COMPETITOR_ENTRIES.md)). What's missing is proof, focus and staying up, not features. Anything not deployed and in the video by the 18th earns nothing.

**Tonight, 16 Oct**
- [ ] **A. Keep the demo alive through judging (shortlist 7 Nov)** · Solomon · 20 min. The hackathon credit expires ~24 Oct. Check which billing account Cloud Run, Cloud SQL and Firebase use; move anything on the hackathon credit to the free trial (until Jan 2027). Set Cloud Run min instances to 1 on the API. The judges' page demo cases answer from the stored copy when a live source is down. Upload a backup video of the full flow in case Amazon.in stalls (item 8)
- [ ] **B. Judges' web page live** (= item 5): the single biggest gap; judges won't install the extension

**17 Oct morning: proof**
- [ ] **C. One checked real-world finding** (= items 12 and 13) · Solomon · 30 min. Open the 7 links in [bench/fixtures/india/still_on_sale.md](bench/fixtures/india/still_on_sale.md) and the 3 exact-model US leads. One confirmed row gives the deck "A product India ordered recalled is still for sale on ___". Claim only what a person confirmed
- [ ] **D. JAPAC identity accuracy** · Seshu · 30 min. Label the 16 pairs from `bench/label_pairs.py`, then `make bench-identity`. Gives a measured number not based on US data (SKUdesk and LedgerLens both show precision)
- [ ] **E. "Recalled abroad, still sold here" count** · Claude · 2 h, after item 10. Match the 41 cross-border models against Indian (and Australian) listings: "N models recalled abroad, still sold here, X listings". The impact number of our own that problem fit is missing

**17 Oct afternoon: story**
- [ ] **F. Regulator report** · Claude · 1–2 h. A weekly report for CCPA, ACCC or CAA: products recalled in another country but still sold locally, with evidence, built from the cross-border scan and case files. Sample PDF + one slide. Moves the story from "protects one shopper" to safety infrastructure
- [ ] **G. Who pays** · one deck slide. Marketplaces (check listings when sellers upload, avoid BIS raids), insurers and payment providers (risk flag on purchases), regulators (report F). The tenant keys, webhooks and usage metering are already built. SLA-backed recall-check API for marketplaces (uptime commitment + support), priced like any other trust-and-safety API — not a new build, just how item 5's API is sold
- [ ] **H. One person, one product, one moment** in the deck and video (items 15 and 16): an Indian parent buying a power bank on Amazon.in gets the Hindi WhatsApp answer. Everything else goes on one "under the hood" slide
- [x] **I. Ideas borrowed from the top 10, all built 16 Oct night** (commits 80f3050 to 0a569df; tests: engine 232, contract 60, extension 7/7, WhatsApp 11; checked in a real browser against the local API). **Needs `make migrate` (009 `incident_reports`) and `make deploy-api`, then `make deploy-web` and an extension reload (2.10.0).** Slide text and video beats: [docs/deck-additions.md](docs/deck-additions.md)
  - [x] **Voice mode, 26 JAPAC languages** (`POST /v1/voice/verdict`, `engine/voice.py`): a short spoken verdict written by code (`plain.say`), translated by Gemini (marked as machine translation, polite form, English if it fails). Extension: Read aloud + "Speak every answer"; web: Listen on every answer; WhatsApp voice note now says the short line
  - [x] **Before and after purchase** (`POST /v1/after-purchase`, `engine/after_purchase.py`, `engine/complaints.py`): the extension **steps in when you click Buy now / Add to cart** on a red or amber answer (why, Listen, "Buy anyway"); **"I already bought it"**: steps, a refund request to the marketplace and a complaint to the regulator, already filled in with the official record (India NCH 1915, ACCC, CAA + 188 with Japanese drafts, CPSO, 1372, CPSC), plus a case file. Written by code, never sent by SafeShelf
  - [x] **"Checked by code, not guessed" badge** on every "Where we checked" line, linked to the official record or list (extension, web)
  - [x] **Ask out loud with Gemini Live** (WebSocket `/v1/live`, `engine/live.py`, `gemini-3.8-live` in us-central1): camera + voice; Live must call SafeShelf's tools (label read + investigation), code sets the result. Measured: Hindi spoken answer in 13 s through the API. Photo + spoken-question fallback `POST /v1/camera/ask`. Judges' page tab "Ask out loud", large text, made for visually impaired and low-literacy shoppers
  - [x] **Attacker vs defender** (`GET /v1/redteam/rounds`, `POST /v1/redteam/round`, judges' page tab): 18 saved rounds replayed; live rounds where Gemini invents the attack. **It found two real holes, fixed the same night:** reposts with a few words changed counted as separate owners (word-alignment rule; bench still 18/18), and fake-shop notices "for AI shopping assistants" got past the filter (sentence rule: 13/13 attacks caught, 0 false alarms on 27,822 real listings, 10/10 fresh rounds held). Limits stated on the panel
  - [x] **Shopper incident reports** (`POST /v1/incidents`, `GET /v1/incidents/signals`, migration 009): Gemini checks the photo and report; code counts independent reports and raises an early warning (never a recall) by the review rule. On the judges' page under "I already bought it"
  - [x] **Retailer side**: Catalog Scan findings now say what a shop should do with each item (stop selling, quarantine, notify buyers…)
  - [x] **Fix found on the way**: the camera label check returned the AI model's name ("gemini-3-flash-preview") as the product's model number, because `gemini.structured()` overwrites a schema field called "model". Label photos now read the real model (ANKER A1263)
  - [ ] **Open (policy call for Solomon):** a forged regulator page can't make a product "recalled", but it still makes it amber "possible match, a person must check". Should an unofficial domain count at all?

**"What's next" slide:** none of the above is "next" any more. Migrants and cross-border families are named on the "who it's for" slide text
---

## 🧩 New trust-check criteria (added 16 Oct night, Solomon's list) — ⚠️ conflicts with the feature freeze
**Heads-up:** feature freeze was called for the evening of 16 Oct ("Overbuilding loses", see [Risks](#%EF%B8%8F-risks-and-heads-ups)) and the Must-do/Plan sections above already carry the scored path to 94. These 8 are genuinely new scope on top of that — none are in the Plan's point path. Listed here so they aren't lost, not sequenced into tonight's work. All 8 extend `engine/trust.py` (M6, Person A's module); none touch the recall track (`engine/safety.py`, `engine/recalls.py`).
- [ ] **Seller/partner context (#2, #6, #7 — official seller, third-party/fraud flag, recently-created seller)**: build out `MODULES.md`'s existing **P2-1 "Seller and partner context for trust-check"** design — replace `data/authorised_sellers.json` (today only Samsung + Xiaomi) with a brand-partner registry, add `relationship: official_brand | authorised_partner | marketplace_third_party | unknown`, seller account tenure ("recently created seller"), and a fraud-report lookup (no data source for this exists yet — needs one). Keep the existing rule: third-party alone never flags; only flag when not-authorised **and** another check also flags. Est. ~5h engine + ~5.5h extension (MODULES.md's own estimate)
- [ ] **Price/spec sanity check (#4)**: general "is this price plausible for this spec" heuristic independent of having a matched genuine reference (today's `spec_check`/`mrp_check`/`price_check` in `trust.py` only compare against a known-genuine fingerprint). Needs a market-price-for-spec data source. Also: flag pseudo-scientific claims ("electricity saving gadget") — no existing detector
- [ ] **Review-based reliability signals (#3)**: extract "stopped working after N days" / build-quality complaints from reviews. Must stay a separate "reliability note," not folded into Safety Radar's hazard verdict in `engine/radar.py` — that module deliberately excludes quality complaints from the fire/shock/choking/chemical/injury verdict by design, to avoid false "unsafe" alarms
- [ ] **Out-of-scope fallback (#8)**: detect when a checked product is outside SafeShelf's focus categories and fall back to showing only review-based signals (rating, purchase count) instead of a full trust-check. No scope-detection path exists yet; `trust_check()` always runs the full check set today
- [ ] **Recall check (#1)** and **untrustworthy-website flag (#5)**: already fully built, no new work — `engine/recalls.py`/`recall_catalog.py`/`crossborder.py` and `trust.py:145` `website_check`

---

## 🧭 Implementation plan v2.2 (decided 16 Oct: build all of it)
Solomon chose to build the whole v2.2 plan (live official sources + evidence verification) instead of freezing tonight. Each line ticks when it is built and tested; it reaches judges with `make migrate` on Cloud SQL and `make deploy-api`.
- [x] **Live official sources** (`engine/sources/`): CPSC API, OECD GlobalRecalls (Australia, Japan, Korea, Singapore, Taiwan, ASEAN) and **Japan's CAA recall site live** (reuse allowed under PDL 1.0; Japanese text and 型番 model numbers kept as published), India's CCPA/BIS notices from the stored copy. ACCC, METI and Singapore's CPSO refuse automated requests; NITE and the SAFETY Mark registry have no verified access; BIS has no automation API. Each shows as "couldn't be checked" or "not supported", never as clear. Registry in `data/source_registry_japac.yaml`; caching, rate limits, circuit breakers, health
- [x] **Evidence verification** (`engine/evidence_verification/`): is the source official and does its text say it; does the notice cover this exact model, variant and batch, in this country; copies count once; retractions and "not affected" notices downgrade. Five results set by code: confirmed recall (local, exact, in scope) · substantiated hazard · potential concern (incl. "recalled abroad, same model") · no matching notice (not proof of safety) · not enough evidence. Plus a per-country coverage list and "what would change this". 41 tests incl. forged regulator address, lookalike model, excluded batch, copied complaints, injected instructions
- [x] **Database migrations 001–008** (additive only) and `data/migrate.py`: applied to the local database. Cloud SQL: Solomon runs `make migrate` through the proxy
- [ ] Investigation pipeline, safety answer and case file use the new results
- [ ] New API endpoints: investigations, source health, recheck, watchlists, identity feedback, reviews, webhooks, developer usage, bench runs
- [ ] Identity review and negative edges · hazard trends and evidence integrity · cause hypotheses · cross-border matching · supply chain · product timeline · certification checks
- [ ] Camera label check · post-purchase rechecks and alerts · case workflow with human review
- [x] **Benchmarks** (each run saved with its versions in `bench/runs/`, served at `GET /v1/bench/runs`): **evidence red-team** 18/18 invented hard cases come out as designed (no unsupported confirmations, no lookalike propagation, copied complaints don't add up; these test the rules, not real-world accuracy) · **historical cutoff check**: all 25 backtest recalls use their first public date, none flagged · **cross-border**: 19 pairs, median lead 22 days (95% CI 13–68, n=17, small sample) · **JAPAC gate, live**: India, Australia, Japan and Singapore products each scoped correctly, one foreign-to-local match, one rejected lookalike, all 5 as expected. **Live vs stored copy:** the stored copy alone misses the Japanese HAIARA W5PRO recall (CAA, Oct 2026, newer than the stored data); only the live check finds it · **identity**: no human labels yet, 16 candidate pairs written for labelling (`bench/label_pairs.py`) · **prospective log**: 19 predictions, hash chain intact · `coverage_by_country.json`, `recall_by_country.json`, `identity_by_country.json`. Make targets: `bench-evidence`, `bench-historical`, `bench-crossborder`, `bench-japac`, `bench-identity`, `eval-prospective`, `bench-all`
- [x] **Screens**: the extension's check card asks the live investigation and shows the code's result with its official record, "What was checked" country by country (live, stored copy, couldn't be checked, not checked), the official record links and what would change the answer; "Investigate the page" adds what would change it; the judges' web page shows the same table; WhatsApp says "RECALLED IN ANOTHER COUNTRY" (English and Hindi) instead of "RECALLED" and lists what was checked. My Shelf saves can go to the new watchlists (rechecks and alerts): turn on `SHELF_SYNC` in `extension/config.js` after `make deploy-api`. Tests: extension 6/6 (incl. "a US recall on an Amazon.in listing is amber, not red"), WhatsApp 11/11
- [x] **Trace and analytics**: `GET /v1/investigations/{id}/trace` now carries the evidence trail (sources and their states, grouped reports, contradictions, policy version, review and case history); `make export-bigquery` writes assessments, coverage, fetches, claims and predictions for BigQuery (`BQ_DATASET=...` loads them). Deep checks run as durable jobs inside the API, not Cloud Tasks
- [x] **Docs**: [docs/source-access.md](docs/source-access.md) (every source: access, terms, status, what happens when it's down) and [docs/privacy-regional.md](docs/privacy-regional.md) (India DPDP, Japan APPI, Singapore PDPA, Australia Privacy Act; open items for production)
- [x] **Fixes from Solomon's live extension tests (16 Oct)**: model numbers with a space (V-Guard "VSDI 100"); model numbers in Amazon's collapsed "Item details" tab (Anker A1229); the brand name no longer counts as the product type (an Anker power bank had matched Anker scooter and cooler recalls); codes in notice titles are read (A1642); a brand with recalls but no model number read says "model number needed" instead of "no matching notice"; the US shows in the "Checked" line. Needs `make deploy-api` and an extension reload
- [x] **Plain-language answers (16 Oct, Solomon's request)**: every answer now leads with a title, one sentence why, and "What you can do", plus "Where we checked" by country in simple words (engine/plain.py), e.g. "Recalled in the US. The safety regulator in the US recalled this NEWDERY ZHX-PB22 because of a fire risk. It hasn't been recalled in India yet…". Extension 2.9.0 card: plain answer on top, seller check in plain sentences, technical detail behind "Show details"; same on the web page and WhatsApp. Needs `make deploy-api` and an extension reload
- [x] **Better agents (16 Oct, Solomon's request)**: (1) **identity agent**: when code finds no model number, Gemini reads the listing and quotes where it found each value; only quotes on the page count (read "HD 9252/90", "Stone 350"); (2) **recall critic**: a second Gemini look at possible matches, quoting both texts; a grounded "different product" sets the match aside, "same" is only a note, never a recall (Anker PowerCore Slim A1229 → "No recalls found"; A1263011 still "Recalled in the US"); (3) **browser-use** (open-source browser agent) with Gemini searches EU Safety Gate and NZ on deep checks, limited to official domains (found real EU alerts with model numbers in ~2 min); (4) **Cloud Trace** for every agent, tool, model and source call (`TRACE_TO_CLOUD=1`, APIs on); (5) **agent test set** gains 4 cases (recall abroad stays amber, Japan red, identity agent, critic). Needs `make deploy-api` and `make deploy-research`
- **To make it visible (Solomon):** `make migrate` on Cloud SQL through the proxy (adds tables, syncs the source registry) → reload CPSC once with descriptions → `make deploy-api` → `make bench-japac` against the live API to confirm Cloud Run can reach CAA, CPSC and OECD → optional: `gcloud secrets create webhook-key`, `make schedule-watch-recheck`, `SHELF_SYNC = true` and reload the extension
- **Needs people, not code:** hand-checked identity pairs (gold set), a second annotator, the SaferProducts.gov key, and checking access for Japan's NITE and Singapore's CPSO

Live check on 16 Oct (no reviews): HAIARA W5PRO on a Japanese shop → **confirmed recall** from CAA, live, 1 s; NEWDERY ZHX-PB22 on Amazon.in → **recalled abroad, same model** (CPSC), sent for review; Baseus BS-30KP365 in Australia → **recalled here for some units, check the serial** (ACCC via OECD); Anker A1263 in Singapore → recalled abroad (CPSC); an unbranded "Fast charger 65W" → not enough evidence.

---

## 🎯 Plan: work through in order
Each line: who · time · score points it adds. Tick it, then re-score ([Score](#-score-out-of-100)). If time runs short, protect the deploys, the cross-border number, the deck, the video and the submission; drop items 11–13 first.

### Tonight, 16 Oct: make it visible (before the freeze)
- [x] **1. Commit the extension's open changes**: the 26-language picker in `extension/content.js` · Solomon · 5 min
- [x] **2. Korea and Taiwan website-age fix** (done 16 Oct: `co.kr`, `com.tw`, `com.hk` and Coupang, Gmarket, 11st, momo, PChome, HKTVmall; tests pass): add `co.kr`, `com.tw`, `com.hk` to `TWO_PART_TLDS` and Coupang, Gmarket, 11st, momo to `MARKETPLACES` in `engine/trust.py`, with tests. Same bug just fixed for Japan and SEA; goes out with item 4 · Claude · 15 min
- [x] **3. India notices into Cloud SQL** (done 16 Oct: CCPA 15, BIS 21 in Cloud SQL): with `cloud-sql-proxy --port 5443` running: `cd engine && PYTHONPATH=.. uv run python ../data/load_india_notices.py --db <Cloud SQL URL on :5443>` · Solomon · 5 min
- [x] **4. `make deploy-api`** (done 16 Oct, revision safeshelf-api-00035, plan v2.2 live; `make check-live` all good: CPSC, CAA, OECD and India reachable from Cloud Run, all 5 JAPAC cases right in about 1 s). Still to do: `make schedule-recheck` and `make schedule-watch-recheck`.: carries everything under [Built, waiting for deploy](#-built-waiting-for-deploy). Then `make schedule-recheck` once and `make deploy-api` again for the half-hourly recall re-check. Check it live afterwards · Solomon · 20 min
- [ ] **5. Judges' web page live**: `make web-samples` → `make deploy-web` (Firebase Hosting; Firebase may need enabling on the project). Look at it on a phone · Solomon · 30 min
- [ ] **6. WhatsApp bot on a Meta test number**; record the Hindi voice-note moment · Solomon · 30 min
  - *Items 3–6 together: UX +3, Problem fit +1, Technical +2 → **77***
- [ ] **7. Cross-border warning number (JAPAC)** — *built 16 Oct, waiting for Solomon's check:* 19 pairs, generic words removed, chart `bench/crossborder_chart.svg` (median 26 days, up to 293); confirm each pair in [bench/crossborder_review.md](bench/crossborder_review.md) (Claude pre-filled same product for all 19, with reasons). Original plan:: JAPAC recalls of a product another regulator recalled first. First pass: 41 JAPAC recalls share a model number and brand with a US recall (Australia 31, Japan 6, Korea 2, Singapore 1, Taiwan 1); the US was first in 20, with a long tail (LG home batteries: US Aug 2021 → Australia Sep 2023; EGO Power+ tools: US Jun 2023 → Australia Mar 2024). Remove false matches on generic words ("5-drawer", "2-burner"), hand-check the rest, and write it to `bench/` with a chart. Headline: "SafeShelf would have warned Australian and Japanese shoppers N weeks before their own regulator" · Claude 2 h + Solomon 20 min checking · Innovation +2, Problem fit +2 → **81**
- [ ] **8. Re-test a real Amazon.in check**: it ran for minutes, then dropped. Probably the same 45 s worker sleep fixed in 2040f43; confirm on Amazon.in, because the video needs an Indian product that answers · Solomon · 15 min

### 17 Oct morning: JAPAC and Indian proof (data and measurement, not features)
- [ ] ~~**9. Backtest with JAPAC recall dates**~~ *Blocked (16 Oct): none of the 19 cross-border products is in our review data, and the full Amazon review set ends Sep 2023, before most pairs. Item 7's lead time tells the JAPAC story instead.* Original plan:: for products from item 7 that have amazon.com reviews, use the Australian or Japanese recall date as the cutoff ("flagged before ACCC or CAA acted"). Small numbers; report every outcome · Claude · 2–3 h · Innovation +2 → **83**
- [ ] **10. More Indian listings**: Firecrawl collects Amazon.in and Flipkart listings in risky categories (power banks, chargers, pressure cookers, heaters, water heaters). Items 11 and 12 need them. Today only 286 Indian listings against 27,525 amazon.com · Claude · 2 h + Firecrawl credits
- [ ] **11. India case studies**: the 4 CCPA pressure-cooker recall orders. Flipkart shows dated reviews without a login: read the reviews posted before each order and see whether SafeShelf would have flagged it earlier. Present as case studies, not a backtest · Claude · 3 h · Problem fit +2, Innovation +1 → **86**
- [ ] **12. India "still on sale" check** — *prepared 16 Oct:* the 9 exact listings CCPA named in Jan 2023 are in [bench/fixtures/india/still_on_sale.md](bench/fixtures/india/still_on_sale.md); the 2 Snapdeal ones are gone; Amazon.in and Flipkart refuse automated checks, so Solomon opens the 7 links in a browser (2 min). Original plan:: are the CCPA-ordered models, and the product types from the BIS raids, still listed on Amazon.in and Flipkart today? Hand-check every row; name sellers only for exact-model matches. One confirmed listing gives the deck its line: "A product India ordered recalled is still for sale on ___" · Claude + Solomon checking · 2 h · Problem fit +2 → **88**
- [ ] **13. Hand-check the 3 exact-model US leads and the Sunbeam heated blanket** (`data/raw/realworld/review_sheet.json`: 34 leads, 3 exact model still for sale, 17 possibly the same, none checked). Claim only what a person confirmed · Solomon · 30 min · Innovation +1 → **89**

### 17 Oct afternoon: the story
- [ ] **14. Final runs**: `make bench`, `make eval-agents`; `make warm` before recording · 30 min
- [ ] **15. Deck** from the official 16-slide template, exported to PDF · Solomon · 3 h · Innovation +1, Problem fit +1, Technical +1 → **92**. Numbers to lead with:
  - "a third of Gemini's false alarms at the same catch rate" and "pooling copies is what makes it work: 1/25 without it, 6/25 with it" (don't headline the bare 6/25)
  - the cross-border number (7), the JAPAC backtest (9), the India case studies (11) and the still-on-sale line (12)
  - India evidence: power-bank fires (IndiGo ×2, Surat) + BIS raids on Amazon and Flipkart warehouses + CCPA pressure-cooker orders, and India has no recall database
  - the [By region](#-by-region) table as a slide, gaps stated openly
- [ ] **16. 3-minute video**: open with the measured numbers; show the first look on a real Amazon.in or Flipkart product (genuine product found live with Gemini + Google Search, then the next shopper gets it in seconds); close with the Hindi WhatsApp voice note · Solomon · 3 h · Technical +1, UX +1 → **94**

### 18 Oct: submit (by 11:59 PM IST)
- [ ] **17. Merge `person-1` into `main`**, update the README, make the GitHub repo public
- [ ] **18. Submit**: deployed link, public repo, video, deck

### After submission
Each is worth about +1 to Problem fit but doesn't fit before the deadline.
- [ ] Fresher Singapore (CPSO) and ASEAN recalls: the OECD GlobalRecalls portal stopped receiving them in 2022; read the regulators' own sites with the Research Agent
- [ ] New Zealand recalls (Product Safety NZ / MBIE): none loaded
- [ ] Extension on Shopee, Lazada, Rakuten, Myntra, Meesho, Tokopedia, Coupang: add to `manifest.json` and read title, price and brand from the shop's schema.org data. Test on real pages first; some shops hide it or block requests
- [ ] Pasted links from Shopee, Lazada and Tokopedia: they build pages with JavaScript, so read schema.org data or open them in the Research Agent's headless browser
- [ ] Same-currency reference prices: add Amazon.co.jp, .com.au and .sg to `REFERENCE_MARKETPLACES` (needs listings from those shops first)
- [ ] A forward JAPAC test: run the first look on each new ACCC, CAA and KATS recall as it arrives and record what reviews showed beforehand
- [ ] Popup and README wording once more shops work
- [ ] My Shelf backend (still a mock)
- [ ] Accessibility pass (Lighthouse ≥ 95)

---

## 📈 Score out of 100
Our own estimate, scored as a judge would see SafeShelf today against the four judging areas and weights. A step counts only once it's done **and** judges can see it (deployed, or in the video or deck). Re-score after each step and add a row to the history.

| Judging area | Weight | Now | If the plan lands | Where we stand |
|---|---|---|---|---|
| Technical merit and GenAI | 40 | **34** | 36 | 🟢 Strong: real agents, Gemini 3.x, measured results. Lost points: the 16 Oct work isn't deployed; an Amazon.in check stalled |
| Problem fit and impact | 25 | **19** | 25 | 🟢 Good, not Strong: JAPAC focus, 26 languages, 6,152 JAPAC notices, but no impact number of our own, India data not live, all measured proof from US data |
| Innovation | 25 | **18** | 24 | 🟢 Good, not Strong: copy-finding and first look are new, but the backtest headline undersells them and there's no checked real-world finding |
| UX | 10 | **5** | 9 | 🟡 Extension and chat page redesigned; no hosted link yet, and judges probably won't install an extension |
| **Total** | 100 | **76** | **94** | |

**Path:** 71 → 77 (items 3–6) → 81 (7) → 83 (9) → 86 (11) → 88 (12) → 89 (13) → 92 (15) → 94 (16)

**History**

| Date | Score | What changed |
|---|---|---|
| 16 Oct | 71 | First score: 16 Oct work built but not deployed; no hosted link |
| 16 Oct, evening | 76 | Plan v2.2 deployed: live official sources (CAA live), country-by-country coverage, recall abroad ≠ local recall; India notices in Cloud SQL. Still no hosted web page |

---

## 🌏 By region
Checked against the local database on 16 Oct. Cloud SQL has the same data except the India notices (item 3).

| Region | Recall data | Shops the extension reads | Answer languages | Biggest gap | Fixed by |
|---|---|---|---|---|---|
| 🇮🇳 India | 36 notices, 2021–Sep 2026 (CCPA 15, BIS 21). India has no recall database | Amazon.in, Flipkart | English + 13 (Hindi, Bengali, Tamil, Telugu…); WhatsApp voice notes in Hindi | Only 286 Indian listings (134 Amazon.in, 152 Flipkart) against 27,525 amazon.com; notices not in Cloud SQL; an Amazon.in check stalled; Myntra and Meesho not read | 3, 8, 10, 11, 12 |
| 🇯🇵 Japan | 677 (CAA), to Aug 2026 | Amazon.co.jp | Japanese | No Japanese listings or yen reference prices; Rakuten and Mercari not read | 7, 9 |
| 🇦🇺 Australia | 2,962 (ACCC), to 13 Oct 2026; 8,470 energy-registry records | Amazon.com.au | English | No AUD reference prices; Kogan not read | 7, 9 |
| 🇳🇿 New Zealand | **None** | none | English | No recall data at all | after submission |
| 🇰🇷 Korea | 2,242 (KATS), to Sep 2026 | none | Korean | No shop read; `co.kr` website-age bug; Coupang not recognised | 2, 7 |
| 🇹🇼 Taiwan | 45 (BSMI), 2023–Sep 2026 | none | Traditional Chinese | No shop read; `com.tw` website-age bug | 2 |
| 🇸🇬 Singapore | 29 (CPSO), **stops Sep 2022** | Amazon.sg | English, Malay, Chinese, Tamil | Data is four years old | after submission |
| South-East Asia | 161 (ASEAN), **stops Oct 2022** | none (screenshot or link only) | Indonesian, Malay, Thai, Vietnamese, Filipino, Burmese, Khmer, Lao | Old data; Shopee, Lazada and Tokopedia pages need JavaScript | after submission |
| 🇺🇸 US (base data) | 2,537 (CPSC), to Oct 2026 | Amazon.com | English | Not a target market, but it holds the backtest, most reviews and all 34 still-on-sale leads | — |

**Why the backtest can't simply move to JAPAC:** it replays years of dated reviews of products that were later recalled. The only open data like that is Amazon Reviews 2023, which is amazon.com only and ends in September 2023. Amazon's Japanese review set was withdrawn, Rakuten's needs a research application, and Amazon.in, .co.jp and .com.au hide most reviews behind a login. So we measure JAPAC with items 7, 9, 11 and 12 instead.

---

## 🚀 Built, waiting for deploy
All of these go live with item 4 (`make deploy-api`); the web page with item 5.
- [ ] **Judges' web page** (`web/`): tested locally on desktop, phone and dark mode. Six samples with known right answers: recall, fake shop, borrowed safety mark, buyer hazard reports, unknown product, and a clean control that must stay quiet. Each replays a saved real run at real speed, then **Run it live with Gemini** (10 a day per browser). Also "Check your own listing" and a **SafeShelf vs Gemini alone** tab. The chat page needs no extension and could be another tab; ideas from other teams in [MODULES.md P2-2](MODULES.md#p2-2-ideas-from-other-teams-entries)
- [ ] **First look for products SafeShelf has never seen** (extension 2.7.0): the card ticks off live: up to 60 critical reviews, recall notices, the market's official recall sites, and the **genuine product found with Gemini + Google Search** (brand's own page, price, energy rating, marks, authorised sellers). Only a price under half the brand's own price changes a colour; web finds are labelled "not a registry check". Saved by model number, so the next shopper gets it in seconds. Tested locally on Samsung and LG fridges, about 20 s. Live (16 Oct): the first run on a real Samsung page stopped at 45 s because Chrome put the extension's worker to sleep during the quiet minute on the recall sites; fixed by keeping it awake, picking up once by itself if the connection drops, and a Try again button. Live re-test on LG: done in 77 s, recall sites included. Also: two-letter brands (LG, HP, Mi) are now searched for recalls, and "Frost-Free" no longer matches an LG TV's "Free-Standing" recall
- [ ] **26 JAPAC languages**: English, Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Odia, Malayalam, Punjabi, Nepali, Sinhala, Japanese, Korean, Chinese (Simplified and Traditional), Indonesian, Malay, Thai, Vietnamese, Filipino, Burmese, Khmer, Lao. Picked in the extension chat or the chat page (remembered; starts from the browser's language), or just write in it: a question in Tamil or Japanese script gets a Tamil or Japanese answer. "Listen" uses that language's voice and says so when the device has none. WhatsApp: write in your language or send its name (TAMIL, 日本語, BAHASA); English and Hindi replies are hand-written, others are Gemini translations, with English sent if translation fails. Also needs the WhatsApp deploy
- [ ] **Model numbers read right**: "Convertible 5-in-1" was taken as model "IN1" on a Samsung fridge on Amazon.in, and long codes like RS76CG8003S9HL were missed; the shop's own "Model number" now comes first
- [ ] **Other JAPAC shops**: website-age check uses the shop itself on Japanese and South-East Asian addresses (`item.rakuten.co.jp` was looked up as `co.jp`; same for `.com.sg`, `.com.my`, `.co.id`, `.co.th`, `.com.ph`). Shopee, Lazada, Rakuten, Tokopedia, Mercari, Qoo10, Kogan, Trade Me and others count as big marketplaces, so the seller is judged. On shops the extension can't read, it points people to chat or WhatsApp
- [ ] **Who really sells it**: a Samsung fridge on Amazon.in sold by DAWNTECH was read by a shopper as sold by Samsung, because of the "Visit the Samsung Store" link. The seller line now says "a third-party seller, not Samsung's own store" and that the link is the brand's page, not the seller. Samsung and Xiaomi sellers are checked against the official seller lists the brands published (Sep 2025, source kept with each list): Clicktech Retail is confirmed for Samsung, DAWNTECH is not on Samsung's list (it is on Xiaomi's, for TVs). "Ships from Amazon" is shown as a small plus, not proof. Chat explains the same difference
- [ ] **Two engine fixes**: a safety mark the registry gives to another brand now makes "Is it real?" amber; Gemini's answer no longer mentions "green" when nothing is green
- [ ] **Recall Catalog**: browse and search every loaded recall by country, regulator or hazard (`GET /v1/recalls`, `GET /v1/recalls/{id}`); fixes dead image links and old ACCC links. Committed (712e1de)

---

## ✅ Done

**Live on Google Cloud**
- [x] API live on Cloud Run: 18 endpoints return real data
- [x] Cloud SQL + pgvector, Gemini 3.x on Vertex, Cloud Storage, Secret Manager; public API is rate-limited
- [x] Research Agent on its own Cloud Run service (headless browser for recall sites with no API)
- [x] Off Gemini 2.5 before its 16 Oct retirement

**Engine**
- [x] Find copies: the same product under different brand names
- [x] Safety Radar: reads reviews and review photos for danger (20/20 on hand-labelled reviews)
- [x] Recall and safety-mark checks: only an exact model counts as "recalled"
- [x] Is it real? checks: photos, price, website age, specs, hidden text
- [x] Catalog Scan for businesses: precision 1.00, recall 0.98 on a 500-row test
- [x] "Already bought it?" owner guidance and case file

**Agents (Google ADK)**
- [x] Investigate, Shelf Chat, Safer Alternative, Report Draft, Shopper Agent, Research Agent
- [x] Live agent steps; colours arrive in about 3 seconds
- [x] MCP server and A2A agent card so other AI agents can use SafeShelf

**Data**
- [x] ~27,800 products and 29,379 real reviews (mostly amazon.com; see [By region](#-by-region))
- [x] 8,689 recalls and notices: 2,537 US (CPSC) + 6,152 JAPAC: Australia 2,962 (ACCC), Korea 2,242 (KATS), Japan 677 (CAA), ASEAN 161, Taiwan 45 (BSMI), India 36, Singapore 29 (CPSO)
- [x] India: 36 official notices, 2021–2026, from government press releases: 4 CCPA recall orders (pressure cookers on Amazon, Flipkart and others), 7 CCPA "don't buy without the ISI mark" notices, 2 penalties, 1 toy-standards action, 22 BIS raids (incl. Amazon, Flipkart and FirstCry warehouses; chargers, power adaptors, LED TVs, water heaters, cables). Raids and notices never mark a product "recalled", only send it to review. Loaded locally; Cloud SQL is item 3
- [x] Real Indian power-bank fires for the pitch and video (`data/india_incidents.json`, sources checked): IndiGo Delhi–Chennai diversion (11 Oct 2026), IndiGo Chandigarh evacuation with 6 hurt (5 May 2026), a Surat YouTuber's room burned out (June 2026)
- [x] 8,470 Australian energy-registry records
- [x] "Still on sale" leads: 34 recalled products possibly still listed (US: eBay, amazon.com), found with Firecrawl + Gemini; hand-check is item 13

**Measured results**
- [x] Backtest (25 past US recalls, 40 never-recalled controls): SafeShelf catches as many recalls early as Gemini alone (6/25) with a third of the false alarms (2/40 vs 6/40). **Pooling copies of the same product is what makes it work: 1/25 without it, 6/25 with it**
- [x] Agent test set: 18/18 cases pass on the live API

**Apps**
- [x] Chrome extension: Amazon India, Japan, Australia, Singapore, US and Flipkart
- [x] New look for the extension: one chat instead of two, with sources, Listen, Copy and Try again; the verdict comes first; loading shows what is being checked; "Check this page" in the toolbar menu
- [x] Chat page (`extension/demo/chat.html`) for shoppers: example questions, live agent steps, paste or drop a screenshot, language picker, works on a phone; developer controls in a Tools drawer
- [x] WhatsApp bot built and tested: link or photo in, Hindi or English text + voice note out (Meta number is item 6)
- [x] Project website (`web/site/`, 17 Oct): Home, How it works, For agents, Results, Team, redesigned on the AIRecruit360 reference (blue #0271E4 / mint / ink, grotesk type, pixel-dither sky and grass scenes drawn by code in `assets/`); every number from `bench/` and `web/data/`. Served at `/site/` with `make deploy-web`
- [x] Download page `web/site/get.html` (17 Oct): mobile-app-style showcase with honest options: Chrome extension (.zip from GitHub + Load unpacked steps), phone browser (judges' page), WhatsApp (soon), MCP. Phone screens are labelled illustrations; there is no app-store app. Every "Add to Chrome" button now opens it
- [x] Mascot "Shelly" (17 Oct): shield-shaped guardian on the logo shape; antenna light and chest badge follow the verdict (green, amber, red, grey; blue while checking). Six SVG poses in `docs/mascot/`, kept off the website

---

## ⚠️ Risks and heads-ups
- **Judges probably won't install a Chrome extension.** The web page (item 5) fixes that.
- **Overbuilding loses** (hackathon notes). After tonight: no new features, only data, measurements and the story.
- **Amazon.in check stalled** once: ran for minutes, then dropped. Flipkart and title-only checks answer in under 20 s. Use those in the video until item 8 confirms the fix.
- **Claim only what a person checked**: still-on-sale leads, the Sunbeam finding and the cross-border matches all need a hand-check before they go in the deck.
