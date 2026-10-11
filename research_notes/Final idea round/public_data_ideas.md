# Final idea round: public-data ideas ("official promise vs observed reality")

Date: 2026-10-11. Constraint: the demo runs only on public or synthetic data (no interviews, users or field photos). Credibility must come from official documents.
Overlap screen: `COMPETITOR_ENTRIES.md` (~105 entries). None mines clearance documents, audit reports or procurement records against satellite evidence. Nearest are **GreenTrace** (supply-chain carbon plus green-bond verifier with Earth Engine; early, no permit documents), **ASAPify** (Indonesian peat-fire alerts; no permits or concessions) and **NyayAI** (court-clerk document analysis, architecture only).

---

## 1. Candidate long-list (12) and quick elimination

| # | Candidate | Theme | Verdict | Why |
|---|---|---|---|---|
| 1 | **ClearSight**: Indian environmental clearance (EC) conditions compared with the proponent's self-reported compliance and with satellite evidence | Sustainability (also Manufacturing/mining) | **FINALIST A** | EC letters are public PDFs with lease pillar coordinates (verified below). The CAG report published 6 Oct 2026 gives a fresh hook and ground truth. Government MSS covers only lease-boundary encroachment for mining. No one checks conditions one by one. |
| 2 | **Ghost Ledger PH**: DPWH flood-control projects × COA fraud audits × Sentinel imagery, used to rank which of the ~20k uninspected projects to inspect first | Sustainability & Social Impact (public finance) | **FINALIST B** | 10,900-row DPWH dataset with lat/long is on Hugging Face under CC-BY-SA, no login. Confirmed ghost projects (COA, Senate) give a validation set. Risks: topical in PH, and 10 m imagery is a limit. |
| 3 | EIA public-hearing video compared with the official minutes | Sustainability | Kill | Hearings must be filmed, but the videos go on CD or pen drive to the SPCB and are **not public**. |
| 4 | Supreme Court / High Court livestream to hearing digest | Future of Work | Kill | SC already runs AI transcription (SUVAS / constitution-bench transcripts). NyayAI entry is adjacent. Weak promise-vs-reality hook. |
| 5 | Parliament video (Sansad TV, PH Senate) to tracker of ministers' assurances | Media | Kill | Lok Sabha's Committee on Government Assurances and its Online Assurance Monitoring System already extract and track assurances. PRS covers analysis. |
| 6 | India CPPP/GeM tender specs compared with CAG audit findings | BFSI / public finance | Kill | No join key between a tender and a CAG paragraph. CPPP has captchas. CAG reports are narrative. 7 days is too short. |
| 7 | Indonesia LPSE/SIRUP × BPK audit findings | public finance | Kill | ICW's **opentender.net** already scores LPSE red flags. Full BPK LHP reports often need a request (only IHPS summaries are public). |
| 8 | Regulator penalty orders (SEBI, RBI, MAS, OJK) compared with the listed company's own SEBI LODR Reg 30 / BRSR disclosures (the "disclosure gap") | BFSI | Backup | Real gap: Reg 30 requires disclosure of regulatory actions. But it is text-only, so weaker on Gemini's native strengths. Proxy advisors (IiAS, SES, InGovern) partly cover it. Low "wow". |
| 9 | Gazette land-acquisition watch: scanned multilingual e-Gazette notices (RFCTLARR s.11) to a map of affected villages | Social Impact | Backup | Gemini OCR on Hindi, Odia and other scans is a real strength. Land Conflict Watch does this by hand. Geocoding villages and scraping the e-Gazette are risky in 7 days. |
| 10 | SPCB/CPCB closure directions compared with continued plant activity (thermal, Sentinel-5P, VIIRS) | Manufacturing | Fold into #1 | Signal is too coarse (100 m to 1 km) for single units. Use it as an optional "industry pack" condition type in ClearSight. |
| 11 | Photo audit of MGNREGA NMMS attendance photos (photo-of-photo, reused images, headcount mismatch) | Social Impact | Strong #3, ethics risk | MoRD (8 Jul 2025) listed 7 manipulation patterns and ordered **manual** verification cells, which is a clear gap for Gemini vision. But the photos are of identifiable poor workers, the demo would effectively accuse private individuals, and the scheme was restructured in late 2025. |
| 12 | Union/State budget-speech promises compared with outcome budgets | Social Impact | Kill | Text only, no multimodal wow. Journalists already do it each year. |
| 13 | PMGSY road DPRs compared with Street View or satellite | Social Impact | Kill | Official GeoSadak / e-Marg exists. Rural Street View coverage is thin. Maps imagery terms restrict ML analysis. |

