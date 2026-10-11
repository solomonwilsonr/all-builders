# AI Builder Cup 2026: everything we found

Team **Hashes** (duo) · compiled 2026-10-11 · deeper notes and sources are in the files linked at the end.

**Contents**
1. The hackathon
2. Competitor submissions
3. What wins hackathons
4. How we searched for ideas
5. The six finalists, explained
6. Ideas we dropped and why
7. Final recommendation
8. Submission deck template
9. Next steps
10. Files on disk

---

## 1. The hackathon

| Item | Detail |
|---|---|
| Name | Google Cloud AI Builder Cup 2026, JAPAC |
| Organiser | Hack2skill (sponsor: Google Cloud) |
| Eligibility | Working professionals, entrepreneurs and startups, **21+**, all members based in JAPAC. **No students**: one student disqualifies the whole team, even after selection |
| Team size | 2–4 (a minimum of 2 is required to submit). Only **2** travel to the finale |
| Entries | One team per person; one solution under one theme |
| Freshness | Only new projects built during the event; nothing started before the program launched |
| Cost | Free |
| Support | Online sessions · Discord https://discord.gg/x5GRzJbKpa · support+aibuildercup@hack2skill.com · +91 98703 30830 |

### Timeline (all deadlines 11:59 PM IST)
| Date | Milestone |
|---|---|
| Sep 1 – **Oct 11** | Registration and team formation (**closes tonight**) |
| Sep 7 – **Oct 18** | Prototype building and submission |
| Oct 19 – Nov 6 | Evaluation (scoring round) |
| **Nov 7** | **Top 50 teams shortlisted** |
| Nov 10 – Nov 30 | Mentorship Week with Google experts (likely for the Top 50) |
| **Dec 4** | In-person Grand Finale, Singapore (9 AM – 5 PM) |

Finalists get sponsored flights, accommodation and event-day meals for **2 members**. Visas are your responsibility; finalists get about 4 weeks' notice.

### Required tech
- **Models:** Gemini or Gemma
- **Agentic platform:** Agent Platform, Antigravity or AI Studio
- **Deployment:** Google Cloud via **Cloud Run or Firebase** (solutions built mainly on other clouds are ineligible)

### Submission requirements
- Working **deployed link**
- **Public GitHub repo**
- **Demo video, 3 minutes max** (YouTube, Vimeo or Google Drive)
- **Deck on the official template, exported to PDF**
- Clearly name your theme; everything in English

### Judging (the same for all themes)
| Criterion | Weight | What judges look at |
|---|---|---|
| Technical Merit & GenAI | **40%** | Meaningful use of GenAI, sound technical build, Google Cloud architectural depth, scalability |
| Problem Alignment & Impact | 25% | Fit to the chosen theme, real value to users or industry |
| Innovation & Creativity | 25% | Originality, creative use of GenAI beyond a basic implementation |
| User Experience & Design | 10% | Usability, accessibility, components working together |

### Prizes (USD 30,000, ranked across all themes, not per theme)
| Award | USD |
|---|---|
| Winner | 10,000 |
| 1st runner-up | 7,000 |
| 2nd runner-up | 5,000 |
| Best use of Google Cloud AI tools | 2,000 |
| Most Impactful Solution | 2,000 |
| Social Choice Award | 2,000 |
| Best UI/UX | 2,000 |

