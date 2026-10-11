# Regulation-deadline ideas: final round (2026-10-11)

**Brief:** find problems created by new 2025-26 JAPAC rules with hard deadlines, where small actors must produce paperwork or proof. Everything must be demoable on public or synthetic data only. Avoid the ~105 competitor entries and the spaces we already rejected.

**Method:** I generated about 20 candidates and killed them with quick web, GitHub (`gh search repos`) and Devpost checks. Searches were in English, Japanese, Korean and Bahasa. Two finalists were then verified in depth.

## Bottom line

| Rank | Idea | Theme | Weighted (5-pt) |
|---|---|---|---|
| **1** | **HakGig**: a statutory-rights engine for gig drivers and riders under **Indonesia's Perpres 27/2026** (published 8 Oct 2026) and **Malaysia's Gig Workers Act 2025 (Act 872)** | Future of Work (or Social Impact) | **4.08** |
| 2 | **Tranche 2 Deal-File Agent**: AML/CTF due diligence and SMR drafting for small Australian real-estate agencies | BFSI | 3.65 |
| ref | SolventGate (earlier round) / BatchWatch | Manufacturing / Retail | 4.18 / 3.80 |

**HakGig is the only regulation-deadline idea that gets close to SolventGate.** It beats SolventGate on timeliness and user scale, but loses about 0.1 on novelty because of generic gig-appeal apps and the PayProof competitor. Tranche 2 is real and urgent, but the market is already full of vendors.

---

## 1. Long list and quick kills

| # | Candidate (regulation, date) | Verdict | Reason (evidence) |
|---|---|---|---|
| 1 | **ID Perpres 27/2026 (8% platform cap) + MY Act 872 gig-worker entitlement and claims** | **FINALIST** | See §2 |
| 2 | **AU AML/CTF Tranche 2** (in force 1 Jul 2026; enrolment deadline 29 Jul 2026) | **FINALIST (runner-up)** | See §3 |
| 3 | JP Freelance Act (Nov 2024) + 取適法 (1 Jan 2026, which replaces the Subcontract Act and adds 特定運送委託) | Kill | Several public repos already do this: `hiroshi57/subcontract-check` (detects >60-day payment, missing written terms and price cuts, with citations), `katsushi2441/ktoriteki`, `eoylab/jftc-actions` (an MCP server of 361 JFTC actions), `yama-kiyo/freelance-meijisho`, `shusakuhayashi/solodocs`, `geekfujiwara/ProcurementOrderCheckAgent`, plus LegalOn/freee/Money Forward. Japan-only. The enforcement story is strong (Japan Post recommendation 2 Sep 2026, 167 freelancers; Timewitch 236; KADOKAWA; 128 broadcast and ad firms given guidance), but the product is already built |
| 4 | JP カスハラ (customer harassment) duty (in force **1 Oct 2026**) with a Live API role-play trainer | Kill | Crowded: SoftBank SoftVoice, Tokio Marine Talktice (Japan Post Bank adopting Dec 2026), Crystal Method カスハラAIロープレ, iRolePlay |
| 5 | KR Serious Accidents Punishment Act, 5–49-employee firms (since Jan 2024): risk assessment from site photos | Kill | Crowded: 세이프티스냅 (Warmblood × The Planet Safety, Jul 2025), KISA 스마플 2.0, 안전함 (3,000 sites), Busan Port Authority AI risk assessment. Harm is strong (5–49-employee sites = 38.9% of deaths), but the tools exist |
| 6 | JP revised Logistics Act: CLO and 中長期計画 for 特定荷主 (first plan due **end Oct 2026**) | Kill | It targets about 3,200 large shippers, not small ones. NRI and Hitachi consult on it; MOVO Berth and Hacobu already measure 荷待ち |
| 7 | JP revised Building Standards Act (4号特例縮小, Apr 2025): drawing and wall-quantity checks | Kill | AI drawing-review tools already exist (comparison articles from 2026); CAD packages already do wall calculations |
| 8 | JP revised Construction Business Act 標準労務費 (Dec 2025): estimate checker | Kill | Japan-only, mostly arithmetic, low Gemini wow |
| 9 | JP chemical risk assessment (自律的管理; list expanded 2025-26): SDS to CREATE-SIMPLE | Kill | AI-OCR SDS tools exist (AskDona RAG and others); Japan-only; close to SolventGate's ground |
| 10 | JP 育成就労 (starts 1 Apr 2027): training plans | Kill | Too early; operating guidance only came out Feb 2026; immigration-admin SaaS will absorb it |
| 11 | SG Workplace Fairness Act: grievance process | Kill | Commencement pushed to **end 2027** |
| 12 | KR Yellow Envelope Act (10 Mar 2026): "substantive control" assessment | Kill | A legal-opinion product with contested standards and no visual wow |
| 13 | AU Food & Grocery Code (mandatory 1 Apr 2025): fresh-produce rejection disputes | Runner-up 3 (~3.5) | Nice rule: rejection needs written reasons within 24 h (photo vs spec). But GoMicro "Exceed" already makes timestamped QC records for exactly this (FreshPlaza, May 2026: rejections cost up to $47k per load). The Code Supervisor's 2024-25 survey shows improvement (74% "no issues", 419 respondents). Niche |
| 14 | ID Koperasi Desa Merah Putih: business proposal for a Himbara loan (PMK 49/2025) | Kill | Dozens of KDMP repos (POS, microsites, management). Politically flagship. Kemenkop's own systems |
| 15 | IN BIS QCOs | Kill | Volatile: 14+ chemical and polymer QCOs were withdrawn in Nov 2025 |
| 16 | IN MSME 45-day payment (43B(h)) / MSME Samadhaan | Kill | Crowded: `greeshma-ch/msme-samadhaan-assistant`, TrustAudit, msme-45-day-clock, reconcile-ai and others. zerogap (GST) is in the cup |
| 17 | VN Advertising Law 75/2025 (KOL verification, 1 Jan 2026) | Already covered | Covered in `Media idea search/creator_newsroom_compliance.md` (FinClear, with a Vietnam extension) |
| 18 | KR AI Basic Act (Jan 2026) / IN SGI labels | Kill | Already rejected: platform-side work, C2PA/SynthID exist |
| 19 | PH AFASA, AU Scams Prevention Framework | Kill | Scam space (rejected) |
| 20 | ID Coretax, MY e-invoice phases, AU Payday Super (1 Jul 2026), VN household tax | Kill | Tax and payroll vendors are crowded; BFSI is the most crowded theme |
| 21 | IN DPDP consent, IN Labour Code registers, AU aged-care notes | Kill (re-confirmed) | No sharply different angle found |

