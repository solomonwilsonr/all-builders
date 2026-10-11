# Final idea (locked 2026-10-11): "ClearSight": they promised · they reported · the satellite saw

**Theme:** Sustainability & Social Impact (environmental intelligence) · **Market:** India first
**Team:** Hashes (A = documents/Gemini/agent, B = Earth Engine/map/UI) · **Deadline:** Oct 18, 11:59 PM IST
**Demo needs no real people.** Every input is a public government document or public satellite data. Nothing in the core result is simulated.

> **One-line pitch:** India's environment ministry has said its regional offices would need **13 years** to inspect every clearance once. ClearSight turns each clearance letter into tests, runs the ones you can check from space, compares the results with the company's own "Complied" claims, and gives inspectors a ranked list with dated satellite evidence. A human signs off every decision.

> **What judges should remember:** *ClearSight doesn't decide guilt. It makes environmental promises testable, shows what evidence is missing, and records how every decision was made.*

Built from three earlier drafts: the original ClearSight (core case and data), **OpenPermit** (Permit-to-Test Compiler, human review, Decision Replay, safe wording) and **NegativeSpace** (missing evidence is not proof of compliance, AlphaEarth embeddings). Previous version: `research_notes/Final idea round/FINAL_IDEA_v1_clearsight.md`.

## The problem
- Mines, quarries and industrial projects get an **Environmental Clearance (EC)** with conditions: lease boundary, validity period, green belt, plantation, no mining near water bodies.
- Companies **self-report compliance** every six months, mostly as "Complied".
- Regional offices can't inspect them: the ministry's own estimate is **13 years per full inspection cycle** (2019; find a 2025–26 figure before pitching).
- Today, a **missing report or a cloudy image is treated as "no problem"**. Nobody tracks what evidence is absent.
- **Hero case (fresh):** the CAG audit published **6 Oct 2026** found MCL's Kalinga coal mine (Odisha) kept mining for **about 17 months after its clearance expired**. Unauthorised output across two mines was **11.8 Mt, worth Rs 9.76 bn**. CAG blamed weak checks of clearance validity and limits.

## The user
A **technical officer at a Ministry of Environment regional office**, responsible for hundreds of projects and able to inspect a handful each year. Secondary users: CAG audit teams, environmental lawyers, journalists.

## How it works (the pipeline)

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

### 1. Permit-to-Test Compiler (Gemini)
Gemini reads the EC letter from PARIVESH (long, often bilingual) and turns each condition into a test contract:

```json
{
  "condition_id": "EC-7",
  "source": {"page": 4, "quote": "Mining shall not be carried out beyond the validity of this clearance"},
  "condition": "No mining activity after clearance expiry",
  "location": "lease polygon (from letter coordinates)",
  "threshold": "no new bare ground / pit growth inside lease",
  "deadline": "2023-03-31",
  "space_checkable": true,
  "evidence_required": ["Sentinel-2 monthly composites", "Dynamic World bare-ground share", "Sentinel-1 backscatter"],
  "falsification_criteria": "Status becomes 'consistent' if bare-ground area stays within ±2% of the expiry-month baseline for 6+ months",
  "uncertainties": ["10 m resolution", "monsoon cloud cover"],
  "status": "needs_review"
}
```
Conditions that can't be checked from space (noise, groundwater, paperwork) are listed as **"not checkable remotely"**. They are never dropped quietly and never marked as passed.

### 2. Evidence Engine (Earth Engine, deterministic code)
An ADK agent calls Earth Engine. **All area and distance maths runs in code, not in the model.**
- **Sentinel-2 monthly composites:** timelapse and before/after image pairs.
- **Dynamic World:** bare-ground and vegetation share inside the lease, outside the lease and in the green belt.
- **Sentinel-1 radar:** fallback for cloudy and monsoon months.
- **JRC Surface Water:** buffer checks for "no mining within X m of water bodies".
- **AlphaEarth Foundations embeddings** (Google DeepMind, a ready-made Earth Engine dataset): year-on-year change score inside the lease and the green belt. This is a second, independent change signal next to Dynamic World.

### 3. Claim Reader (Gemini)
Gemini reads the company's six-monthly compliance report (public on company websites) and links each "Complied" claim to the matching condition ID.

