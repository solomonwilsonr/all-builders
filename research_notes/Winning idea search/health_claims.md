# Healthcare x Insurance Paperwork (JAPAC): research notes

Researched 2026-10-10 for the Google Cloud AI Builder Cup 2026 (BFSI theme). Deadline Oct 18.

---

## 1. How big the problem is (with sources)

### India: private health insurance (IRDAI)
- **FY25 (IRDAI annual data):** 3.26 crore health claims. 87% settled, 8% repudiated, about 5% still pending at year end. Total claimed Rs 1,32,487 cr. Paid Rs 94,248 cr. **Disallowed (partial deductions) Rs 18,521 cr.** Repudiated Rs 11,412 cr. That is about Rs 30,000 cr not paid, up about 17% YoY. (Business Standard / Outlook Money, citing the IRDAI annual report.)
- **FY24:** Rs 26,000 cr disallowed plus repudiated. Repudiations rose 19.1% YoY.
- **Survey:** over 50% of claimants faced rejection or partial approval (Business Today, Jan 2025, LocalCircles). In another LocalCircles survey, 6 in 10 claimants waited **6–48 hours for discharge**.
- **IRDAI Master Circular (May 2024; in force from 31 Jul 2024):** 1-hour pre-auth and 3-hour discharge authorisation. If discharge runs past 3 hours, the insurer pays the extra hospital charges. Compliance from Aug 2024 to May 2025: 86.88% of 63.7 lakh pre-auths were decided within 1 hour, and 96.69% of 56.8 lakh discharges within 3 hours.
  - **Insight:** the insurer's clock now meets its target. The remaining delay sits on the **hospital side**: incomplete documents, queries, back-and-forth. The clock only starts once the hospital sends a *complete* request.
- **Hospital–insurer conflict:** in Aug–Sep 2025, AHPI told North Indian hospitals to suspend cashless treatment for Bajaj Allianz, citing "unilateral deductions" and slow pre-auth and discharge approvals. Max Hospitals stopped cashless for Niva Bupa (Business Standard, Sep 2025).
- **Small hospitals:** small and mid-sized hospitals make up about 85% of facilities and face months of settlement delays (Accion). Hospitals under 100 beds are 46% of empanelled facilities in government schemes and handle 54% of hospitalisations.

### India: Ayushman Bharat PM-JAY
- About **50,000 claims/day**, 1,961 procedures in HBP 2022, and **only ~20% auto-adjudicated** (NHA hackathon brief, 2026).
- Payment crises: in **Haryana, 650 private hospitals suspended PM-JAY over about Rs 490–500 cr in dues** (Aug 2025). Nagaland (Apr 2025): Rs 179 cr submitted, Rs 99 cr disbursed, Rs 48.8 cr pending. 609 private hospitals have left PM-JAY since 2018 over payment delays and low rates (Govt reply, Moneylife).
- Claims are often "query raised" for missing mandatory documents. Each HBP package has its own STG checklist (e.g. pre-op X-ray, histopathology, intra-op photo with geotag, discharge photo).

### India: NHCX
- NHCX went live in 2024. By Jul 2024, 34 insurers/TPAs and **about 300 hospitals** were live. It is **not legally mandatory**. The draw is money: DHIS pays Rs 200 per PM-JAY claim filed via NHCX in FHIR, after earlier offering Rs 500 or 10% of the claim. In Mar 2026 NHA named its first "NHCX-PMJAY Early Integrators" (nirmitee.io; NHA/IITH press release).
- **The hospital side is the bottleneck.** Small hospitals are still on paper. FHIR ClaimBundle and pre-auth example bundles are public at nrces.in.

### Philippines: PhilHealth
- **2024: 483,000 denied claims (PHP 4.7 B)** and **304,082 return-to-hospital (RTH) claims (PHP 4.2 B)**. 2018–2023: 3.0 M denied (PHP 32.4 B) and 1.74 M RTH (PHP 18.3 B). Unpaid claims 2017–2024 total PHP 59.6 B (ABS-CBN / Tribune, Jan 2025).
- Most **denials** come from missing the 60-day filing window. **RTH** claims come mainly from **clerical errors** and are fixable and resubmittable. A clean pre-submission check would prevent both.
- PhilHealth itself is piloting AI pre-validation for fraud on the payer side (SwiftClaims / Pulse 63, 2025).

