# Team Hashes: all ideas, one file

Updated 2026-10-11 · AI Builder Cup 2026 · Deadline **Oct 18, 11:59 PM IST** (aim Oct 17)

| Part | Idea | Theme | Role | Score |
|---|---|---|---|---|
| **1** | **ClearSight** | Sustainability | **CORE: we are building this** | **~4.45** (ceiling ~4.7) |
| 2 | SolventGate+ | Manufacturing | Backup if Earth Engine fails by end of Oct 12 | 4.34 |
| 3 | Witness | Media | Vision / roadmap slide only | ~3.9 |
| 1b | PitStop (SMED changeover copilot) | Manufacturing | New candidate (2026-10-11), see `PITSTOP.md` | ~4.39 |
| 4 | Ghost Ledger PH, HakGig, NightDesk, BatchWatch | various | Parked | 3.4–4.1 |
| 5 | ~40 others | various | Dropped | n/a |

Scores are rough estimates, weighted 40/25/25/10 (Technical / Impact / Innovation / UX). A gap under ~0.3 is basically a tie.

Other files: `HACKATHON.md` (rules, judging, deck template) · `COMPETITOR_ENTRIES.md` (~120 public entries) · `feasibility/` (satellite test script + image) · `witness/BENCHMARK.md` (25-video test set) · `solventgate/reference_docs/` (backup's evidence).

---

# PART 1 — CORE: ClearSight

**They promised · they reported · the satellite saw**

**Theme:** Sustainability & Social Impact · **Market:** India first · **Team:** A = documents/Gemini/agent, B = Earth Engine/map/UI
**Demo needs no real people.** Every input is a public government document or public satellite data.

> **Pitch:** India's environment ministry told the National Green Tribunal its regional offices would need **13 years** to inspect every clearance once. ClearSight turns each clearance letter into tests, runs the ones you can check from space, compares the results with the company's own compliance reports, and gives inspectors a ranked list with dated satellite evidence. A human signs off every decision.

> **What judges should remember:** *ClearSight doesn't decide guilt. It makes environmental promises testable, shows what evidence is missing, and records how every decision was made.*

## 1.1 The problem
- Mines and big projects get an **Environmental Clearance (EC)** with conditions: capacity, lease area, validity, green belt, dump slopes, reclamation.
- Companies **self-report compliance** every six months, in free-text prose ("being done", "maintained", "will be complied").
- **13 years per full inspection cycle:** MoEFCC 2019 affidavit to the NGT (likely *Sandeep Mittal v. MoEFCC*), cited by [LiveLaw, 21 Aug 2026](https://www.livelaw.in/articles/post-facto-environmental-clearance-546751). The same NGT orders found no monitoring for ~92% of Category-B and 33% of Category-A projects. No newer figure found.
- A missing report or a cloudy image is treated as "no problem". Nobody tracks what evidence is absent.

## 1.2 Hero case (verified)
**Balram OCP (formerly "Kalinga OCP"), Talcher coalfield, Angul, Odisha. Mahanadi Coalfields Ltd.** All post-2022 documents use the name Balram.

| Fact | Value | Source |
|---|---|---|
| Original EC | J-11015/4/87-IA-C, **24 Oct 1990**, 8 MTPA, 1,309 ha lease | MCL site, 40th EAC minutes |
| EC expired | **23 Oct 2021** (30 yrs + Covid extension) | CAG via [Construction World, 6 Oct 2026](https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253) |
| Mined without valid EC | Nov 2021 – **Mar 2023**, ~**11.5 Mt, Rs 9.57 bn** | CAG |
| Second mine in the audit | Kulda OCP: 0.23 Mt over capacity (Rs 190 M). Total across both: 11.8 Mt, Rs 9.76 bn | CAG |
| New EC | 15 MTPA / 2,574 ha, **24 Feb 2025** (EC25A001OR198573) | MCL site |
| Location | Bbox 20°55'53.6"–20°59'7.11" N, 85°2'36.37"–85°6'21.71" E (no polygon published) | 2025 EC |
| **Company's own report, Oct 2021–Mar 2022** | Filed under the 1990 EC, **never mentions it expired**, says the project "has not exceeded the approved capacity of 8 MTY" | [MCL HYC](https://www.mahanadicoal.in/Environment/pdf/EC%20Half%20Yearly/HYC_Oct21-Mar22/Balram%20OCP.pdf) |

**Bonus case:** the 2025 Ananta OCP EC contains a ministry-written table of **excess production beyond EC capacity**, year by year (1993–2010). Good second validation case.

## 1.3 The user
A **technical officer at a MoEFCC regional office** (19 Integrated Regional Offices), responsible for hundreds of projects, able to inspect a handful a year. Secondary: CAG audit teams, environmental lawyers, journalists.

## 1.4 How it works
```text
EC letter PDF ──► 1. Permit-to-Test Compiler ──► testable conditions
                                                     │
Satellite data ──► 2. Evidence Engine (code) ────────┤
Compliance report ► 3. Claim Reader ─────────────────┤
                                                     ▼
                  4. Evidence-Gap Check ──► 5. Verdict ──► 6. Human review
                                                                │
                  7. Decision Replay ◄── re-evaluation on new real data
                                                                │
                                         8. Ranked inspection list + dossier
```

**1. Permit-to-Test Compiler (Gemini).** Reads the EC letter (scanned 1990 images need OCR; 2014+ letters have text) and turns each condition into a test contract:
```json
{
  "condition_id": "EC-xii",
  "source": {"page": 2, "quote": "The capacity of the project shall not be increased without prior environmental clearance"},
  "condition": "No operation beyond EC validity / capacity",
  "location": "mine footprint (reviewer-drawn, from 2025 EC bbox)",
  "threshold": "no new bare ground / pit growth after expiry",
  "deadline": "2021-10-23 (computed by validity rule, not stated in letter)",
  "space_checkable": true,
  "evidence_required": ["Sentinel-2 monthly composites", "Dynamic World bare share", "Sentinel-1 backscatter"],
  "falsification_criteria": "consistent if bare area stays within ±2% of expiry-month baseline for 6+ months",
  "uncertainties": ["10 m resolution", "monsoon cloud", "footprint hand-drawn"],
  "status": "needs_review"
}
```
- **Validity comes from a rule, not the letter.** Pre-2006 ECs carry no expiry. Gemini extracts the issue date; code applies the validity rule and shows it on screen.
- Conditions that can't be checked from space (noise, effluent, paperwork) are listed as **"not checkable remotely"**, never dropped or passed.
- Space-checkable conditions in the 1990 letter: (iii) dump slope ≤ 28°, (iv) forest land ≤ 85.201 ha, (vi) reclamation, (xii) no capacity increase without EC.

**2. Evidence Engine (Earth Engine, deterministic code).** All area maths in code, never in the model.
- **Sentinel-2** (`COPERNICUS/S2_SR_HARMONIZED`) monthly composites with **Cloud Score+ per-pixel masking**: timelapse and image pairs.
- **Dynamic World** (`GOOGLE/DYNAMICWORLD/V1`, class 7 = bare): bare share **inside the mine footprint only**.
- **Sentinel-1** (`COPERNICUS/S1_GRD`): monsoon fallback (multi-month composites; S1B gap 2022–24).
- **AlphaEarth embeddings** (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`): year-on-year change via dot product. **2017–2024 certain**, 2025 uncertain.
- **Water:** JRC Global Surface Water ends 2021 (baseline only); use Dynamic World water / MNDWI after.

**3. Claim Reader (Gemini).** Reads the six-monthly report (prose, not checkboxes) and links each claim to a condition ID.

**4. Evidence-Gap Check.** Missing evidence is not proof of compliance.
- Missing or late report → a finding, raises priority.
- Cloud over the critical window, or footprint too small for 10 m → *inconclusive, field visit recommended*.
- Impossible or off-site coordinates → a finding.
- Two claims from the same source count as **one** confirmation (dependency tracking).
- Every verdict lists what's missing and what would change it.

**5. Verdict.** One of **consistent · possible inconsistency · inconclusive · not checkable remotely**. Evidence quality by stated rules: **strong** (two independent signals agree, cloud-free, >25 ha) · **moderate** (one signal, partial cloud, or hand-drawn footprint) · **weak** (small lease, radar only, conflicting signals). The word "violation" never appears.

**6. Human review.** Test contract, evidence, an **alternative explanation** ("may be an approved overburden dump"), missing evidence, and **Approve / Reject / Mark inconclusive** with a required note. Nothing reaches the list without a reviewer.

**7. Decision Replay.** Every status change stored with trigger, reviewer and reason. New data (a newer month, a loaded report, a corrected footprint) re-runs only what it affects and shows the change on a timeline.

**8. Output.** Ranked inspection list + one-page evidence dossier per project.

## 1.5 Demo (3 minutes)
| Time | Beat |
|---|---|
| 0:00–0:20 | **Problem:** 13-year backlog; self-reported compliance; CAG found a mine working 17 months after expiry |
| 0:20–0:50 | **Compile:** upload the scanned 1990 Balram EC. Gemini extracts conditions with quotes; the **validity rule computes 23 Oct 2021** on screen |
| 0:50–1:30 | **Evidence:** footprint on the map, Sentinel-2 slider, bare-ground chart with expiry marked. **The mine keeps working after the expiry date.** AlphaEarth agrees |
| 1:30–1:55 | **They promised · They reported · The satellite saw:** the company's report for that period never mentions expiry and says capacity wasn't exceeded |
| 1:55–2:25 | **Review + replay:** reviewer sees the alternative explanation, approves; a newer month loads and the timeline records why |
| 2:25–2:45 | **Output:** ranked list and one-click dossier |
| 2:45–3:00 | **Close + vision:** "ClearSight doesn't decide guilt. It makes environmental promises testable." Then: "Same engine, any claim about the physical world" (Witness, Part 3) |

**Wording rules:** say "shows the mine kept working after the computed expiry date", **not** "reproduces the CAG finding without anyone pointing it to the site". Government-owned mine already named in a public audit; don't name small private holders.

## 1.6 Google stack
| Product | Role |
|---|---|
| **Gemini 3.x Flash** (Vertex AI) | Compiler, Claim Reader, explanations, alternative explanations, OCR of scans |
| **ADK** (`google-adk` 2.11) | Orchestrates compile → evidence → gap check → verdict; EE functions as tools |
| **Earth Engine** | Sentinel-1/2, Dynamic World, AlphaEarth, Cloud Score+ |
| **Cloud Run** | FastAPI backend + frontend |
| **Firestore** | Cases, test contracts, reviewer decisions, replay log |
| Cloud Storage | PDFs, cached tiles |

Cut on purpose: Document AI, BigQuery GIS, Looker, Firebase Auth, custom ML models.

## 1.7 Feasibility test (2026-10-11): GO
| Test | Result |
|---|---|
| `earthengine-api` 1.7.47, `google-genai`, `google-adk` 2.11 on Python 3.14 | ✅ |
| S2, S1, Dynamic World live through today | ✅ |
| AlphaEarth | ⚠️ 2017–2024 only certain |
| JRC water | ⚠️ ends 2021 |
| EE noncommercial access | ✅ free, immediate, 150 EECU-h/month |
| CAG finding | ✅ verified |
| EC letters + compliance reports public | ✅ [mahanadicoal.in](https://www.mahanadicoal.in/Environment/hestatuatorycp.php) (mcl.gov.in is dead) |
| 1990 EC | ⚠️ scanned image, no expiry, no coordinates |
| Cloud-free S2 over mine, dry season | ✅ 28–50 scenes/season |
| Visible mine change 2021→2023→2025 | ✅ `feasibility/balram_triptych.png` |
| Naive bbox NDVI | ❌ farmland dominates; a "0% cloud" scene was hazy → must clip to footprint + per-pixel cloud mask |

Not yet tested (needs a logged-in GCP project): Earth Engine itself, Gemini on the scanned letter.

## 1.8 Cost (whole hackathon): ~$15–70, covered by the $300 trial credit
| Item | Cost |
|---|---|
| Earth Engine (Community tier) | $0 |
| Gemini 3.6/3.7 Flash on Vertex ($0.75 in / $3.75 out per 1M tokens, intro price to 31 Dec 2026) | ~$10–50 (~$0.15 per project run) |
| Cloud Run / Firestore free tiers | $0 (~$5–15 if one instance kept warm during judging) |
| Cloud Storage | < $1 |

Guardrails: $50 budget alert day 1 · cache EE + Gemini outputs for demo cases · pin a 3.x model ID in an env var · call Gemini via Vertex, not AI Studio.

## 1.9 Competitive position
- **No overlap** among ~120 public entries (scan 2026-10-11). Watch "Project CANOPY" (Sustainability, repo not public).
- Code-checked figures and human approval are now standard (Groundtruth, ASAPify, andon-agent), so they don't set us apart. **What does:** the satellite contradicting a company's own report, checked against a real audit.
- **Prior art to acknowledge:** India's Mining Surveillance System (boundaries only); **CMPDI's own satellite land-reclamation monitoring** of MCL mines (public on mahanadicoal.in); SkyTruth; ESA GreenClaims; an ISPRS 2026 paper on sand mining vs ECs. **Our new part:** conditions read from the letter + self-report comparison + evidence-gap rules.

## 1.10 Validation set
- CAG: Balram (expired EC), Kulda (capacity excess).
- Ananta OCP: ministry-written excess-production table.
- NGT: Olasingh laterite quarry, Khordha (OA 179/2026/EZ, ~15× permitted, no green belt, no reports); Bheluguri stone mahal, Assam (OA 66/2025/EZ, no EC since Jan 2024); Rushikulya sand mining, Ganjam (ORSAC imagery); Tolarpasi quarry, Talcher (OA 185/2025/EZ, unconfirmed).

## 1.11 Plan
**Today, Oct 11 (unblock):**
| Who | Task | Done when |
|---|---|---|
| Both | **Lock the team on Hack2skill** (closes tonight) | Confirmed |
| B | GCP project, register EE (noncommercial), `earthengine authenticate`, $50 budget alert | `ee.Initialize()` works |
| B | Load S2 over the Balram bbox; hand-draw the mine footprint | GeoJSON saved |
| A | Pull the Balram pack: 1990 EC, 2025 EC, HYC reports (Oct20–Mar21, Oct21–Mar22, Apr–Sep22), 40th/44th EAC minutes, CAG report | Files in `data/balram/` |
| A | Enable Vertex AI, confirm a Gemini 3.x model ID, OCR the 1990 letter | 16 conditions extracted |

**Oct 12 — go/no-go:** B gets monthly Dynamic World bare share inside the footprint (Jan 2021–Dec 2023), expiry marked. **Go** if bare area keeps growing after expiry; **no-go → SolventGate+**. A gets the compiler producing test contracts with quotes and the validity rule in code.

| Day | A (documents / Gemini / agent) | B (Earth Engine / map / UI) |
|---|---|---|
| Oct 13 | Claim Reader on prose reports; evidence-gap rules; verdict logic | AlphaEarth 2021→2024; dump/forest-area checks; S1 fallback |
| Oct 14 | ADK end to end; Firestore cases + replay log | Map, slider, three-column "promised / reported / saw" screen; first Cloud Run deploy |
| **Oct 15** | **Feature freeze.** Reviewer screen + re-evaluation; benchmark ~10 CAG/NGT cases | Ranked list + dossier; cache demo results |
| Oct 16 | README, architecture diagram, deck (incl. Witness vision slide) | Polish; record video + backup take |
| Oct 17 | **Submit** | Final test on live link |
| Oct 18 | Buffer only | |

## 1.12 Risks
- **EE access / learning curve:** B starts today; go/no-go end of Oct 12.
- **No lease polygon anywhere:** reviewer-drawn footprint from the 2025 EC bbox, labelled "moderate" evidence.
- **Farmland noise / haze:** clip to footprint, Cloud Score+, dry-season composites.
- **Small leases at 10 m:** demo on large mines; small leases auto-labelled "weak".
- **Scanned 1990 letter:** Gemini OCR; fallback is manual transcription shown as "reviewer-entered".
- **Ethics:** no "violation" wording; the hero is a government mine already in a public audit.

## 1.13 Out of scope (roadmap slide only)
Citizen reports, company response/appeal, other industries and countries (Philippine DPWH pack = Ghost Ledger), local-language voice, cumulative river-basin impact, Witness (Part 3).

---

# PART 2 — BACKUP: SolventGate+ (Manufacturing, 4.34)

**Use only if Earth Engine isn't working by end of Oct 12.** Evidence already on disk in `solventgate/reference_docs/`.

> **Pitch:** Over 300 children have died since 2022 because a drum labelled "propylene glycol" held industrial ethylene glycol. SolventGate checks every drum at the receiving gate (label, CoA, invoice, supplier chain) and blocks it from production until the lab test and paperwork are real.

**Problem.** Indonesia 2022 (200+ deaths): trader CV Samudera forged Dow's label. India 2025 (Coldrif, 24 deaths): "PG" from a detergent-fragrance firm, resold trader to trader the same day, never tested. The documents existed; nobody cross-checked them.

**Why now.** CDSCO: every excipient batch tested (Oct 2025); ONDLS portal tracks PG/glycerin/sorbitol batch by batch (22 Oct 2025); IP requires DEG/EG testing; revised Schedule M binding 1 Jan 2026 (~6,300 small makers at licence risk); Indonesia's BPOM tests every container.

**User.** Anil, QA officer at a 40-person syrup maker in Baddi.

**How it works.**
1. Photograph drum label, CoA, invoice.
2. Gemini reads all three; signals in priority order: **(1)** exact hit on WHO/DRAP falsified-batch registry, **(2)** cross-document mismatch (batch, manufacturer, site, dates), **(3)** chain of custody (repacker/trader present, seller ≠ manufacturer, same-day resale), **(4)** CoA content (no DEG/EG test, limit ≠ ≤0.10%, method ≠ GC), **(5)** grounded supplier search (detergent firm selling "pharma PG"), **(6)** visual label cues, **advisory only**.
3. Deterministic rules decide; each rule cites FDA 2023, IPC GD-11 2026, USP/EP or IPEC 2026.
4. Verdict is always **"HOLD: GC lab test required"**, never "safe". Generates quarantine label, lab request, Schedule M receiving record, mocked ONDLS entry.
5. Stretch: downstream recall screen (drum → syrup batches).

**Key finding.** The real WHO forged Dow label (batch F9600L7PPA4) **looks genuine**. Demo beat: Gemini says "appears genuine" → *"Even AI can't tell by looking"* → cross-checks catch it → HOLD.

**Evaluation.** 30–40 synthetic perturbed cases from the 5 genuine CoAs → per-rule precision/recall.

**Hard judge questions.** "A registry hit is hindsight" → show HOLD with the registry off. "Testing is already mandatory" → "rules exist; enforcement at the gate doesn't" (Coldrif: 39 critical violations, PG never tested). "Why you, no pharma background?" → every rule cites a regulator; say plainly there's no user evidence yet.

**Scores.** Tech 4.5 · Impact 4.25 · Innovation 4.5 · UX 3.5 → **4.34**. No pharma entries among ~120 public competitors.

**Build sketch.** Oct 11 model check + parse WHO/DRAP annexes · Oct 12–13 extraction + cited rule engine · Oct 14 grounded supplier check + ADK + paperwork · Oct 15 eval set · Oct 16 freeze · Oct 17 submit.

---

# PART 3 — VISION: Witness (Media, ~3.9)

**Role:** final slide of the ClearSight deck: *"The same engine verifies any claim about the physical world: permits today, viral disaster footage next."* Not being built.

**Concept.** "Could this video have been recorded at the claimed place and time?" A viral flood/cyclone video + claim → Gemini reads the scene and on-screen text → find earlier uploads (Cloud Vision Web Detection on keyframes) → weather, sun position and Sentinel-1 radar as supporting checks → verdict **consistent / possible inconsistency / inconclusive** → human review → ClaimReview output.

**Shared with ClearSight:** claim-to-test compiler, falsification criteria, evidence-gap rules, dependency tracking, human review, incremental re-verification.

**Why it's not the build.**
- Benchmark (`witness/BENCHMARK.md`, 25 videos from BOOM, Quint, Newschecker, CyberPeace): **all 18 misattributed cases were solved by an earlier upload or matching news coverage; none by physics.** The novel part is the least decisive part.
- That puts it close to the existing **InVID–WeVerify** plugin and Google Lens workflow.
- Radar can contradict a caption in only ~1 benchmark case (Fengal/Jeddah).
- No Indian case found of real footage wrongly dismissed as fake.

**Useful findings anyway:** on-screen text (dates, GPS, signs) decides several cases; clips get reused across events (CY-03, LS-01); AI-generated flood videos are rising (2025–26), and the right verdict for them is "inconclusive".

**Gate if ever revived:** Cloud Vision Web Detection finds the earlier source for ≥3 of 5 test videos (keyframes from the viral copy).

**Full-platform version** ("Witness AI": six engines, three products, ConstraintGraph): ~3.6. Too big for 7 days; vision material only.

| | Focused | Full platform |
|---|---|---|
| Technical | 4.0 | 3.0 |
| Impact | 4.0 | 4.0 |
| Innovation | 3.5 | 4.5 |
| UX | 4.0 | 3.0 |

---

# PART 4 — PARKED FINALISTS

### Ghost Ledger PH (Sustainability, 4.13)
Philippine flood-control scandal: **673 fully paid ghost projects** among ~10,000 inspected; ~₱180 bn if the rate holds across ~30,000. Public HF dataset of 10,900 DPWH projects → location plausibility + satellite change between start and claimed completion + contract red flags (₱98.999M) → ranked list. Demo: COA-confirmed Bulacan ghosts rise to the top 2%. Weak: narrow riverbank walls hard at 10 m; hot topic; DPWH has a PhilSA satellite deal. **Natural ClearSight expansion pack.**

### HakGig (Future of Work, 4.08)
Indonesia Perpres 27/2026 (platform cut ≤8%) and Malaysia Gig Workers Act 2025 (pay in 7 days, suspension ≤14 days). Upload trip screenshots → Gemini extracts → code computes the real cut with the exact article → one-tap complaint; Malay voice intake for suspensions (Gemini Live). Weak: PayProof overlap; Indonesia's final rules pending.

### NightDesk (Media, 3.69)
Night-shift triage for small fact-checking teams: Gemma filters → Gemini extracts claims from Taglish/Hinglish/Tamil video → match existing fact-checks (Fact Check Tools API) → rank by health harm → editor approves → ClaimReview. Weak: VERA Files SEEK, Full Fact Raphael, SemEval-style "already solved"; no harm-ranking validation; ClaimReview write path uncertain.

### BatchWatch (Retail, 3.43)
Chemist photographs purchase invoices → Gemini extracts batches → match CDSCO NSQ/spurious alerts → quarantine + return + inspector notice. Weak: Pharmixa already does invoice → batch extraction; "280 batches/month" figure unverified (Apr 2026 = 78, Jun 2026 = 27). Its registry matcher lives on inside SolventGate+.

---

# PART 5 — DROPPED IDEAS

| Idea | Why dropped |
|---|---|
| Golden Hour scam-recovery copilot | Several near-copies; 7+ scam entries in the cup |
| Genba Proof (worker video check) | Already sold in Japan (AI Manual Coach, Dive, Ollo) |
| LiveGuard (livestream compliance) | Common in China; real-time audio hard |
| RDANA damage reports (PH) | Luwas is a near neighbour in the cup |
| Audio description | Gapline already built and deployed |
| Hospital pre-authorisation copilot | BFSI crowded; Kavach covers appeals |
| Timbang (PH nutrition register) | AshaAI made Solution Challenge Top 100 |
| Yasashii Clinic Pack | Reads as healthcare, not media |
| Influencer ad-compliance checker | BanProof overlap; no before/after |
| Counter Check (Rx vs pack) | Nesayo already does it; handwriting ~58% accuracy |
| Outbreak kit (Indonesia school meals) | Similar tools; politically sensitive |
| Halal compliance copilot | AMANA, AMINRA, SiHalal exist |
| Australia real-estate AML agent | Crowded vendor market |
| Japan freelance law, harassment training, Korea accident safety | Existing products |
| Stealth-edit ledger for news | PageCrawl, NewsDiffs, diffengine exist |
| Village Memoir (satellite documentary) | Soft impact; Google Earth Timelapse exists |
| CBAM calculators, OTT age ratings, sign language, music licensing | Exist, or too hard in 7 days |

---

# PART 6 — HOW WE GOT HERE

| Round | What we did | Outcome |
|---|---|---|
| 1 | Manufacturing gaps for JAPAC SMEs | Expert-video → SOP already exists |
| 2 | All six themes | Scam recovery, Genba Proof, LiveGuard, RDANA, NightDesk |
| 3 | Prior-art check of top 4 | All partly done |
| 4 | Competitor screen | Scams crowded; audio description taken |
| 5 | Winner-pattern search | BatchWatch picked |
| 6 | Media-only search | NightDesk best |
| 7 | "Even better" search | SolventGate beat BatchWatch |
| 8 | Final round: demo needs no real people | **ClearSight** best; stress test produced SolventGate+ |
| 9 | Feasibility test (Oct 11) | ClearSight **GO**; hero case corrected to Balram OCP |
| 10 | Out-of-the-box Media search | Witness → benchmark showed physics isn't decisive → vision slide |

About 55 ideas screened in total. **No idea guarantees a win; execution decides more than the idea.**
