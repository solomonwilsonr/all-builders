# Final pick: "ClearSight": they promised · they reported · the satellite saw

**Theme:** Sustainability & Social Impact (environmental intelligence) · **Market:** India first, with a second data pack for the Philippines if time allows
**Demo needs no real people.** Every input is a public government document or public satellite data.

> **One-line pitch:** India's environment ministry has said its regional offices would need **13 years** to inspect every clearance once. ClearSight reads each clearance letter, checks the conditions you can see from space, compares them with the company's own "Complied" claims, and hands inspectors a ranked list with dated satellite evidence.

## The problem
- Mines, quarries and industrial projects get an **Environmental Clearance (EC)** with conditions: lease boundary, validity period, green belt, plantation, no mining near water bodies.
- Companies **self-report compliance** every six months, mostly as "Complied".
- Regional offices can't inspect them: the ministry's own estimate is **13 years per full inspection cycle** (2019, so find one 2025–26 figure before pitching).
- **The hero case (fresh):** the CAG audit published **6 Oct 2026** found MCL's Kalinga coal mine (Odisha) kept mining for **about 17 months after its clearance expired**. Unauthorised output across two mines was **11.8 Mt, worth Rs 9.76 bn**. CAG blamed weak checks of clearance validity and limits.

## The user
A **technical officer at a Ministry of Environment regional office**, responsible for hundreds of projects and inspecting a handful each year. Secondary users: CAG audit teams, environmental lawyers, journalists.

## What it does
1. **Read:** Gemini reads the EC letter PDF from PARIVESH (bilingual, long) into a fixed structure: lease corner coordinates, area, validity dates, depth limit and every condition.
2. **Sort:** Gemini labels each condition as checkable from space (boundary, validity, green belt, water bodies, plantation) or not (noise, groundwater, paperwork).
3. **Check:** an ADK agent calls **Earth Engine** for Sentinel-2, Dynamic World land cover, Sentinel-1 radar and JRC surface water. It measures pit growth over time, bare ground outside the lease, vegetation in the promised green belt, and activity after expiry. Area maths runs in code, not in the model.
4. **Compare:** Gemini reads the company's six-monthly compliance report (public on its website) and lines up each "Complied" claim against the satellite evidence.
5. **Verdict:** for each condition, *consistent / contradicted / inconclusive*, with a confidence score and dated image pairs. **"Inconclusive" is allowed**, and small leases are flagged as low-confidence.
6. **Output:** a ranked inspection list and a one-page evidence dossier per project. It's framed as **"inspection priority", never an accusation.**

## Wow moment (demo)
**ClearSight reproduces the CAG Kalinga finding from public data in under 2 minutes:** a satellite timelapse shows the pit still growing after the clearance expired, flagged without any human pointing to it.
Then a split screen for a second project: **"They promised | They reported 'Complied' | The satellite saw"**.

## Why it beats every earlier option
| | ClearSight | SolventGate+ | HakGig | BatchWatch |
|---|---|---|---|---|
| Weighted score (agents' estimates) | **4.50** | 4.34 | 4.08 | 3.43 |
| Needs real people? | **No** | No, but adoption is unproven | No | No |
| Google tech depth (40%) | **Gemini + Earth Engine + ADK + Cloud Run**, Google's own planetary stack | Gemini + grounding | Gemini + Live API | Gemini vision |
| Ground truth for the demo | **Government audit published 6 Oct 2026** | WHO alerts | New law text | CDSCO lists |
| Market prior art | India's Mining Surveillance System checks boundaries only. ESA GreenClaims uses the same pattern for EU corporate claims. **Nobody reads EC conditions and checks self-reports** | Open | Partly open (PayProof in this hackathon) | Eroding (Pharmixa) |
| Competing entries in this hackathon | 0 (Groundtruth = heat, FloodEyes = floods, ASAPify = peat; none on clearances) | 0 | 1 partial | 0 |

Sustainability is a busy theme (~25 entries), but **prizes are ranked across all themes**, and no entry overlaps this idea. Earth Engine is a Google product judges will recognise immediately.

## Data (all public, no login)
- **EC letters:** PARIVESH (parivesh.nic.in). A sample PDF with lease coordinates was downloaded without login.
- **Six-monthly compliance reports:** posted on company websites (e.g., Coal India subsidiaries).
- **Validation set:** CAG audit (6 Oct 2026) and National Green Tribunal orders naming violating sites.
- **Satellite:** Earth Engine (Sentinel-1/2, Dynamic World, JRC water). Free for non-commercial and research use; register the Cloud project.

## Rubric map
- **Technical 40%:** multimodal reading of long documents into a schema, an agent calling Earth Engine, a Gemini verdict on image pairs that can say "inconclusive", a contradiction check against the self-report, area maths in code, Cloud Run + Firebase.
- **Impact 25%:** a 13-year inspection backlog, a Rs 9.76 bn CAG finding, a working inspection list.
- **Innovation 25%:** a new "promise vs pixel" pattern for Indian environmental clearances: document → checkable promises → satellite evidence.
- **UX 10%:** map view, timelapse slider, three-column split screen, one-click dossier.

## 7-day plan (2 people: A = documents/Gemini, B = Earth Engine/map)
| Day | A | B |
|---|---|---|
| Oct 11 | Lock team. Pull 10 EC letters + the Kalinga docs; Gemini extraction schema | Register Earth Engine; get the Kalinga lease polygon onscreen with a Sentinel-2 timelapse |
| Oct 12 | Condition sorting; compliance-report reader | Pit-growth and bare-ground metrics; post-expiry activity check |
| Oct 13 | ADK agent wiring + verdict logic (inconclusive allowed) | Green-belt NDVI + water-body checks |
| Oct 14 | Dossier generator; ranked list | Map UI + timelapse slider; deploy to Cloud Run |
| Oct 15 | **Feature freeze.** Evaluate on ~10 projects (CAG/NGT cases as ground truth) | UI polish; cache Earth Engine results for the demo |
| Oct 16 | Deck from the official template (slides 11–12 with real numbers) | Record 3-min video + backup take |
| Oct 17 | **Submit** (Oct 18 is the buffer) | |

Stretch (only if ahead): a Philippine flood-control pack using the public 10,900-project DPWH dataset to show it works across JAPAC.

## Risks and mitigations
- **Small leases (~1 ha) at 10 m resolution:** use mid/large mines for the demo, and mark small leases "low-confidence".
- **Wrong coordinates in letters:** flag polygons that are impossible or off-site, and treat that as a finding in itself.
- **Earth Engine learning curve:** person B starts today, and only three metrics are needed.
- **Cloud cover / monsoon:** Sentinel-1 radar fallback; pick dry-season dates.
- **Ethics:** use the government-owned mine (already in a public CAG audit) as the hero case. Don't name small private holders on screen.
- **Before pitching:** find one 2025–26 statistic on EC violations or inspection capacity, and confirm EC letters can be found through PARIVESH public search.

## Backup if Earth Engine proves too hard by Oct 13
**SolventGate+** (IDEA_SOLVENTGATE.md + research_notes/Final idea round/stress_test.md). Documents only, no satellite, with the real WHO forged-label photos already downloaded.

Notes: research_notes/Final idea round/