### Indonesia: BPJS Kesehatan
- "Klaim pending" means a claim BPJS returned for missing evidence, a coding mismatch, or administrative gaps. A "dispute" means the two sides disagree.
- Example: RSUP Hasan Sadikin, Jun–Aug 2025: **2,888 of 12,268 claims pending (23.5%)**. **37% of those were administrative** (SEP/eligibility, missing procedure report, data mismatch).
- PERSI East Java: about IDR 500 B delayed across 12,000 services at 439 hospitals. The Ombudsman flagged pending claims as possible maladministration (Feb 2025). Clean claims are paid in about 13.6 days (BPJS, Sep 2025).

### Vietnam
- HCMC hospitals had **about VND 2,500 B in social health insurance (SHI) money not finalised** ("treo"): VND 557 B in 2023 and VND 1,930 B in 2024 (thuonghieucongluan). Disputes over "xuất toán" (VSS clawbacks) are common. Data is mostly in Vietnamese. This is a weak demo market.

### Japan (レセプト, monthly insurance claims)
- 返戻 (returns) and 査定 (deductions) hurt clinic cash flow. The market is **saturated** with レセプトチェック checker software (Mighty Checker, レセプトチェッカーLS, PHC Medicom AI, ORCA plugins, and 2026 comparison articles of AI checkers). Rules-based checking is mature. **Low novelty for us.**

### Thailand
- UCS/NHSO e-Claim has 3 funds. No good 2024–26 public number on denial pain turned up. Low priority.

---

## 2. Who suffers

1. **The TPA/insurance desk executive at a 30–100 bed nursing home in a Tier-2/3 Indian city** (e.g. a 50-bed multi-specialty hospital in Nashik or Indore). This is often 1–2 people with a nursing or commerce background. They handle 15–30 TPAs/insurers plus PM-JAY, each with its own portal and form. They type pre-auth forms from **handwritten case sheets**, chase doctors for notes, reply to queries ("provide past history / indoor case papers / ICP for LOS justification"), and rebuild the discharge file. A partial deduction or rejection comes straight out of the hospital's margin, or the patient pays.
2. **The patient and family at discharge.** LocalCircles: 6 in 10 wait 6–48 hours.
3. **The PM-JAY Arogya Mitra / MEDCO** at an empanelled private hospital. They upload STG-mandated documents per package and handle queries from the state health agency (SHA).
4. **The PhilHealth claims processor at a Level-1 private hospital**, facing the 60-day deadline and RTH corrections.

**Best demo persona:** "Priya, the TPA desk executive at a 60-bed hospital in Nashik, sends about 25 pre-auths a day across 18 insurers."

---

## 3. Existing products and the gap

| Player | Side | What it does | Gap for small hospitals |
|---|---|---|---|
| Medi Assist (MAven IDP, MAgnum, MAven Guard, MAtrix) | **TPA/payer** | AI reads hospital documents into clinical summaries. 186k pre-auths approved in under 5 min (Q1 FY27). Fraud detection. 19k hospitals. | Built to speed the *payer's* decision. Does not help the hospital *assemble* a complete, policy-aware request. |
| Star Health, Bajaj, and other insurers | Payer | AI auto-adjudication (Star aims for >50% of cashless claims via AI) | Payer side |
| NHA PM-JAY Auto-Adjudication Hackathon (May 2026, IISc; 3,500 registrants) | **Payer/SHA** | Problem statements: document classification + STG compliance, radiology correlation, forgery detection | **Payer side.** Shows that AI STG-compliance checking is a recognised priority, so a provider-side mirror is credible. |
| NHCX Hackathon (Feb–Mar 2026, IIT Hyderabad; 110+ solutions; **Google on the jury**) | Interop | FHIR / NHCX integrations | Winners not public in what I found. **Check before final pitch.** |
| ClaimBook, Healspan (60+ hospitals), Care.fi RevNow (300 hospitals) | **Hospital** | Insurance desk workflow, tracking, query notifications, RCM financing | Workflow and tracking tools. No evidence of multimodal reading of handwritten notes, per-package/policy rule matching, or AI-drafted query replies. Care.fi bundles financing. |
| HMIS vendors (Docpulse, Healthray, KareXpert, Practo Insta) | Hospital | HMIS with a TPA module | Form-filling only |
| Plum, Loop, Even | Employer/payer/insurer | Group cover and claims support for employees | Patient/employer side, not the hospital desk |
| US AI RCM (AKASA, Infinitus, Cohere Health, Waystar) | US payer/provider | Prior auth and denial prediction for US CPT/ICD and payer policies | Not in India/SEA. Assumes structured EHRs, and Indian hospitals are paper-based. |
| Japan レセプトチェック checker software | Clinic | Rules + AI checking | Mature. Japan-only. |
| PhilHealth / SwiftClaims | Payer | AI fraud pre-validation | Payer side |