### The six themes (official wording, summarised)
| Theme | Problem statement | Suggested directions | Suggested Google tech |
|---|---|---|---|
| **BFSI** | Risk, fraud, automation, customer interactions, personalised finance | Fraud detection, transaction anomalies, document intelligence, financial assistance, compliance automation, risk assessment | Gemini on Vertex AI, BigQuery, Vertex AI models, Document AI, Vertex AI Search, Cloud Run, Cloud SQL/AlloyDB, Pub/Sub |
| **Retail & Commerce** | Understand, engage and serve customers; operational efficiency | Hyper-personalisation, conversational commerce, product discovery, demand forecasting, basket analysis, segmentation, inventory intelligence | Gemini, Vertex AI Search, BigQuery (+AI), Cloud Run, Cloud Storage, AlloyDB/Cloud SQL, Looker |
| **Manufacturing** | Efficiency, quality, reliability, supply/demand, sustainability; operational data → insights/actions | Predictive maintenance, visual inspection, production optimisation, supply-chain intelligence, forecasting, waste reduction, operational copilots | Gemini, Vertex AI, BigQuery, Cloud Storage, Vision AI, Pub/Sub, Dataflow, Cloud Run |
| **Media, Content & Digital** | How content is created, discovered, personalised, understood or experienced | (No dashboard screenshot captured) | — |
| **Future of Work** | Knowledge access, collaboration, decisions, everyday work | Knowledge assistants, copilots, document/meeting intelligence, workflow automation, research assistants, search | Gemini, Vertex AI Search, Document AI, **Agent Engine + ADK**, Cloud Run, BigQuery, AlloyDB/Firestore |
| **Sustainability & Social Impact** | Environmental or societal challenge | Climate intelligence, disaster preparedness, agriculture, resource optimisation, accessibility, community services, waste | Gemini, BigQuery, Vertex AI, **Earth Engine**, Cloud Storage, Vision AI, Cloud Run, Pub/Sub |

### Inconsistencies on the official site
- The rewards page shows a "USD 0" total (placeholder); the home page says $30k, and the individual prizes add up to that.
- The themes page asks for a "PDF proposal"; the FAQ says "deck". The official PPTX template settles it: deck → PDF.
- A "Category Specification" line lists Healthcare/Education/etc. That's copied from an older event; use the six themes.
- One aggregator site lists the event as ending Oct 11. The official dashboard confirms **Oct 18** for submission.

### Gemini models: important
- **Gemini 2.5 Pro/Flash/Flash-Lite retire on Vertex on Oct 16, 2026**, during judging. Don't build on them.
- On day one, list the newer model IDs your project can actually call (3.x). Keep the model ID in an environment variable.
- The $300 Google Cloud trial credit can't pay for Gemini API calls through AI Studio. Use the AI Studio free tier, or call Gemini through Vertex billed to the trial.

---

## 2. Competitor submissions

There's **no official submission count**; Hack2skill doesn't publish one. We tracked **public GitHub repos that name the hackathon**:

| Scan | Public entries |
|---|---|
| Oct 9 | ~33 |
| Oct 10 (morning) | ~45 |
| Oct 10 (second scan) | ~70 |
| **Oct 10 (evening)** | **~105** |

### By theme (latest)
| Theme | Entries | Common ideas |
|---|---|---|
| BFSI | ~27 | **Scams (7+)**, fraud investigation, credit underwriting, KYC, GST, insurance claims |
| Sustainability | ~25 | Disaster/flood, accessibility, seniors, agriculture, heat, care staffing |
| Future of Work | ~19 | Meeting commitments, organisational memory, agent governance, knowledge handover |
| Retail | ~15 | COD risk, shop voice assistants, in-store analytics, dark patterns, marketplaces |
| Manufacturing | ~11 | Predictive maintenance, fault diagnosis, shift handover, quality inspection |
| **Media** | **~8–9** | Audio description (Gapline), ad localisation, AI-video continuity checks, learning from video |

**Takeaways**
- **BFSI is the most crowded and Media the least.**
- **Most teams are probably still private**, so treat these numbers as a trend sample, not a total.
- **What matters more than theme crowding is overlap with your exact idea**, because prizes are ranked across themes.
- **No public entry touches** pharma/medicine safety, fact-checking, environmental clearances or gig-worker law.

Full list: `COMPETITOR_ENTRIES.md`

---

## 3. What wins hackathons
From our study of 16 hackathons in 2026 (`2026-hackathon-winners.md`) and `checklist.md`:

- **One named user, one painful workflow**, often healthcare or public-service paperwork
- **A measurable before/after** ("weeks → 5 hours")
- **A human-in-the-loop safeguard**: the AI says "verify", the human decides
- **Deep use of the sponsor's tech**, not a token API call
- **Looks like a product, not a demo**: it works end to end, polished, with tests
- **A credible builder or human story**, and one memorable **wow moment**
- **What didn't win:** generic "AI for X", novelty that isn't feasible, overbuilding