Rejected spaces from the brief (scams, generic RAG, meeting notes, predictive maintenance, audio description, disaster command centres, ESG reporting, consumer fact-check, shift handover, CBAM, halal) were not considered.

---

## 2. FINALIST A: ClearSight. "What they promised, what they reported, what the satellite saw"

**One-liner:** For each Indian environmental clearance, Gemini reads the official EC letter, pulls out the lease polygon and every condition, works out which conditions can be checked from space, runs the Earth Engine check, and compares the result with the proponent's own "Complied" claims. The output is a ranked inspection list with a dated evidence dossier.

### Named user
- **Primary:** Scientist-C / technical officer at a MoEFCC Integrated Regional Office (or SEIAA / SPCB member secretary) who must monitor post-clearance compliance with 2–3 staff per office.
- **Secondary:** environmental litigators (NGT petitions), CAG field audit parties, investigative journalists (Down To Earth / CSE).

### Harm (numbers)
- **CAG compliance audit, published 6 Oct 2026** (year ended March 2024): two MCL coal mines in Odisha. **Kalinga OCP kept mining for about 17 months after its EC expired** (EC expired 23 Oct 2021, mining continued to Mar 2023): 11.5 Mt, Rs 9.57 bn. Kulda OCP exceeded its EC cap by 0.23 Mt. **Total 11.8 Mt, Rs 9.76 bn recoverable.** CAG blamed "inadequate verification of EC validity and permitted production limits". https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253
- In an NGT affidavit, MoEFCC said its regional offices would need **13 years to monitor all existing clearances once** and 4.5 years to re-inspect each project. Each project is seen once every 3–4 years. There are 2–3 officials per regional office. (Older, but the structural fact still holds.) CAG Report 39 of 2016, ch. 7: https://saiindia.gov.in/uploads/download_audit_report/2016/Chapter_7_Post_Environment_Clearance_Monitoring_by_Regional_Offices_Union_Government_Report_39_of_2016.pdf
- Six-monthly compliance reports are **self-declarations** by the proponent (EIA Notification 2006; PARIVESH compliance module, MoEFCC OM 14-06-2022). https://environmentclearance.nic.in/writereaddata/OM/1187428054$299_OM_14_06_2022.pdf
- The government's Mining Surveillance System raises alerts, but "governments sleep on half of them" (The Wire). It also checks only a 500 m boundary buffer, not EC conditions. https://thewire.in/political-economy/a-system-to-identify-illegal-mining-raises-hundreds-of-alerts-governments-sleep-on-half-of-them
- TODO before the pitch: add one 2025–26 count of EC violation cases or NGT orders (e.g., a Lok Sabha reply from the Monsoon 2025 or Budget 2026 session).

### Public data (download checked)
| Source | What it gives | Login? |
|---|---|---|
| PARIVESH EC certificates, e.g. https://parivesh.nic.in/certificates/ISLAM_UDDIN/2/64694847/V_0_SIA_UP_MIN_471182_2024_64694861_-signed.pdf | Signed EC letter, 19 pp. **Verified by download:** EC ID, date 26/05/2025, lease 1.214 ha, **4 pillar coordinates (DMS) "verified by DMO"**, ultimate depth 12 m, 38,848 m³/yr, plantation at 1,000 plants/ha, green belt 33%, 2,500 saplings/ha in reclaimed area, plantation-polygon condition | **No login** (direct PDF). Discovery: Google `site:parivesh.nic.in/certificates` or the PARIVESH public search. |
| environmentclearance.nic.in (legacy archive) | Older ECs and OMs | No login |
| Proponents' six-monthly compliance reports (EC condition: post on own website), e.g. https://www.lodhagroup.com/sites/default/files/projects/compliance/Six-Monthly-EC-Complaince-Report-Apr-23-Sept-23.pdf, https://sipcotweb.tn.gov.in/uploads/complinance_reports/26/8.%20Compliance%20Report%20-%20Tindivanam%20June%202025.pdf | Condition-by-condition "Complied / Noted" self-claims | No login |
| CAG audit reports (cag.gov.in) and NGT joint-committee reports (greentribunal.gov.in), e.g. https://www.greentribunal.gov.in/sites/default/files/news_updates/Report%20of%20Joint%20Committee%20in%20OA%20No.%20440%20of%202023%20(Naveen%20Kumar%20Vs.%20State%20of%20U.P.%20&%20Others).pdf | **Ground truth**: officially documented violations at named sites, used to validate | No login |
| Earth Engine: Sentinel-2 SR Harmonized, Dynamic World V1 (10 m land cover: bare/trees/built/water), Sentinel-1 GRD, JRC Global Surface Water | Excavation extent, green cover, river setback, monsoon-period activity | Free noncommercial GEE registration on a Cloud project |