---

## 2. FINALIST 1: HakGig, a statutory-rights engine for gig drivers and riders (Indonesia + Malaysia)

### The regulations and deadlines (verified)

**Indonesia: Perpres No. 27/2026 on Protecting the Platform-Based Digital Transport Ecosystem**
- Signed 1 May 2026 (May Day speech). The text was **only published on 7–8 Oct 2026**, 3 days ago.
- Platform fee is capped at **8%**. The driver gets **at least 92% of the trip fare** before operating costs. The old split was about 80/20, and under KP 1001/2022 (15% + 5%) actual deductions reportedly "approached 50%".
- Covers passengers, goods and food. Kemenhub sets ojol tariffs, Komdigi sets delivery tariffs, and the UMKM ministry oversees partnership agreements. A joint three-ministry task force will be set up.
- Drivers get rights to **clarity of fee structure and algorithm transparency**. Platforms must run a complaint service that **responds within 7 days**. BPJS health, work-accident and death cover is mandatory.
- **Six-month transition** for platforms to fix partnership agreements, transaction-recording systems and income transparency, which runs to about Apr 2027. Implementing regulations are due by **31 Dec 2026**.
- The minister has publicly admitted "perbedaan penafsiran" (different interpretations) among drivers of how to calculate the split (detik, 7 Jul 2026). Grab said it applied 8% from 1 Jul 2026, and Gojek is "studying" it.
- Scale: Grab alone has about 3.7M registered partners (700–800k monthly active). A union counted **6M ojol drivers who did not receive the 2026 holiday bonus (BHR)**; only about 850k got it.