---

## 4. How we searched for ideas

| Round | What we did | Outcome |
|---|---|---|
| 1 | Manufacturing gaps for JAPAC SMEs | Expert-video → SOP already exists (Studist Teachme AI) |
| 2 | All six themes | Ranked: scam recovery, Genba Proof, LiveGuard, RDANA damage reports, NightDesk |
| 3 | Prior-art check of the top 4 | **All partly done.** Scam recovery copied several times (a "Golden Hour" repo existed); worker-video comparison sold in Japan (AI Manual Coach, Dive, Ollo); livestream compliance common in China; RDANA least done |
| 4 | Competitor screen | Scam ideas crowded; audio description taken (Gapline); Luwas close to RDANA |
| 5 | Winner-pattern search | **BatchWatch** picked; hospital pre-auth copilot and Philippine nutrition-register tool runners-up |
| 6 | Media-only search | NightDesk best; Yasashii Clinic Pack runner-up; influencer ad-compliance checker weaker |
| 7 | "Even better" search | **SolventGate** beat BatchWatch; Counter Check partly done; outbreak kit and halal dropped |
| 8 | Final round: **demo must need no real people** | **ClearSight** best; Ghost Ledger PH, HakGig new finalists; stress test produced SolventGate+ |

About 50 ideas screened in total.

---

## 5. The six finalists, explained

Scores are rough estimates, weighted 40/25/25/10. Separate research tracks produced them, so **a gap under ~0.3 is basically a tie.**

| Rank | Idea | Theme | Score |
|---|---|---|---|
| 1 | ClearSight | Sustainability | **4.50** |
| 2 | SolventGate+ | Manufacturing | 4.34 |
| 3 | Ghost Ledger PH | Sustainability | 4.13 |
| 4 | HakGig | Future of Work | 4.08 |
| 5 | NightDesk | Media | 3.69 |
| 6 | BatchWatch | Retail | 3.43 |

### 1. ClearSight (Sustainability), 4.50
**Problem:** in India every mine or big project needs an Environmental Clearance (EC) with conditions: lease boundary, validity date, green belt, distance from water bodies. Companies self-report compliance every six months, mostly as "Complied". The environment ministry has said its regional offices would need **13 years** to inspect every clearance once (a 2019 figure; find a 2025–26 one).

**User:** a technical officer at a Ministry of Environment regional office (secondary: CAG auditors, environmental lawyers, journalists).

**How it works**
1. Gemini reads the EC letter PDF (from PARIVESH, public, no login) → lease coordinates, dates, every condition.
2. Gemini sorts conditions into checkable from space or not.
3. An ADK agent calls **Earth Engine** (Sentinel-1/2, Dynamic World, JRC water): pit growth, bare ground outside the lease, activity after expiry, green-belt vegetation.
4. Gemini compares that with the company's public "Complied" report.
5. Verdict per condition: consistent / contradicted / **inconclusive**, with confidence and dated image pairs. Area maths runs in code.
6. Output: a ranked inspection list and an evidence dossier, framed as **"inspection priority", not an accusation.**

**Demo moment:** the **CAG audit published 6 Oct 2026** found MCL's Kalinga coal mine kept mining **~17 months after its clearance expired** (11.8 Mt, Rs 9.76 bn unauthorised across two mines). ClearSight reproduces that finding from public data in under 2 minutes. Then a split screen: *"They promised | They reported | The satellite saw."*

**Strengths:** no real people needed; Gemini + Earth Engine + ADK is the deepest Google stack; a real audit validates it; no competing entry.
**Weaknesses:** Earth Engine learning curve; small leases (~1 ha) hard to see at 10 m; coordinates in letters may be wrong.
**Prior art:** India's Mining Surveillance System checks boundaries only. ESA's GreenClaims uses a similar pattern for EU corporate claims. Nothing reads EC conditions and checks self-reports.