**What nobody clearly does today (the white space):**
1. **Multimodal intake on the hospital side.** Photos of handwritten case sheets, investigation reports, and bills go to structured fields (Gemini vision).
2. **Package/policy-aware completeness checks before submission.** Map the case to a PM-JAY HBP package or the policy terms (room-rent caps, sub-limits, waiting periods, exclusions) and list the missing mandatory documents.
3. **Predict the query or deduction before it happens**, with citations to the specific STG clause or policy clause.
4. **Draft the query response or appeal**, grounded in the patient's own documents, for a human to approve.
5. **Output an NHCX FHIR ClaimBundle**, so small hospitals get the DHIS Rs 200/claim incentive without buying a full HMIS.

Medi Assist and the NHA hackathon are building the *mirror image* of this on the payer side. The pitch writes itself: *"Payers have AI now. The 50-bed hospital does not."*

---

## 4. Hackathon prior art
- lablab AMD Hackathon: **MediClear**, a 4-agent prior auth + appeals system. US-centric (ICD-10, US payers).
- AI Tinkerers LA: **ClaimReclaim**, a voice agent for pre-auth calls. US.
- MediAuthPro (UiPath forum): voice notes to pre-auth justification. Generic/US.
- NHA PM-JAY Auto-Adjudication Hackathon (payer side) and the NHCX Hackathon (interop). Repos are not public as far as I found.
- I found no Devpost/GitHub project doing **hospital-side, India/PhilHealth package-aware pre-auth with handwritten intake on Gemini**. Searches for "PMJAY claim AI github" and "PhilHealth claim AI github" returned only official docs. *(Verify with a direct GitHub search for "pmjay" and "nhcx" before committing.)*

**Novelty verdict:** the generic version ("AI prior auth / denial appeal") is **not novel**. Several US hackathon clones exist. The **India-specific, hospital-side version is novel enough**: handwritten case sheet → HBP/STG + IRDAI policy rule check → query prediction → NHCX FHIR bundle. It is also timely (IRDAI's 1h/3h clock, NHCX incentives, NHA's own 2026 hackathons) and tied to Google (Google sat on the NHCX hackathon jury). Medium-high novelty for a JAPAC hackathon.

---

## 5. Public demo data
- **PM-JAY HBP 2022 master** (1,961 procedures, package codes, rates, mandatory pre-auth/claim documents): pmjay.gov.in/hospital/hbc and the NHA HBP 2.2 manual (nha.gov.in/img/resources/HBP-2.2-manual.pdf). State SHA sites (e.g. sha.uk.gov.in) host **STG PDFs** with per-package checklists and FAQs.
- **NHCX FHIR IG** (ClaimBundle, pre-auth example, ClaimResponse example): nrces.in/ndhm/fhir/r4/ (v3.1.0 to v5.0.0).
- **IRDAI Master Circular on Health Insurance** (May 2024) plus standard product wordings (exclusions, waiting periods, room-rent proportional deduction) from insurer websites.
- **PhilHealth**: eClaims implementation guide; case rate lists (ACR circulars); PC2025 circulars.
- **BPJS**: INA-CBG grouper documentation; Permenkes tariffs.
- **Synthetic patient data**: Synthea (FHIR); MIMIC-IV notes need credentialing, so skip them. Generate synthetic **handwritten Indian case sheets** by printing templates, filling them by hand, and photographing them, or render them with handwriting fonts. Gemini can also generate realistic case narratives.

---

## 6. Idea framings