**Malaysia: Gig Workers Act 2025 (Act 872)**, in force **31 Mar 2026**, covering 1.64M gig workers. Subsidiary regulations are P.U.(A) 143–146/2026.
- s.3: the service agreement must list parties, period, service, obligations, **rate and details of earnings**, and payment method.
- s.11: earnings must be paid **within 7 days** of service completion if the agreement is silent.
- s.12: deductions are allowed only for overpayment (within the past 3 months), legal authority or DG approval.
- **s.14: a suspension for inquiry can last at most 14 days, with written notice. If no cause is found, the worker is reactivated and paid half of average daily earnings as compensation.** The worker has a right to be heard.
- s.17: the internal grievance must be resolved within **30 days**. **P.U.(A) 146: conciliation must be filed within 60 days** of the dispute or decision. After that, the case goes to the Gig Workers Tribunal (P.U.(A) 144, 30 days' notice of hearing).
- s.108 general penalty: up to RM50k or 2 years. The MOHR **e-Aduan Gig** portal opened 1 Apr 2026, for income, account suspension and agreement-breach complaints, with a 21-working-day target.
- The **first Tribunal hearing was on 1 Sep 2026** (e-hailing driver v GrabCar Sdn Bhd; saver trips, cashback, advance booking), and it was adjourned for more evidence. **The evidence problem is real.**

### Named user (role)
- **Pak Budi**, an ojol motorbike driver in Bekasi who does about 15 trips a day. His evidence is trip-detail screenshots. He cannot tell whether he is getting 92%.
- **Encik Hafiz**, a p-hailing rider in Kuala Lumpur. He has been suspended for 19 days, and his evidence is the notification screenshot plus support chats.
- Secondary user: a driver-association paralegal (Garda Indonesia, or a Malaysian rider association) who handles many cases.

### Harm with numbers
- At Rp25,000 per trip, an 8% cut leaves the driver Rp23,000. A 20% cut leaves Rp20,000. **That is Rp3,000 per trip, or about Rp1.1M a month at 15 trips a day over 25 days**, which is significant against ojol incomes.
- Malaysia s.14: each unlawful day of suspension past day 14 is lost income, plus statutory compensation. The **60-day conciliation clock** is a hard bar that a worker can miss without knowing it.
- Scale: about 6–7M Indonesian ojol drivers (union and BHR figures) plus 1.64M Malaysian gig workers.
- Gap: no driver-side tool computes legal entitlement. Platforms publish their own explanations, and the minister asked platforms to "explain more".

### Public templates and data (all public or synthetic)
- Official texts: Perpres 27/2026 (JDIH Setneg / peraturan.go.id), Act 872 plus P.U.(A) 143–146/2026, the MOHR Act 872 briefing slides (mohr.gov.my), and the e-Aduan Gig categories. Also KP Menhub 1001/2022 for the old regime.
- Synthetic data:
  - About 60 trip-detail and weekly-payout screenshots from a **fictional platform ("JalanKu")**, with noisy phone captures, Bahasa labels, promos and tips. Half are seeded with an over-cap fee or a hidden "biaya layanan".
  - A synthetic suspension notice, support chat and earnings history for the Malaysia case.
- **No Grab or Gojek branding** (avoids impersonation).

### 3-minute demo: the "wow moment"
1. Pak Budi drops 30 screenshots. Gemini reads each one, and a ledger table fills in with fare, platform fee, promo and tip per trip, with low-confidence cells flagged.
2. **Wow:** the code engine shows that the effective platform take is **14.6%** on 9 of the 30 trips. It shows both readings side by side: "fee on fare before promo" vs "fee on fare after promo". Each reading carries a citation chip that opens the exact Perpres 27/2026 article. Shortfall: **Rp41,250 this week**.
3. One tap builds the complaint to the platform, with the 7-day response clock started, and an escalation pack for the task force or association.
4. Switch to Malaysia. Hafiz *speaks* in Malay through the **Live API** ("akaun saya digantung 19 hari...").
   - The agent asks for the notice screenshot and reads the dates.
   - A timeline shows "Day 15: s.14 limit breached".
   - It computes **s.14 compensation = ½ × average daily earnings × days**, using his earnings screenshots.
   - It shows a **60-day conciliation countdown** and drafts the e-Aduan text and conciliation statement in Malay and English, with section citations.

### Gemini features
- Multimodal batch extraction with a structured schema.
- **Live API voice** in Bahasa Indonesia and Malay.
- Function calling into a **deterministic entitlement engine**: fee-cap math, s.14 compensation, s.11 7-day payment, s.12 deductions and the deadline clocks. **The LLM never does arithmetic.**
- Grounding with clause-level citations, using Vertex AI Search or File Search over the official PDFs.
- Agentic case-building: evidence, then timeline, then breaches, then the filing pack.
- Gemma optional for on-device redaction of names and plates.
- Deploy: Cloud Run plus Firebase Hosting and Auth.

### 7-day buildability (2 people)
| Day | Work |
|---|---|
| D1 | Synthetic screenshot generator (HTML templates rendered to PNG with noise) and law-text corpus |
| D2 | Extraction schema plus eval on 60 images |
| D3 | Entitlement engine plus unit tests |
| D4 | Grounded citation layer |
| D5 | Live API Malay flow |
| D6 | Filing-pack PDF, UI polish and deploy |
| D7 | Video and deck |

- Risk: implementing regulations (due 31 Dec 2026) may fix the calculation basis. That is mitigated by the "two interpretations" feature, which is an honest differentiator.
- Risk: PayProof-style extraction accuracy. Mitigation: have the user confirm cells (PayProof's own eval found confident wrong values).

### Novelty verdict: **partly open (open on the statutory angle)**
- GitHub: **0 repos** for Perpres ojol, ojol potongan or Act 872 / Gig Workers Act Malaysia. Most "ojol" repos are community sites and finance trackers.
- Generic gig-rights prior art:
  - Devpost **GigShield**: India deactivation appeal letters, built with Baidu MeDo.
  - `vishwabandhukn/Gig-Workers-Rights-VerificationSystem`: US-style appeal letters and an evidence locker.
  - `nkgaurdev/NyayaAI`: gig contract clause risk.
  - Grab's own Malaysia Gig Hub.
- **In-cup competitor PayProof** (`nithinraj49/payproof`): India, English only. It computes true hourly pay after costs from gig screenshots with Gemini plus fixed formulas. It does **no law, no jurisdiction and no filing**. That overlaps on mechanics, so the pitch must say "PayProof tells you what you earn; HakGig tells you what you are *owed by law* and files the claim".
- No product found that computes **Perpres 8% compliance** or **Act 872 s.14 compensation and conciliation deadlines**.

### Scores
| Criterion | Weight | Score | Why |
|---|---|---|---|
| Technical & GenAI | 40% | 4.5 | Multimodal batch, Live API, tool-calling engine, clause grounding, agentic filing |
| Problem & Impact | 25% | 4.0 | 6–7M + 1.64M workers, a law 3 days old, the first tribunal case; lacks MY deactivation statistics |
| Innovation | 25% | 3.5 | Statutory entitlement engine is new; generic appeal apps and PayProof reduce it |
| UX | 10% | 4.0 | Phone-first, voice, Bahasa, one-tap pack |
| **Weighted** | | **4.08** | |

---

## 3. FINALIST 2: Tranche 2 Deal-File Agent (AU real estate AML/CTF)

### Regulation and deadline
- AML/CTF Amendment Act 2024 plus AML/CTF Rules 2025 (Aug 2025).
- **Obligations from 1 Jul 2026** for about 80–100k newly regulated businesses: real estate agents, conveyancers, lawyers, accountants, TCSPs and precious-metal dealers.
- **Enrolment deadline was 29 Jul 2026.** At that date, about 50% of accounting practices, **about 40% of real estate agencies**, 12–14% of law firms and about 10% of jewellers had enrolled (Clyde & Co).
- **From 28 Aug 2026, AUSTRAC began issuing s.167 notices**, with response windows as short as 14 days. Ignoring one is a criminal offence (up to 6 months' jail or 30 penalty units).
- Visibl survey (61 firms, 31 Jul–10 Aug 2026): **18% had not done the ML/TF risk assessment**; 65.6% think they would pass a review, but only 34.4% are actually ready.
- Reporting duties:
  - TTR for cash of A$10k or more within 10 business days.
  - SMR when a suspicion is formed.
- AUSTRAC's 2024 National Risk Assessment rates real estate as **very high vulnerability**.

### Named user
**Sarah**, principal of a 6-person real-estate agency in Box Hill, VIC, who is also the compliance officer.

### Public templates and data
- AUSTRAC Real Estate **Program Starter Kit** (Jan 2026) and the real-estate risk-assessment template, which was **updated Aug 2026** with a superseded version still online.
- Tranche 2 obligations factsheet, AML/CTF Rules 2025 and the 2024 money-laundering National Risk Assessment.
- DFAT Consolidated Sanctions List (a public XLSX) and the ABN Lookup API.
- Synthetic deal file: contract of sale, synthetic IDs, a trust deed with a corporate trustee, a company extract and a deposit paid from a third-party overseas account.

### 3-minute demo wow
1. Drop the messy deal folder. Gemini reads 9 documents and builds the **ownership graph**: buyer, trust, corporate trustee, director, then a beneficial owner.
2. Tool calls: ABN Lookup shows the trustee company was registered 3 weeks ago, and a DFAT list check returns a near-match.
3. The agent flags 4 indicators, each cited to AUSTRAC guidance.
4. It decides that enhanced due diligence plus an SMR are needed, and drafts the SMR fields with the clause trail.
5. Separately, it fills the starter-kit risk assessment from the agency's synthetic ledger.

### Gemini features
Multimodal document reading, agentic tool use, clause-level grounding, structured SMR output. Deploy on Cloud Run.

### Buildability
Feasible in 7 days. Synthetic documents are easy to make; the DFAT list and ABN Lookup are free.

### Novelty verdict: **largely done (commercially crowded)**
- Vendors: First AML (a REIA partner), **AML Partners** (more than 300 property firms signed in 4 months), Real Time Agent (automated CDD), **Arctic Kickstart** (starter-kit-aligned risk assessment and program), InfoTrack, Persona, didit, NameScan, Zyphe, Legl, plus AUSTRAC's own "Check if you may be regulated" tool.
- In the cup, **SafeGlobe** (KYC, sanctions and ownership graph) overlaps the core visual.
- No hackathon entry is specific to Tranche 2 real estate (GitHub and lablab: 0), but judges will see "KYC agent" in BFSI, the most crowded theme (about 27 entries).

### Scores
| Criterion | Weight | Score |
|---|---|---|
| Technical & GenAI | 40% | 4.5 |
| Problem & Impact | 25% | 4.0 |
| Innovation | 25% | 2.0 |
| UX | 10% | 3.5 |
| **Weighted** | | **3.65** |

---

## 4. Recommendation
- If the team wants a regulation-deadline idea, **build HakGig**.
  - Lead with the Indonesia Perpres. It is 3 days old as of this research, a national story with presidential ownership, and has 6M+ drivers.
  - Use Malaysia Act 872 as the second jurisdiction, because it carries the hard statutory clocks (14-day, 30-day and 60-day) and the Live-voice demo.
  - Theme it **Future of Work**: about 19 entries there, and no gig-law entry.
  - Name PayProof directly in the submission and draw the line between them.
- Compared with SolventGate (4.18), HakGig (4.08) is within the noise. HakGig wins on timeliness, user scale and the Live-voice UX. SolventGate wins on novelty and on being in the least-crowded theme.
- Avoid Tranche 2 unless there is a sharply new angle, for example an s.167-notice responder. Vendors will be judged against it.

## Sources (key)
- Perpres 27/2026 publication and contents:
  - https://nasional.kontan.co.id/news/resmi-diterbitkan-cek-poin-poin-penting-perpres-nomor-27-tahun-2026-tentang-ojol
  - https://transportasimedia.com/detail/21866/resmi-terbit-perpres-no-27-tahun-2026-batasi-potongan-aplikasi-ojol-maksimal-8-persen
  - https://nasional.kompas.com/read/2026/10/08/10211981/pemerintah-akhirnya-terbitkan-perpres-ojol-atur-tarif-hingga-jaminan-sosial
  - https://malang.disway.id/nasional/read/24154/perpres-ojol-2026-terbit-atur-tarif-penumpang-antar-barang-makanan-hingga-biaya-platform-8
  - https://umkm.go.id/news/rowvqp5scf319fhokcha84co
- Interpretation dispute: https://finance.detik.com/berita-ekonomi-bisnis/d-8563654/aplikator-sudah-terapkan-potongan-driver-ojol-8-menhub-bilang-begini
- Grab 8% from 1 Jul: https://www.idnfinancials.com/id/news/65148/grab-terapkan-bagi-hasil-8-untuk-mitra-ojol-mulai-1-juli-2026
- Driver numbers:
  - https://ekonomi.bisnis.com/read/20260314/98/1960459/serikat-pekerja-catat-6-juta-pengemudi-ojol-tak-terima-bhr-2026
  - https://ekonomi.bisnis.com/read/20260303/12/1957251/850000-driver-gojek-grab-cs-dapat-bhr-ojol-cair-h-7-lebaran
- Old regime ("approaching 50%"): https://katadata.co.id/digital/startup/6a8c46fa2cc36/beda-dengan-ri-kemitraan-ojol-di-malaysia-dan-singapura-diatur-kemenaker
- Act 872 text summary: https://lawplayer.com/my/act/act-872
- Act 872 subsidiary regulations: https://www.skrine.com/insights/alerts/april-2026/gig-workers-act-2025-and-related-subsidiary-legisl
- Act 872 commencement: https://www.thevibes.com/articles/news/121349/gig-workers-act-2025-comes-into-force-to-safeguard-1.64-million-platform-based-employees
- First tribunal: https://www.humanresourcesonline.net/malaysia-s-gig-workers-tribunal-hears-first-case
- e-Aduan Gig: https://www.utusan.com.my/nasional/2026/03/pekerja-gig-boleh-buat-aduan-berkaitan-di-platform-eaduan/
- PayProof: https://github.com/nithinraj49/payproof
- GigShield: https://devpost.com/software/gigshield-pnk4od
- Tranche 2 timeline and numbers:
  - https://www.clydeco.com/en/insights/2026/08/austrac-takes-compliance-action-in-relation-to-tra
  - https://newshub.medianet.com.au/2026/10/a-month-after-the-compliance-deadline-one-in-five-newly-regulated-businesses-still-havent-done-the-single-most-foundational-aml-anti-money-laundering-task/174432/
  - https://withpersona.com/blog/tranche-2-australia
- Tranche 2 starter kits:
  - https://www.austrac.gov.au/news-and-media/media-release/austrac-backs-newly-regulated-sectors-release-amlctf-program-starter-kits
  - https://www.austrac.gov.au/sites/default/files/2026-06/Real_estate-Risk_assessment.docx
- Tranche 2 vendors:
  - https://itbrief.com.au/story/aml-partners-signs-300-firms-as-property-rules-tighten
  - https://arctic-intelligence.com/platforms/kickstart
  - https://agent.domain.com.au/all-stories/real-time-agent/real-time-agent-is-partnering-with-aml-ctf-customer-due-diligence-providers
- JP Freelance Act enforcement:
  - https://www.lnews.jp/2026/09/s0902505.html
  - https://www.gamebusiness.jp/article/2026/06/11/27187.html
  - https://www.sakigake.jp/news/article/20251210CO0082/
- 取適法 transport: https://atsoho.com/blog/transport-resubcontract-owner-driver
- カスハラ effective date and products:
  - https://www.freee.co.jp/kb/kb-trend/customer-harassment-measures/
  - https://www.softbank.jp/business/content/blog/202605/customer-harassment-softvoice
  - https://crystal-method.com/blog/kasuhara-ai-customer/
- Logistics CLO timeline: https://www.nri.com/jp/media/column/mcs_blog/20260615.html
- KR SAPA:
  - https://newstomato.com/ReadNews.aspx?no=1163490
  - https://www.unicornfactory.co.kr/article/2025070717014984442
- SG WFA end-2027: https://www.hsfkramer.com/notes/employment/2025-posts/singapore-workplace-fairness-act-to-take-effect-end-of-2027
- KR Yellow Envelope 10 Mar 2026: https://www.lawtimes.co.kr/news/213626
- 育成就労: https://kumanichi.com/articles/1902918
- 4号特例 AI tools: https://atsoho.com/blog/building-code-inspector-ai-drawing-review-comparison
- Grocery Code:
  - https://grocerycodesupervisor.gov.au/sites/grocerycodesupervisor.gov.au/files/2026-06/food-grocery-code-supervisor-annual-report-2024-25.pdf
  - https://www.freshplaza.com/asia/article/9835149/the-47k-problem-behind-every-rejected-load-of-spinach/
- KDMP: https://ekonomi.bisnis.com/read/20250728/12/1896887/syarat-dan-cara-koperasi-desa-merah-putih-dapat-pinjaman-rp3-miliar-dari-bank
- BIS QCO withdrawals: https://visionias.in/current-affairs/upsc-daily-news-summary/article/2025-11-14/business-standard/polity-and-governance/no-bis-certification-required-qcos-for-plastics-synthetic-fibres-scrapped