### 2. SolventGate+ (Manufacturing), 4.34
**Problem:** more than 300 children have died since 2022 from cough syrup made with toxic DEG/EG, sold as pharma-grade propylene glycol.
- **Indonesia 2022 (200+ deaths):** trader CV Samudera forged Dow's label.
- **India 2025 (Coldrif, 24 deaths):** the solvent came from a detergent-fragrance firm, was resold trader to trader the same day and was never tested.

**Why now:**
- Oct 2025: CDSCO ordered testing of every excipient batch.
- 22 Oct 2025: the ONDLS portal began tracking these solvents batch by batch.
- Indian Pharmacopoeia amended to require DEG/EG testing.
- Revised Schedule M binding 1 Jan 2026; ~6,300 small manufacturers at licence risk.
- Indonesia's BPOM tests every container.

**User:** the QA officer at a small syrup maker (e.g., Baddi).

**How it works**
1. Photograph the drum label, the supplier's CoA and the invoice.
2. Gemini cross-checks grade, batch/lot numbers, manufacturer, and whether a DEG/EG result is reported.
3. Google Search grounding: is the "manufacturer" a pharma producer or a detergent firm or trader?
4. **"+" part:** exact match against WHO/DRAP lists of confirmed-fake batch numbers.
5. Deterministic rules decide. The verdict is always **"HOLD: GC lab test required"**, never "safe". It generates the quarantine label, lab request and receiving record.

**Demo moment:** replay both disasters with reconstructed documents and stop both drums at the gate. Honest beat: Gemini looks at the real forged label and says it "appears genuine" (*"even AI can't tell by looking"*), and then the cross-checks catch it.

**Strengths:** extreme harm, new regulations, real WHO forged-label photos already downloaded, the least crowded large theme, no pharma entries.
**Weaknesses:** no real users to show adoption; the forged label fools visual checks; the "why you?" question is harder without pharma credibility (answer with clause citations to FDA 2023, IP, USP/EP).
**Assets already on disk:** `solventgate/reference_docs/`: 10 WHO alerts, 5 genuine CoAs, forged Dow label photos, a genuine Spectrum label, Dow SDS, FDA 2023 guidance. `solventgate/ADVISOR_OUTREACH.md`.

### 3. Ghost Ledger PH (Sustainability), 4.13
**Problem:** the Philippine flood-control scandal. **673 fully paid ghost projects** among ~10,000 inspected; the Senate estimates ~₱180 bn (US$3 bn) if the rate holds across ~30,000 projects. ~20,000 projects are still uninspected.

**User:** a COA fraud-audit team leader, or an analyst at the Independent Commission for Infrastructure.

**How it works:** a public Hugging Face dataset of 10,900 DPWH projects (location, contractor, cost, dates, CC-BY-SA) → location plausibility + satellite change between start and claimed completion + contract red flags (e.g., ₱98.999M, just under ₱100M) → projects ranked by ghost likelihood.

**Demo moment:** COA-confirmed Bulacan ghost projects rise into the top 2% without the model being told about them.

**Strengths:** national news story, free public data, the demo validates itself.
**Weaknesses:** narrow riverbank walls are hard to see at 10 m (triage, not proof); a hot topic, so others may build it; novelty medium (DPWH has a satellite deal with the Philippine Space Agency).

### 4. HakGig (Future of Work), 4.08
**Problem:** two new gig-worker laws.
- **Indonesia, Perpres 27/2026** (text published Oct 7–8, 2026): platform cut at most 8%, driver at least 92%; fee and algorithm transparency; complaints answered within 7 days. Implementing rules due by 31 Dec 2026.
- **Malaysia, Gig Workers Act 2025 (Act 872)**, in force 31 Mar 2026, covering 1.64M workers: pay within 7 days; suspension for inquiry at most 14 days, with compensation if no cause is found; 30-day internal grievance; 60 days to file for conciliation; e-Aduan Gig portal.

**Users:** Pak Budi (ojol driver, Bekasi) and Hafiz (delivery rider, Kuala Lumpur).