### A. "PreAuth Copilot": hospital TPA desk agent for India (RECOMMENDED)
- **Named user:** Priya, TPA desk executive at a 60-bed nursing home in Nashik. She handles about 25 cashless cases a day across 18 insurers and PM-JAY.
- **Flow:** She photographs the handwritten admission note, investigations, and the ID/policy card. Gemini 2.5 multimodal extracts the data. The case is matched to an HBP package or the policy terms using RAG over the STG and policy wording (Vertex AI Search, or Firestore vectors). The completeness checker produces a red/amber/green list: "Missing: pre-op ECG; LOS 5d exceeds package 3d, so add justification." It predicts the likely query or deduction with a cited clause (e.g. room-rent proportional deduction). It pre-fills the pre-auth form and an NHCX FHIR ClaimBundle. **Human-in-the-loop:** Priya and the treating doctor review every field. Low-confidence handwriting is highlighted, and nothing is sent without sign-off. When a query arrives, an agent drafts the reply from the patient's own documents.
- **Before/after:** pre-auth prep falls from about 45–60 min of retyping and chasing to under 8 min, and the first-pass "complete" rate rises. Discharge wait drops from 6–48 h (LocalCircles) toward the IRDAI 3-hour target, because the insurer's 1h/3h clock only starts on a complete file. The Rs 18,521 cr of FY25 disallowances shows the size of the money at stake.
- **Gap:** Medi Assist and the NHA hackathon do this on the *payer* side. ClaimBook, Healspan, and Care.fi do workflow and tracking, not multimodal, rule-grounded drafting.
- **Buildable in 8 days:** yes. Next.js/Flutter web on Cloud Run, Gemini 2.5 Flash/Pro (vision + function calling), ADK agent, Firestore, Cloud Storage. Seed 10–15 HBP packages (e.g. cataract, hernia, appendectomy, LSCS, PTCA) and 2 sample policy wordings. FHIR bundle from the nrces template. Demo with 3 handwritten cases.

### B. "RTH Zero": PhilHealth pre-submission scrubber
- **Named user:** Ana, billing clerk at a 50-bed Level-1 private hospital in Iloilo.
- **Flow:** Upload CF2/CF4 forms, SOA, operative record → Gemini checks against case rates, required attachments, and the 60-day deadline clock → auto-fix list → resubmission pack for existing RTH claims.
- **Before/after:** the RTH rate on the hospital's claims (nationally 304k RTH plus 483k denied in 2024, PHP 8.9 B) falls, and RTH correction time drops from days to minutes.
- **Gap:** PhilHealth's AI is fraud-side. Hospital eClaims vendors only submit.
- **Risk:** CF4 and case-rate rule data is fiddlier to obtain. The judging team may be less familiar with it. Good as a **"JAPAC-ready" second-market slide** for idea A rather than its own build.

### C. "Query-to-Cash": denial and deduction appeal agent (India PM-JAY + private)
- **Named user:** Dr. Mehta, owner of a 40-bed PM-JAY-empanelled hospital in Haryana, whose dues are stuck.
- **Flow:** Ingest the query or rejection letter plus the claim file → classify the reason → find supporting evidence in the patient file (page and bounding box) → draft the reply or appeal with the STG clause cited → track the ageing of Rs stuck.
- **Before/after:** query turnaround falls from 3–7 days to the same day, and the share of Rs recovered rises.
- **Weaker:** this is closer to the US-clone pattern (MediClear). It works best as module 2 of idea A.

**Recommendation:** build **A**, with C's query-reply drafting as a feature and B as a JAPAC expansion slide. Pitch line: *"Insurers got AI to decide in 5 minutes. Priya still spends an hour typing handwritten notes into 18 portals. We give the small hospital the same AI."*

## Open checks before committing
- Winners of the NHCX Hackathon (Mar 2026) and the PM-JAY Auto-Adjudication Hackathon (May 2026): did any build a hospital-side Gemini copilot?
- Whether Care.fi RevNow or ClaimBook now advertise LLM document reading (as of late 2026).
- Get the HBP 2022 Excel and 2–3 STG PDFs on day 1.

