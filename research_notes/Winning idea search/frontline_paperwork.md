# Frontline Public-Service / Community Health Worker Paperwork (JAPAC)

Research date: 2026-10-10. Context: Google Cloud AI Builder Cup 2026 (JAPAC), deadline Oct 18. Themes: Sustainability & Social Impact / Future of Work.

## TL;DR verdict

- **The generic idea "photo of a paper register + voice note -> AI fills the report" is NOT novel, especially for India ASHA/Anganwadi.** Close matches already exist:
  - **AshaAI** (Rohan45create/aasha-ai): Google Solution Challenge 2026, **Global Top 100**. Built on Google Cloud. "Workers can scan handwritten paper registers using Gemini Vision OCR", voice input in Marathi/Hindi, offline Firebase, supervisor dashboard. This is almost exactly the idea, built on the sponsor's own stack.
  - **SAHELI** (alankits/Saheli): SahAI for Shiksha 2026 (Wadhwani AI + Google.org). "Speak one Hindi sentence -> attendance register filled" for Anganwadi workers. Uses Gemini + Sarvam.
  - **ASHA Voice** (Devpost): "Speak a home visit in Telugu, Hindi or English. AI writes the record, rules catch danger signs."
  - Devpost has about **125 "ASHA worker" projects**. GitHub has 15+ ASHA+Gemini repos from Jul-Aug 2026 alone, all triage or record-keeping apps.
  - **NHA Aarogya Setu 2.0 + Google Gemma 4 Medical Data Toolkit** (announced 2026-06-30): converts photos and text of paper medical records into FHIR. It is open-sourced, so it is Google's own first-party version of "paper -> structured data".
  - **Google.org HealthVaani** (Wadhwani AI, $2.5M, Gemini 2.5 Flash): an LLM assistant for ASHA and Anganwadi workers.
  - **Karnataka SAMASTA** (2026-27): a government app that cuts the ASHA diary from **485 to 134 data fields (about 75% less data entry)** and replaces the paper registers.
  - **FormBharo** (arXiv 2608.06027): a voice agent that fills MCH enrolment forms with ARMMAN.
- **The space that is still open:** the **Philippines (FHSIS / OPT Plus)** and **Indonesia (Posyandu SIP registers -> e-PPGBM/ASIK)**. Devpost has **0 "FHSIS" projects**, 2 "barangay health worker" projects (both benefits navigators) and 7 "posyandu" projects (none do register -> official report; TumbuhGuard does measurement QA only). GitHub has **0 "posyandu gemini"** repos. FHSIS repos are CRUD apps, e.g. komunidad-health-log, a Flutter app with direct entry and no photo or voice capture.
- **What sets a project apart is not the OCR.** It is: (a) producing output in the exact official format (FHSIS TCL/M1, e-OPT Excel, Posyandu SIP/F1 monthly report, e-PPGBM upload), (b) **deterministic validation**, meaning WHO z-scores computed in code rather than by the LLM, plausibility flags and month-to-month consistency, (c) a midwife/nurse **approve-before-submit** step, and (d) checking the result against the totals of last month's report.

## 1. Quantification (best available evidence)