**How it works**
1. Upload trip screenshots; Gemini extracts fare, fee, promo and tip.
2. Code (not AI) computes the real platform cut under both readings of the rule, citing the exact article: *"14.6% on 9 trips, short Rp41,250 this week."*
3. One tap drafts the complaint and starts the 7-day clock.
4. Hafiz explains his suspension **by voice in Malay (Gemini Live)**. The app builds a timeline, shows the 14-day limit breached, computes compensation and drafts the filings.

**Strengths:** extremely timely, millions of affected workers, an impressive voice demo.
**Weaknesses:** one in-cup overlap (**PayProof**, gig-pay screenshots, no law or filing); Indonesia's final calculation rules are still pending.

### 5. NightDesk (Media), 3.69
**Problem:** small fact-checking teams get hundreds of Taglish, Hinglish and Tamil videos a night and can check only a few, so health lies spread (e.g., AI-faked ads of Dr. Willie Ong selling cures). IFCN 2026: 76% of fact-checkers are financially vulnerable or in crisis, and 86% cover health.

**User:** Joanna, the night-shift editor at a 5-person Philippine fact-checking team.

**How it works:** Gemma filters spam → Gemini extracts claims with timestamps from video and audio → match against existing fact-checks in any language (Google Fact Check Tools API) → rank by health harm → Tagalog draft → editor approves → publish as ClaimReview.

**Demo moment:** the fake doctor ad jumps to the top, labelled "HIGH HARM", already matched to a debunk.