### Pipeline and Gemini features
1. **Long-context PDF understanding** (Gemini 2.5/3 Pro): reads a 19–60 page bilingual EC letter (Hindi/English), and **structured output** (JSON schema) extracts conditions, lease pillars (DMS to decimal polygon), validity dates, production caps, depth, setbacks and green-belt %.
2. **Checkability classifier:** Gemini tags each condition as satellite-checkable, document-checkable or field-only, and maps it to a metric template (e.g. "33% green belt" → Dynamic World tree+grass fraction inside the polygon ≥ 0.33 by year 5).
3. **Function calling / ADK agent** runs Earth Engine jobs: bare-ground growth inside and outside the polygon (encroachment), activity after EC expiry, distance of bare ground to river (JRC water), change during monsoon months (sand-mining ban), NDVI trend in the green-belt zone.
4. **Multimodal judgement:** Gemini looks at Sentinel-2 true-colour chips or an animated timelapse plus metric plots, writes a reasoned verdict with confidence, and is told to say "inconclusive" when there is cloud or the 10 m pixels limit it.
5. **Contradiction step:** it reads the proponent's six-monthly compliance PDF, aligns each claim with its condition, and flags "Claimed complied, satellite contradicts".
6. **Code execution** for area and percentage maths. Output is an **inspection-priority queue** plus an evidence dossier (PDF) for the Regional Office.
Deploy: Cloud Run (FastAPI + ADK agent + GEE Python API), Firebase Hosting (map UI), Firestore for results, Cloud Storage for PDFs and chips.

### 3-minute demo "wow moment"
1. (0:00) "CAG published this audit **five days ago**. It took two years of paperwork to find that a coal mine kept digging for 17 months on an expired clearance."
2. (0:30) Paste the Kalinga OCP EC. Gemini reads it in about 40 s, draws the lease, lists 31 conditions and marks 7 as "checkable from space", including validity to 23-Oct-2021.
3. (1:15) Timelapse Oct 2021 → Mar 2023: the pit keeps growing after expiry. Banner: **"Active excavation +X ha after EC expiry"**, which **independently reproduces the CAG finding from public data in under 2 minutes.**
4. (1:50) A UP stone/sand mining EC: pillars plotted, bare ground spreads past the lease toward the river, the green belt never appears. The proponent's own compliance report says "Complied" for both. Split screen: **They promised | They reported | Satellite saw.**
5. (2:30) Batch view: 50 ECs ranked by number of contradicted conditions. One click gives an inspection dossier. Close: "13 years to inspect every clearance once. This sorts them in an afternoon."
Ethics: show outcomes as "inspection priority / anomaly", never as "violator". Use the PSU / corporate case as the hero, and do not name small individual proponents on screen (blur names, or use EC IDs only).

### 7-day plan for 2 people
- D1: Corpus of about 40 EC PDFs (UP Bundelkhand stone, Betwa/Ken sand, Odisha coal including MCL Kalinga/Kulda) plus compliance reports where they exist. GEE project. (A: data, B: GEE scaffold)
- D2: Gemini extraction schema and DMS parser. Test on 10 PDFs and check by hand. (A) GEE metric functions: Dynamic World bare/tree fractions, polygon buffers, JRC water distance. (B)
- D3: ADK agent: condition → metric routing. Chip and timelapse generation (GEE `getVideoThumbURL`). (A+B)
- D4: Multimodal verdict prompt with an "inconclusive" path. Compliance-report alignment. Reproduce the MCL Kalinga case. (A) Firebase UI with a map (MapLibre), condition cards and split screen. (B)
- D5: Batch run, ranking, dossier PDF. Deploy to Cloud Run. (A+B)
- D6: Validation table (CAG/NGT documented sites vs tool flags), error analysis, guardrails. (A) UX polish. (B)
- D7: Video, deck, README, buffer.
Main risks: (a) small leases (~1 ha ≈ 120 S2 pixels): pick larger leases or report "insufficient resolution"; (b) coordinate errors in ECs: show the polygon and let Gemini check that it falls in the stated village/district (reverse geocode); (c) for Kalinga, mining existed before expiry, so the claim must be continued expansion, not new activity; (d) GEE quotas: precompute the hero cases.