### 4. Evidence-Gap Check (from NegativeSpace)
**Missing evidence is not proof of compliance.** Explicit rules:
- A **missing or late six-monthly report** is a finding in itself and raises the project's inspection priority.
- **Cloud cover over the critical window, or a lease too small for 10 m pixels:** the result is *inconclusive, field visit recommended*, never *consistent*.
- **Letter coordinates that are impossible or off-site** (polygon in a river, wrong state, area mismatch) are flagged as a finding.
- Every verdict lists **what evidence is missing** and **what would change the verdict**.

### 5. Verdict (fixed wording, no made-up percentages)
For each condition, one of: **consistent · possible inconsistency · inconclusive · not checkable remotely**.
Evidence quality is labelled by **stated rules**, not a model's confidence score:
- **Strong:** two independent signals agree (e.g., Dynamic World + AlphaEarth), cloud-free, lease larger than 25 ha.
- **Moderate:** one signal, or partial cloud.
- **Weak:** small lease, radar only, or conflicting signals.
The word "violation" never appears. Gemini writes a plain-language explanation from the measured numbers and cites them.

### 6. Human review
Reviewer screen: the test contract, supporting evidence, a possible **alternative explanation** (e.g., "bare ground may be an approved overburden dump" or "may be seasonal"), missing evidence, and **Approve / Reject / Mark inconclusive** with a required note. **Nothing reaches the inspection list or a dossier without a reviewer's decision.**

### 7. Decision Replay and re-evaluation
Every status change is stored with what triggered it, who decided and why. When **new real data** arrives, the system re-runs and shows the change on a timeline:
- a newer Sentinel-2 month is added,
- the company's compliance report is loaded,
- a reviewer corrects the lease polygon.

### 8. Output
A **ranked inspection list** (by evidence strength, number of possible inconsistencies, missing reports and time since last inspection) and a **one-page evidence dossier** per project, with source quotes, image pairs, measurements and decision history.

## Demo (3 minutes)
| Time | Beat |
|---|---|
| 0:00–0:20 | **Problem:** 13-year inspection backlog; companies self-report "Complied"; the CAG found a mine operating 17 months after expiry. |
| 0:20–0:50 | **Compile:** upload the Kalinga EC letter. Gemini extracts the validity condition and lease polygon and turns them into a test contract, with the source quote highlighted. |
| 0:50–1:30 | **Evidence:** map with lease polygon; Sentinel-2 timelapse slider; bare-ground chart with the expiry date marked. The pit keeps growing after expiry. AlphaEarth change score agrees. **ClearSight reproduces the CAG finding from public data, without anyone pointing it to the site.** |
| 1:30–1:55 | **Claim vs pixel:** split screen for a second project: *They promised · They reported "Complied" · The satellite saw.* A missing compliance report moves it up the list. |
| 1:55–2:25 | **Review + replay:** the reviewer sees the alternative explanation and missing evidence, then approves. Load a newer satellite month (or correct a polygon): the status changes live and the Decision Replay timeline records why. |
| 2:25–2:45 | **Output:** ranked inspection list and one-click dossier. |
| 2:45–3:00 | **Close:** "ClearSight doesn't decide guilt. It makes environmental promises testable and decisions traceable." |

## Google stack (only what we actually build)
| Product | Role |
|---|---|
| **Gemini** (Vertex AI) | Permit-to-Test Compiler, Claim Reader, plain-language explanations, alternative explanations |
| **ADK** (Agent Platform) | Orchestrates compile → evidence → gap check → verdict |
| **Earth Engine** | Sentinel-1/2, Dynamic World, JRC water, **AlphaEarth embeddings** |
| **Cloud Run** | Backend (FastAPI) and frontend |
| **Firestore** | Cases, test contracts, reviewer decisions, Decision Replay log |
| Cloud Storage | PDFs and cached image tiles |

**Cut on purpose:** Document AI (Gemini does it), BigQuery GIS (Earth Engine does the buffers), Looker, Firebase Auth, WeatherNext, custom ML models.

## Out of scope (roadmap slide only)
Citizen reports, company response and appeal workflow, other industries and countries (Philippine DPWH pack), local-language voice, cumulative impact on a river basin, privacy redaction. **Don't build any of these before Oct 18.**

## Data (all public, no login)
- **EC letters:** PARIVESH (parivesh.nic.in). A sample PDF with lease coordinates was downloaded without login.
- **Six-monthly compliance reports:** company websites (e.g., Coal India subsidiaries).
- **Validation set:** CAG audit (6 Oct 2026) and National Green Tribunal orders naming specific sites.
- **Satellite:** Earth Engine (Sentinel-1/2, Dynamic World, JRC water, AlphaEarth satellite embeddings). Free for non-commercial and research use; register the Cloud project.