**Strengths:** least crowded theme; strong use of Gemini on video and mixed-language audio.
**Weaknesses:** parts already exist (Full Fact's Raphael, VERA Files SEEK, many consumer apps); without fact-checkers you can't validate the harm ranking; Tagalog audio accuracy risk; ClaimReview publishing needs verifying.

### 6. BatchWatch (Retail), 3.43
**Problem:** CDSCO flags substandard or spurious medicine batches monthly, but chemists rarely hear about them. WHO: about 1 in 10 medical products in low- and middle-income countries is substandard or falsified.

**User:** Ramesh, a one-counter chemist in Lucknow with no software (India has ~1.24M chemists).

**How it works:** photograph purchase invoices (batch numbers are legally required on them) → Gemini extracts every line → match against CDSCO alert lists → confirm by photographing the strip → one tap for the quarantine entry, supplier return note and Drug Inspector notice.

**Demo moment:** *"3 flagged batches in your stock: would have been caught 41 days earlier."*

**Strengths:** simple, buildable, public data, health stakes, zero competing entries.
**Weaknesses:** novelty dropped this week (**Pharmixa**, a live product, reads medicines and batches from invoices); risks reading as "OCR plus lookup"; the headline numbers need re-checking against the actual CDSCO PDFs.

---

## 6. Ideas we dropped and why

| Idea | Why dropped |
|---|---|
| Golden Hour scam-recovery copilot | Several near-copies (Golden Hour repo, ShieldTrace, Satark, Unscammed); 7+ scam entries in the hackathon, including another GoldenHourScam |
| Genba Proof (worker video check + quiz) | Video comparison already sold in Japan (AI Manual Coach, Dive, Ollo Factory) |
| LiveGuard (livestream compliance) | Common in China; real-time audio is hard; name clash with NexTide's "Liveguard" |
| RDANA damage reports (PH) | Luwas (barangay command center) is a near neighbour in the hackathon |
| Audio description | Gapline already built and deployed in the hackathon |
| Hospital pre-authorisation copilot | BFSI crowded; Kavach covers patient-side appeals |
| Timbang (PH nutrition-register tool) | AshaAI (India version) made the Google Solution Challenge Top 100; no hours-saved data |
| Yasashii Clinic Pack | Novel combination, but reads as healthcare rather than media |
| Influencer ad-compliance checker | BanProof overlap; no real before/after figure |
| Counter Check (Rx vs pack) | Nesayo already auto-fills the H1 register; best AI reads only ~58% of Indian handwritten Rx lines correctly |
| Outbreak kit (Indonesia school meals) | Similar tools exist; politically sensitive |
| Halal compliance copilot | AMANA, AMINRA and SiHalal already exist |
| Australia real-estate AML agent | Crowded vendor market |
| Japan freelance/subcontract law, customer-harassment training, Korea serious-accident safety | Existing repos and products |
| CBAM calculators, OTT age ratings, sign language, music licensing | Already exist, or too hard in 7 days |

---

## 7. Final recommendation

**Build ClearSight.** Backup: **SolventGate+** if Earth Engine isn't working by **Oct 13**.

**Why ClearSight:** highest technical score (Gemini + Earth Engine + ADK), no real people needed, validated by a government audit published this week, and no overlap with any known entry.

**No idea can guarantee a win.** Most entries are private and the judges are unknown. Execution (a working, polished demo and a clear pitch) will decide more than the idea.

### 7-day plan (A = documents/Gemini, B = Earth Engine/map)
| Day | A | B |
|---|---|---|
| Oct 11 | **Lock team.** Pull 10 EC letters + Kalinga docs; Gemini extraction schema | Register Earth Engine; Kalinga lease polygon + Sentinel-2 timelapse |
| Oct 12 | Condition sorting; compliance-report reader | Pit-growth and bare-ground metrics; post-expiry activity |
| Oct 13 | ADK agent wiring + verdict logic. **Checkpoint: switch to SolventGate+ if EE fails** | Green-belt NDVI + water-body checks |
| Oct 14 | Dossier generator; ranked list | Map UI + timelapse slider; deploy to Cloud Run |
| Oct 15 | **Feature freeze.** Evaluate on ~10 CAG/NGT cases | UI polish; cache EE results for the demo |
| Oct 16 | Deck on the official template (real numbers on slides 11–12) | Record the 3-min video + backup take |
| Oct 17 | **Submit** (Oct 18 = buffer) | |

---

## 8. Submission deck template (16 slides)
| # | Slide | Notes |
|---|---|---|
| 1 | Team details | Team name Hashes, leader, problem statement/theme |
| 2 | Instructions | Delete before submitting |
| 3 | Brief about the idea | Pitch + user story |
| 4 | Opportunities: how it differs, how it solves, USP | Competitor comparison |
| 5 | Features | |
| 6 | Process flow / use-case diagram | |
| 7 | Wireframes (optional) | Can skip; slide 11 shows real screens |
| 8 | Architecture diagram | Google stack |
| 9 | Technologies | |
| 10 | Implementation cost (optional) | Worth filling; makes it look like a real product |
| 11 | **Prototype snapshots** | Needs real screenshots |
| 12 | **Performance / benchmarking** | Needs measured numbers |
| 13 | Future development | |
| 14 | Links | GitHub, 3-min video, live URL |
| 15–16 | Closing | |

---

## 9. Next steps
1. **Tonight (Oct 11, 11:59 PM IST):** confirm the team on the portal.
2. **Today:** stop researching and start building.
3. **Day one:** confirm callable Gemini 3.x model IDs (2.5 retires Oct 16).
4. **Oct 13:** ClearSight checkpoint.
5. **Oct 15:** feature freeze. **Oct 16:** deck + video. **Oct 17:** submit.

---

## 10. Files on disk
| File / folder | Contents |
|---|---|
| `HACKATHON.md` | Rules, themes, dates, prizes |
| `COMPETITOR_ENTRIES.md` | ~105 competitor entries by theme, three scans |
| `FINAL_IDEA.md` | ClearSight full plan |
| `IDEA_SOLVENTGATE.md` | SolventGate (backup) |
| `IDEA.md` | BatchWatch |
| `MEDIA_IDEA.md` | NightDesk (+ Yasashii Clinic Pack runner-up) |
| `solventgate/` | WHO alerts, CoAs, forged-label photos, FDA guidance, advisor outreach kit |
| `reports/` | Manufacturing and all-tracks whitespace reports |
| `research_notes/` | All research with sources: Manufacturing, All tracks, Prior art check, Winning idea search, Media idea search, Final idea round |
| `2026-hackathon-winners.md`, `checklist.md` | Winner patterns and checklist |
| `Submission Template _ AI Builder Cup.pptx` | Official deck template |