## Sources
- IRDAI timelines and compliance: https://oga-prod.angelone.in/news/personal-finance/cashless-health-insurance-claim-authorisation-in-2025-how-long-does-it-take-irdai-s-new-rules-and-data ; https://businessworld.in/article/cashless-claims-within-an-hour-discharge-from-hospital-in-3-hrs-irdai-521477
- FY25/FY24 rejections: https://www.outlookmoney.com/personal-finance/health-insurance-claims-worth-over-rs-26-crore-denied-in-fy24-is-your-policy-at-risk ; https://www.business-standard.com/amp/finance/personal-finance/health-insurance-claims-rejection-up-19-10-in-fy24-irdai-report-124122700754_1.html ; https://www.businesstoday.in/amp/personal-finance/insurance/story/insurance-claims-over-50-health-cover-claims-faced-rejection-or-partial-approval-says-survey-459394-2025-01-02
- Discharge delays: https://www.theweek.in/news/biz-tech/2024/04/29/medical-insurance-claims-5-out-of-10-patients-face-discharge-delays.amp.html ; https://www.outlookmoney.com/insurance/waiting-for-discharge-after-a-claim-heres-what-you-can-do
- AHPI vs Bajaj: https://www.outlookmoney.com/amp/story/news/ahpi-hospitals-to-suspend-cashless-treatment-for-bajaj-allianz-policyholders-from-september-1
- Small hospitals: https://www.accion.org/building-the-financial-rails-for-cashless-healthcare-in-india
- PM-JAY: https://www.business-standard.com/health/haryana-hospitals-to-continue-ab-pmjay-strike-despite-partial-payment-125080601850_1.html ; https://morungexpress.com/nagaland-nhps-urges-private-hospitals-to-continue-ab-pm-jay-cmhis-services ; https://moneylife.in/article/ayushman-bharat-scheme-609-private-hospitals-opted-out-due-to-payment-delays-low-reimbursements-since-2018-says-govt/76783.html
- PM-JAY hackathon: https://www.ocacademy.in/blogs/ab-pm-jay-auto-adjudication-hackathon-2026/ ; https://english.punjabkesari.com/business/indiaai-mission-nha-felicitate-winners-of-ai-hackathon-to-boost-claims-processing-under-ayushman-bharat/
- NHCX: https://nirmitee.io/blog/is-nhcx-mandatory-hospitals-hmis-2026/ ; https://pr.iith.ac.in/pressrelease/NHCX26.pdf ; https://nrces.in/ndhm/fhir/r4/3.1.0/Bundle-ClaimBundle-preauth-example-01.html
- Medi Assist: https://nsearchives.nseindia.com/corporate/MEDIASSIST_09082026195837_MAHSInvestorPresentationAug26.pdf ; https://cxotoday.com/media-coverage/medi-assist-advances-access-to-cashless-healthcare-over-50-of-hospital-pre-authorisations-now-approved-in-under-five-minutes/
- Hospital-side vendors: https://www.digitalhealthnews.com/care-fi-launches-revnow-to-transform-hospital-revenue-management-in-india ; https://bwdisrupt.com/article/insurance-tech-startup-healspan-raises-seed-funding-led-by-lead-angels-536327
- PhilHealth: https://abs-cbn.com/news/business/2025/1/15/philhealth-urged-to-revise-claims-processing-as-denied-claims-pile-up-1646 ; https://tribune.net.ph/2025/01/17/probe-of-p596-b-philhealth-mess-urged ; https://asianews.network/?p=249924
- BPJS: https://www.cnbcindonesia.com/news/20250919195052-4-668643/dipastikan-tepat-waktu-klaim-rs-cair-dari-bpjs-dalam-136-hari ; https://insight.kontan.co.id/news/pending-claim-rumah-sakit-di-tahun-2024-kepada-bpjs-kesehatan-sentuh-triliunan-rupiah
- Vietnam: https://thuonghieucongluan.com.vn/tp-ho-chi-minh-cac-benh-vien-chua-duoc-quyet-toan-gan-2-500-ty-dong-bao-hiem-y-te-a273284.html
- Japan: https://atsoho.com/blog/medical-clerk-receipt-check-ai-assist-compare ; https://www.phchd.com/jp/medicom/park/tech/receip-ai
- Hackathon prior art: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii/manvibuilds/mediclear-ai-agents-that-fight-denials ; https://forum.uipath.com/t/mediauthpro-transforming-healthcare/2874186
- HBP/STG data: https://nha.gov.in/img/resources/HBP-2.2-manual.pdf ; https://pmjay.gov.in/hospital/hbc ; https://sha.uk.gov.in/ScannedDocs/WebSite/Uploads/STAND_TREAT/FAQs-for-STG-Approved.pdf