### India: ASHA / ANM / Anganwadi (the best-documented burden, and the most crowded field)
- One ASHA juggles **7 apps** plus WhatsApp groups, Google Sheets and Excel. An ASHA enters data twice: on paper (four "ASHA diaries") and then in apps. One worker took **about 2 days to enter 200 TB patients in Ni-Kshay**. The ABHA app logs out every 15 minutes without saving. Entering one person can take **20-30 minutes** on a slow phone. Pay is about $40/month stipend, with $55-165 total. Workers do field work and digital tasks until midnight. Source: New Lines Magazine 2025, https://newlinesmag.com/reportage/indias-digital-health-push-is-overworking-its-front-line-women/
- **64% of rural women cannot do basic smartphone tasks** (2025 government survey, cited in the same article).
- Guidelines expect about 20 hours/week from an ASHA. Surveys find 53% work 3-4 hours/day and 16% work 5-6 hours/day. Sources: https://bookdown.org/oskarevolearn/rise/asha-workload-and-remuneration.html and a Nagpur protocol at https://f1000research.com/articles/13-428
- ASHAs carry about **74 tasks**, and the diary has **485 data fields** (SAMASTA: https://www.digitalhealthnews.com/karnataka-approves-samasta-rollout-to-digitise-health-records).
- ANMs in North India spend **two-thirds of their time on indirect care** (records and reporting). Direct care plus personal time is only 19%. Source: time-motion studies at https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6258406/
- Anganwadi workers in Tamil Nadu keep **16 paper registers** and use 2 tracking apps (Poshan Tracker plus TN ICDS), across 5 digital platforms and **150+ metrics**. Their digital workload has doubled in 3 years. They upload until 10 PM although their shift ends at 4 PM. FRS needs 3 OTPs, each with waits of 20 minutes to hours. Source: https://behanbox.com/2025/05/14/from-caregivers-to-data-workers-the-hidden-burden-on-tamil-nadus-anganwadi-workers/
- **ASHA incentive claims:** the gap between filing a claim and being paid is "sometimes as much as **6-7 months**" (Columbia, Jharkhand). Meghalaya's payment app cut payment time from **120-150 days to 5-7 days**. Sources: https://globalcenters.columbia.edu/sites/default/files/content/Mumbai/Publications/Sahhiya%20(ASHA)%20Incentivization-Khunti%20Jharkhand.pdf and https://morungexpress.com/meghalaya-government-introduces-asha-payment-app

### Philippines: BHW / BNS / RHU midwife
- About 1,500 BHWs are targeted by HEAL Hub (CARE, built on CommCare) in Quezon. In the 2024 baseline (55 BHWs), only **43.6% knew how to complete online forms and fewer than 39% felt confident doing so**. The honorarium is about **$17/month**. Political turnover has caused "80,000 BHWs removed". Source: https://chwcentral.org/wp-content/uploads/Digital-health-for-Barangay-Health-Workers-_-a-mixed-methods-baseline-assessment-in-Quezon-Philippines.pdf
- Qualitative studies (Acta Medica Philippina) describe "excessive workload, meager compensation, politicization". I found **no hard hours-per-week figure for BHW paperwork**. This is a gap, so the pitch should rely on a field quote or survey, or on the per-task timings below.
- FHSIS 2018 MOP recording tools: ITR, **Target Client Lists (TCL)** for prenatal, postpartum, under-1 children, FP, sick children, TB and leprosy, then the **Summary Table** and **Monthly Consolidation Table**. These feed the M1 (monthly program report), Q (quarterly) and A (annual) reports. BHS reports go to the RHU and are consolidated there (https://jointlearningnetwork.org/wp-content/uploads/2026/05/6.-FHSIS_Data_Workflow_for_Mapping.docx).
- **OPT Plus** is the annual weighing of all children aged 0-59 months, done by Barangay Nutrition Scholars (target coverage 80% or more). BNS write on paper masterlists and then type them into the **NNC e-OPT tool (Excel 2007+, max 500 children, computes WHO status automatically)**. Inquirer, "Mismeasuring malnutrition", questions how accurate OPT Plus data is (page blocked; title confirmed).

### Indonesia: Posyandu kader
- There are **300,000+ posyandu** and about **1M active kader** (Kemendagri 2023). In 2025 the "Posyandu 6 SPM" reform widened the posyandu's scope beyond health. New systems: **SiPADU**, **ASIK** (MoH app, plus a WhatsApp chatbot for stunting data that feeds the SATUSEHAT dashboard), and **e-PPGBM**.
- Paper: **SIP has 7 formats** (birth/death records, register ibu, register bayi, register balita, register PUS/WUS, posyandu data, monthly results). Kader also mark the KMS growth chart in the Buku KIA.
- **Data quality is the headline problem.** e-PPGBM reported **4.15% stunting** (Karanganyar 2024) while the SSGI survey found **22.1%**. Another district reported 13.5% (e-PPGBM) against 25.1% (SKI 2023) (https://giziindonesia.persagi.org/index.php/Gizi_Indon/article/download/1196/486/4191). In one study, **70.6% of kader had insufficient knowledge, 79.4% insufficient skills, and measurement precision was poor (64.7%)** (IPB repository 123456789/172888).
- **A before/after number already exists:** the SIGAP posyandu digitisation cut **Laporan Bulanan Posyandu preparation from 3-5 days to under 2 hours** (30 kader, 250+ families) (ojs.amikom.ac.id semhasabdimas 2485). This is the kind of number the winners used.

### Vietnam: commune health stations
- Studies from Thanh Hoa (2024-2025) cover statistical-reporting practice at 48 CHS (238 staff) and a pre/post test of integrated reporting software (tapchiyhcd.vn; the site would not load, so I have no numbers). The immunization registry has been paper-based and error-prone. Evidence is thin and in Vietnamese only. **Not recommended.**

### Japan: care managers (ケアマネ)
- **More than 90% of 居宅介護支援 offices spend 3+ hours a day on clerical work** (MHLW/MURC 2024). A complex care plan takes up to about 4 hours. Offices fell by about 10% in 4 years, and **29 municipalities have none**. There are 125,000 licensed care managers who are not working in the role.
- **The space is commercially saturated:** CDI **SOIN** (trained on 470k care plans), Welmo **ミルモぷらん**, CareFran **TR** (funded in Dec 2025), and **Charm Care + NTT DX Partner** generative-AI care plans (target cut of 35 hours/month, rollout spring 2026), plus the national ケアプランデータ連携システム. **Not recommended.**

### Teachers (Japan/Korea) and social workers (SG/AU)
- Not researched in depth. Japanese teacher overwork is well known, but the product space (校務DX, Google Workspace for Education) is well covered and offers weaker human-in-the-loop safety stories. Skipped.

## 2. Bottleneck forms and demo templates

| Country | Bottleneck form | Template availability |
|---|---|---|
| PH | FHSIS 2018 **TCL -> Summary Table -> M1** (BHS -> RHU); **OPT Plus masterlist -> e-OPT Excel** | MOP 2018 is not easily downloadable (DOH/FOI). Scribd copies exist ("M1 all programs", "Sample OPT format"). The e-OPT Excel structure is documented. **Plan: recreate the TCL and OPT masterlist columns as a printable PDF and fill them by hand with synthetic data.** |
| ID | **SIP Format 1-7 / Register Balita / Laporan Bulanan Posyandu (F1)** -> e-PPGBM/ASIK | Many puskesmas PDFs and theses reproduce the formats (e.g. the puskesmas-trawas posyandu guide 2025). Easy to recreate. |
| IN | HMIS **HSC monthly form (NRHM/HSC/3/M)**, ASHA monthly activity / **incentive claim** form (21st-20th cycle) | MoHFW HMIS user guidelines PDF, Scribd "ASHA Report Format Revised". |
| JP | ケアプラン 第1-3表 | MHLW standard forms are public. |

**Synthetic data feasibility: high.** WHO growth standards (LMS tables) generate realistic child weights and heights. Writing the entries by hand on printed templates (several people's handwriting, with smudges and crossings-out) gives a realistic photo test set. For speech, record Taglish or Bahasa voice notes.

## 3. Existing tools and why they fall short

- **Government apps** (Poshan Tracker, ANMOL, U-WIN, RCH, e-PPGBM, ASIK, e-OPT, eFHSIS) are entry targets, not helpers. They assume the worker types each record, often after writing it on paper first ("do everything twice"). They also have no checks on plausibility, and the e-PPGBM vs SSGI gap shows the result.
- **NGO platforms** (CommCare/HEAL Hub, Medic CHT, Khushi Baby) replace paper with direct digital entry. That is a big change for workers aged 40-60 with low digital confidence (fewer than 39% confident with online forms in Quezon). They do not accept the paper workers already keep. CommCare's AI so far is an app-builder bot, not ingestion of paper forms.
- **Wadhwani AI** (Shishu Maapan newborn anthropometry from video, HealthVaani Q&A) and **Khushi Baby ASHABot** answer questions or measure. They do not produce reports.
- **Google first-party**: Gemma 4 Medical Data Toolkit / Aarogya Setu 2.0 handles lab reports and clinical documents -> FHIR, not program registers -> government aggregate reports. Still, judges may see "paper -> data" in India as already done by Google.
- **Hackathon prior art:** AshaAI (closest), SAHELI, ASHA Voice, Anganwadi Schedule Optimiser. All are India-focused.
- **Accuracy evidence that supports human-in-the-loop:** the best frontier models (Gemini 3.1 was best overall) reach only **about 85% field accuracy / about 90% weighted F1** on messy handwritten medical forms (arXiv 2604.16504). The paper itself recommends routing low-confidence fields to human review. Use this as the design rationale.

## 4. Idea framings

### A. "Timbang" — OPT Plus + FHSIS copilot for Barangay Nutrition Scholars (PH), **recommended**
- **Named user:** "Aling Nena", BNS in a Quezon barangay. She weighs about 300 children aged 0-59 months during OPT Plus season and also feeds the midwife's FHSIS TCL.
- **Flow:** she photographs each handwritten masterlist page (Gemini 2.5 Flash vision, structured JSON with a per-field confidence score). She can add a Tagalog voice note for corrections ("Si baby Cruz, 9.2 kilos pala"). **WHO z-scores are calculated in Python, not by the LLM.** Flags cover |WHZ|>5, children who got shorter since last month, digit preference (.0/.5) and duplicate children. The RHU midwife sees a review queue sorted by confidence and approves fields. The app exports an **e-OPT-compatible Excel** plus the nutrition lines of the **FHSIS M1**. Gemini drafts a short Tagalog/English narrative for the barangay nutrition committee (BNAP).
- **Before/after to measure in the demo:** minutes per 100 children, typing vs photo+review. Benchmark: SIGAP's 3-5 days -> under 2 hours. Also show the share of implausible records caught.
- **Gap vs competitors:** no FHSIS/OPT AI tools exist (0 Devpost results). HEAL Hub/CommCare requires direct entry, while this accepts the paper they already keep. Validation is deterministic rather than plain OCR.
- **Buildable in 8 days:** yes. Cloud Run (FastAPI) + Firebase Auth/Firestore/Storage + Gemini API (vision + audio) + openpyxl export + a small React/Flutter-web PWA. WHO LMS tables are public. Synthetic handwritten sheets take 1 day.

### B. "Rekap Posyandu" — monthly report + stunting data-quality guard for kader (ID)
- **Named user:** "Bu Sri", kader at a posyandu in Central Java. Each month she copies scales readings into Register Balita and the KMS, then the midwife (bidan desa) re-types them into e-PPGBM/ASIK.
- **Flow:** photograph the Register Balita/SIP page plus a voice note in Javanese/Bahasa -> structured records -> **Laporan Bulanan Posyandu (SIP F1)** and an e-PPGBM-ready CSV. Gemini explains each flag in plain Bahasa ("Tinggi Aisyah turun 3 cm dari bulan lalu — ukur ulang?"). The bidan approves before upload.
- **Metric:** 3-5 days -> under 2 hours for the monthly report (an established local baseline), plus a "data trust score" that targets the **e-PPGBM 4% vs SSGI 22%** stunting gap. The impact story is that undercounting means children miss interventions.
- **Gap:** ASIK's WhatsApp bot still takes typed entries one child at a time, and none of the 7 posyandu Devpost projects ingest registers. TumbuhGuard does measurement QA only.
- **Buildable in 8 days:** yes, with the same stack as A. Main risk: the e-PPGBM import format is not public, so it would be mocked as a CSV.

### C. "Klaim" — ASHA incentive-claim autopilot (IN), **only if India is required**
- **Named user:** an ASHA in Jharkhand/Rajasthan who loses income to unfiled or rejected incentive claims (payment lag up to 6-7 months).
- **Flow:** photograph the ASHA diary pages and add a Hindi voice note. The app matches the entries to the state incentive rulebook (deterministic rules, e.g. JSY ANC, full immunization, institutional delivery) and produces a pre-filled **monthly claim + activity report** with evidence links for the ANM to verify.
- **Angle:** the worker gets paid more and faster, an emotional and measurable "₹ recovered per month" metric. Most competitors target data for the government, not money for the worker.
- **Risk:** this is the most crowded field (AshaAI, SAHELI, SAMASTA, HealthVaani, Aarogya Setu 2.0/Gemma). Judges may have seen AshaAI in the Solution Challenge. **Novelty: low-medium.**

## Novelty verdict
- India ASHA/Anganwadi "photo + voice -> records": **low novelty** (near-duplicate AshaAI on Google Cloud/Gemini; Google's own Gemma toolkit).
- Japan care plan AI: **low** (commercial products already shipping).
- **Philippines OPT Plus/FHSIS and Indonesia Posyandu: medium-high novelty.** No AI ingestion tools were found, the official formats are well defined, there is a strong data-quality story (Indonesia's documented survey gap) and a clean human-in-the-loop step (midwife/bidan approval). A is the best fit for the winner pattern of one named user, a paper bureaucracy, a before/after number, human-in-the-loop and deep Gemini use. B has the stronger published numbers (3-5 days -> under 2 hours; 4% vs 22%) and could be merged into A as a "SEA" framing, but one country makes for a crisper pitch.
- **Weak spots to fix in the pitch:** there is no peer-reviewed hours-per-week figure for BHW/BNS paperwork. Either cite the SIGAP number plus Indian ANM time-motion data (two-thirds indirect), or time the demo live (typing 50 rows into e-OPT vs photo+review).

## Sources
- https://newlinesmag.com/reportage/indias-digital-health-push-is-overworking-its-front-line-women/
- https://behanbox.com/2025/05/14/from-caregivers-to-data-workers-the-hidden-burden-on-tamil-nadus-anganwadi-workers/
- https://www.digitalhealthnews.com/karnataka-approves-samasta-rollout-to-digitise-health-records
- https://www.indianpharmapost.com/digitisation/nha-integrates-googles-gemma-4-ai-into-aarogya-setu-20-to-digitize-health-records-20779
- https://www.theweek.in/news/biz-tech/2025/12/16/google-steps-up-ai-investments-in-indian-healthcare-infra-startups-ecosystems.amp.html (HealthVaani)
- https://github.com/Rohan45create/aasha-ai ; https://github.com/alankits/Saheli ; https://github.com/renzdeveyra/komunidad-health-log ; https://devpost.com/software/asha-voice ; https://devpost.com/software/tumbuhguard-standardize
- https://arxiv.org/abs/2604.16504 (handwritten form digitisation benchmark) ; https://arxiv.org/abs/2608.06027 (FormBharo)
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6258406/ (ANM time-motion)
- https://globalcenters.columbia.edu/sites/default/files/content/Mumbai/Publications/Sahhiya%20(ASHA)%20Incentivization-Khunti%20Jharkhand.pdf
- https://chwcentral.org/wp-content/uploads/Digital-health-for-Barangay-Health-Workers-_-a-mixed-methods-baseline-assessment-in-Quezon-Philippines.pdf
- https://jointlearningnetwork.org/wp-content/uploads/2026/05/6.-FHSIS_Data_Workflow_for_Mapping.docx
- https://giziindonesia.persagi.org/index.php/Gizi_Indon/article/download/1196/486/4191 (e-PPGBM vs SSGI)
- https://repository.ipb.ac.id/handle/123456789/172888 (kader measurement accuracy)
- https://ojs.amikom.ac.id/index.php/semhasabdimas/article/download/2485/2312 (SIGAP 3-5 days -> <2h)
- https://www.goodnewsfromindonesia.id/2025/07/07/posyandu-6-spm-dan-sipadu-resmi-diluncurkan-di-pontianak
- https://www.murc.jp/wp-content/uploads/2024/04/koukai_240425_05.pdf ; https://www.charmcc.jp/corp/_cms_/wp-content/uploads/2025/05/ (Charm Care/NTT) ; https://thebridge.jp/2025/12/carefran-raises-funding-to-expand-ai-care-plan-tool-tr-and-accelerate-multi-region-rollout
- https://blog.google/innovation-and-ai/technology/developers-tools/winning-entries-gemma-4-good-challenge/