### Novelty verdict: **High, with partial prior art**
- Government **Mining Surveillance System** (IBM/NRSC; state rollouts for minor minerals; UP AI-drone crackdown July 2025) checks **lease-boundary encroachment only**. It does not read clearance conditions or compare self-reported compliance, and covers no non-mining sectors.
- **ESA "GreenClaims"** (business.esa.int/projects/greenclaims) does LLM claim extraction plus satellite verification for **corporate green claims in Europe**. This is the same pattern but a different domain and region; cite it as validation that the pattern works.
- SatSure, Blue Sky Analytics, PhilSA and others sell geospatial analytics, but no product reads EC letters.
- Hackathons: satellite NDVI eco-monitors and carbon-credit verifiers exist (e.g. RedBrick Hacks III, Feb 2026). None reads EC conditions. No GitHub/Devpost hit for "environmental clearance" + satellite + LLM.
- Competitors in this cup: GreenTrace (green bonds) is the only Earth Engine entry. Different user and documents.

### Scores (1–5)
| Criterion | Weight | Score | Note |
|---|---|---|---|
| Technical & GenAI | 40% | **5** | Long-context bilingual PDF to schema, agentic tool use with GEE, multimodal timelapse judgement, document-vs-document contradiction |
| Problem & Impact | 25% | **4** | Rs 9.76 bn CAG finding this week; 13-year monitoring backlog. Needs one more 2025–26 statistic. |
| Innovation | 25% | **4** | New mix of condition-level checking and self-report contradiction. MSS and GreenClaims are partial prior art. |
| UX | 10% | **4** | Map plus "promised / reported / saw" split screen is very clear |
| **Weighted** | | **4.50** | 2.0 + 1.0 + 1.0 + 0.4 |

---

## 3. FINALIST B: Ghost Ledger PH. Rank the uninspected flood-control projects

**One-liner:** For each of the roughly 10,900 DPWH flood-control contracts (2018–2025), combine (i) whether the location makes sense, (ii) satellite change before start versus after "actual completion", and (iii) contract red flags such as ABC split just under PHP 100M and contractor concentration. The result is a ghost-likelihood ranking that tells COA, ICI or AFP teams which of the ~20,000 uninspected projects to visit first. It is validated against ghost projects COA and the Senate have already confirmed.