## Rubric map
- **Technical 40%:** long-document extraction into a test schema; an ADK agent calling Earth Engine; two independent change signals (Dynamic World + DeepMind's AlphaEarth); maths in code; evidence-gap rules; re-evaluation on new data; Cloud Run + Firestore.
- **Impact 25%:** a 13-year inspection backlog, a Rs 9.76 bn CAG finding reproduced, a working ranked inspection list.
- **Innovation 25%:** Permit-to-Test Compiler; claim-vs-pixel comparison against self-reports; treating missing evidence as a signal; Decision Replay.
- **UX 10%:** one map, one evidence panel, one status, one timeline, one reviewer action.

## Competitive position (GitHub scan, 2026-10-11)
- **No public entry overlaps** (~115 entries): nobody works on clearances or permits, or checks company claims against satellite images.
- **Benchmark: Groundtruth** (Bengaluru heat, already live, "N of N figures verified"). Code-checked figures and human approval are now standard (Groundtruth, ASAPify, GreenLedger, andon-agent, riskbrief), so they don't set us apart. **What does:** the satellite contradicting a company's own report, checked against a real audit.
- Other geospatial entries (ASAPify, FloodEyes, AidAtlas) predict hazards; none checks whether a party kept a written promise.
- CycloneShield is **not** an AI Builder Cup entry (built for a different Hack2skill event).
- Prior art to acknowledge, not hide: India's Mining Surveillance System (boundaries only), SkyTruth, commercial ESG satellite monitoring, ESA GreenClaims. **Our new part:** conditions read from the letter, plus self-report comparison, plus evidence-gap rules.

## 8-day plan
| Day | A (documents / Gemini / agent) | B (Earth Engine / map / UI) |
|---|---|---|
| **Oct 11** | Lock team (team changes close today). Pull the Kalinga EC letter + 10 others + compliance reports. Draft the test-contract schema | Register Earth Engine. Get the Kalinga lease polygon on a map with a Sentinel-2 timelapse |
| Oct 12 | Permit-to-Test Compiler working on real PDFs (with source quotes) | Bare-ground metric inside/outside lease; post-expiry activity chart. **Go/no-go on Earth Engine by end of day** |
| Oct 13 | Claim Reader; evidence-gap rules; verdict logic | AlphaEarth change score; green-belt and water-buffer checks; Sentinel-1 fallback |
| Oct 14 | ADK wiring end to end; Firestore cases + Decision Replay log | Map UI, timelapse slider, split screen; first Cloud Run deploy |
| **Oct 15** | **Feature freeze.** Reviewer screen + re-evaluation trigger; evaluate on ~10 projects (CAG/NGT as ground truth) | Ranked list + dossier; cache Earth Engine results for the demo |
| Oct 16 | README, architecture diagram, deck (official template) | Polish; record the 3-minute video + backup take |
| Oct 17 | **Submit** | Final end-to-end test on the deployed link |
| Oct 18 | Buffer only. No new features | |

## Risks and mitigations
- **Earth Engine access or learning curve:** B starts today; only three metrics are needed. If it's not working by **end of Oct 12**, switch to SolventGate+.
- **Kalinga lease polygon missing from the letter:** look for the coordinates in the EC letter, the mining plan or the PARIVESH record. If you have to trace it from a map, say so on screen and label the evidence "moderate".
- **Small leases (~1 ha) at 10 m resolution:** use mid-size and large mines for the demo; small leases are labelled "weak" automatically.
- **Wrong coordinates in letters:** flag them as a finding (Evidence-Gap Check).
- **Cloud cover / monsoon:** Sentinel-1 radar fallback; pick dry-season dates.
- **Ethics:** the hero case is a government-owned mine already named in a public CAG audit. Don't name small private holders on screen. No "violation" wording.

## Check before pitching
- A 2025–26 statistic on EC violations or inspection capacity.
- Exact Kalinga clearance expiry date and the 17-month window (from the CAG report).
- The years covered by the AlphaEarth annual embeddings in Earth Engine. They're annual, so Sentinel-2 drives the monthly timeline and AlphaEarth confirms the year-on-year change.
- That EC letters can be found through PARIVESH public search.

## Backup if Earth Engine fails by Oct 12
**SolventGate+** (IDEA_SOLVENTGATE.md + research_notes/Final idea round/stress_test.md). Documents only, no satellite, with the real WHO forged-label photos already downloaded.

Notes: research_notes/Final idea round/