### Named user
COA fraud-audit team leader / ICI technical-working-group analyst. Secondary: PCIJ / Rappler data journalists, and LGU watchdogs (e.g. the Pasig mayor's office asked for the technical documents).

### Harm (numbers)
- **673 fully paid ghost flood-control projects** among about 10,000 inspected (2016–2025). Senate estimate: **about PHP 180 bn (US$3 bn)** if the 6% rate holds across all ~30,000 projects. **About 20,000 are still uninspected.** (Gulf News, 3 Dec 2025) https://gulfnews.com/world/asia/philippines/673-ghost-flood-projects-drain-filipino-taxpayers-senate-uncovers-3-billion-scam-1.500367682
- PHP 545 bn spent on flood control from Jul 2022 to May 2025, and **20% went to 15 contractors** (Sumbong sa Pangulo launch, Aug 2025).
- COA fraud audit reports flagged PHP 330M of Bulacan projects as ghost or illegally relocated, naming specific contracts (e.g. PHP 92.88M Angat River, Pulilan, SYMS; three PHP 98.999M TopNotch/One Frame JV projects, an ABC just under PHP 100M). https://malaya.com.ph/news/national-news/coa-finds-4-new-ghost-flood-control-projects-in-bulacan , https://www.dzrh.com.ph/post/coa-flags-peso330m-flood-control-projects-in-bulacan-ghost-illegally-transferred
- Some Sumbong sa Pangulo coordinates point to the wrong place (MindaNews fact-check, May 2026), so location integrity is itself a signal. https://mindanews.com/top-stories/2026/05/fact-check-a-sumbong-sa-pangulo-flood-control-project-item-is-falsely-located-in-another-area-in-davao-de-oro/

### Public data (download checked)
| Source | What | Login? |
|---|---|---|
| https://huggingface.co/datasets/chrisandrei/DPWH_Flood_Control_2018-2025_Projects | **10,900 rows, CC-BY-SA-4.0**: lat/long, region/province/municipality, description, ABC, contract cost, start, original and actual completion dates, contractor, district engineering office | No login (public, not gated) |
| sumbongsapangulo.ph | Official source of the list (9,855 projects, Jul 2022–May 2025) | Public site |
| COA annual audit reports and fraud audit reports (coa.gov.ph), news-reported Senate/ICI lists | Ground-truth ghost projects | Public PDFs |
| BetterGov.ph PhilGEPS open data | Bids, awards, bidders per contract | Public |
| Earth Engine: Sentinel-2 SR, Sentinel-1 GRD (SAR backscatter of new concrete), JRC water, Dynamic World | Before/after change at the riverbank | Free noncommercial |

### Gemini features
Structured extraction from free-text descriptions ("Construction of revetment along X River, 350 lm, Brgy Y"). Gemini checks whether the point lies near the named river and barangay (and spots wrong coordinates). Multimodal before/after S2 chips plus S1 backscatter plots give a verdict with "inconclusive" allowed. Long-context reading of COA audit reports links findings to contract rows. Agent tool calls to GEE and to the contract table. Grounded narrative per project for the audit team.

### 3-minute demo "wow"
"We gave the model the 10,900 projects and nothing else." The Bulacan COA-confirmed ghosts rise into the top 2% of the ranking. Click one: the PHP 92.88M Angat River project's before/after imagery shows an unchanged riverbank. Gemini notes the coordinates are 6 km from the barangay named in the title, and three sibling contracts share an ABC of PHP 98,999,000. Then: "Here are the next 50 uninspected projects with the same signature."

### 7-day buildability
Feasible. Data is already tabular with coordinates, so it is the cheaper build. Risk: Sentinel-2 at 10 m cannot reliably resolve a 200 m × 5 m revetment. It needs S1 SAR plus document and location signals, and must be framed as triage. High-resolution Google Maps imagery cannot be used for ML analysis under its terms.

### Novelty verdict: **Medium**
- **DPWH–PhilSA MOA (Nov 2025)** puts satellite monitoring of DPWH projects inside government. No AI is mentioned and it is not public-facing. https://tribune.net.ph/2025/11/03/dpwh-inks-moa-with-philsa
- **FloodGuard PH** (conversational over the project list) and **BetterGov** (open PhilGEPS) exist. Journalists did manual satellite checks. No open AI satellite ghost-triage tool was found on GitHub, Devpost or in PH hackathons (2025–26 PH hackathons were flood early-warning and sensors).
- Highly topical in PH, so **other JAPAC teams may build something close**. None appears among the ~105 public entries yet.

### Scores
| Criterion | Weight | Score |
|---|---|---|
| Technical & GenAI | 40% | 4 (the signal limit caps the satellite part) |
| Problem & Impact | 25% | 5 |
| Innovation | 25% | 3.5 |
| UX | 10% | 4 |
| **Weighted** | | **4.13** |

---

## 4. Recommendation
Build **ClearSight (A)** as a general **"Promise vs Pixel" engine**: an official document goes in, spatially checkable promises come out, then Earth Engine evidence, then a Gemini verdict, then an inspection queue. Lead with India ECs, using the CAG report from 6 Oct 2026 as a reproducible validation case. If time allows on D6, add the PH flood-control dataset as a **second "pack"** (same engine, contracts instead of clearances) to show it generalises across JAPAC. Backups: #8 disclosure gap (BFSI) and #11 NMMS photo audit (only with synthetic or blurred photos).

## Sources
- CAG MCL audit (pub. 6 Oct 2026): https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253
- CAG Report 39/2016 ch. 7: https://saiindia.gov.in/uploads/download_audit_report/2016/Chapter_7_Post_Environment_Clearance_Monitoring_by_Regional_Offices_Union_Government_Report_39_of_2016.pdf
- MoEFCC compliance OM: https://environmentclearance.nic.in/writereaddata/OM/1187428054$299_OM_14_06_2022.pdf
- DTE on the compliance module: https://www.downtoearth.org.in/blog/environment/what-is-moef-cc-s-compliance-module-for-environmental-clearance-all-about--83376
- The Wire on MSS: https://thewire.in/political-economy/a-system-to-identify-illegal-mining-raises-hundreds-of-alerts-governments-sleep-on-half-of-them
- UP AI drones (Jul 2025): https://www.theweek.in/wire-updates/national/2025/07/02/des34-up-illegal-mining-ai.html
- ESA GreenClaims: https://business.esa.int/projects/greenclaims
- PH: Gulf News 673 ghosts; Inquirer 421/8,000 https://newsinfo.inquirer.net/2122028/dizon-421-of-8000-flood-control-works-are-ghost-projects ; Tribune PhilSA MOA; HF dataset; MindaNews fact-check; Malaya/DZRH COA Bulacan.
- NMMS manipulation (MoRD, 8 Jul 2025): https://www.downtoearth.org.in/amp/story/governance/rural-ministry-backtracks-on-digital-first-attendance-system-for-mgnregs-workers-after-misuse-and-manipulation-instances
