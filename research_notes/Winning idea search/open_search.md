# Open search: can anything beat BatchWatch? (2026-10-11)

**Method:** I read IDEA.md, MEDIA_IDEA.md, COMPETITOR_ENTRIES.md (~105 entries), the winners file and the research_notes headings. Then I generated about 15 candidates, killed most of them quickly, and ran the survivors through web search (English plus Bahasa Indonesia), `gh search repos` and Devpost/lablab queries.

**Bottom line:** one idea beats BatchWatch on paper: **SolventGate**, a receiving-gate check for pharma excipients at MSME syrup makers, in the Manufacturing theme. It wins on the 40% technical criterion and on theme crowding. It ties on impact and loses a little on UX and on how many users it has. The margin is about 0.4 points on a 5-point scale. That is a real lead, but not a landslide.

---

## 1. Candidate long list and quick kills

| # | Candidate | Theme | Kill / keep reason |
|---|---|---|---|
| 1 | **SolventGate**: an MSME pharma QA gate that checks propylene glycol/glycerin/sorbitol drums, CoAs and invoices for DEG risk and forgery (India + Indonesia) | Manufacturing | **KEEP → top 3** |
| 2 | **KLB Kit**: a food-poisoning outbreak investigation copilot for Puskesmas, covering MBG school-meal outbreaks (Indonesia) | Sustainability/Social | **KEEP → top 3** (partly taken, see §2) |
| 3 | **Wajib Halal Copilot**: SJPH self-declare dossier for Indonesian micro and small businesses (UMK); the deadline is 17 Oct 2026 | Retail | **KEEP → top 3, then killed in verification** (AMANA, AMINRA, BPJPH's own AI pre-check) |
| 4 | Sec-105 Check: Gemini watches a police search-and-seizure video and audits BNSS §105 / NDPS §52A compliance, then drafts the seizure memo | Social/FoW | Runner-up. Very Gemini-native (long video, Hindi audio). Allahabad HC rebuked UP police in Aug 2026. But courts say the real problem is that no video gets recorded at all, so AI doesn't fix the root cause. The harm is hard to quantify and the police-tool framing is sensitive |
| 5 | MBG kitchen AI CCTV / SOP monitor | Social | Killed: IFSR + KBI launched an AI-CCTV product for SPPG kitchens (2026), BGN is centralising CCTV, and many SPPG repos exist (MBG-Smart-Logistics uses Gemini for delivery windows) |
| 6 | Spurious pesticide label check (India) | Sustainability | Killed: the Insecticides (Amendment) Rules 2025 mandate QR codes on every label (Aug 2025), so the government channel now covers authentication. Harm numbers are weaker than for medicines |
| 7 | EUDR smallholder geolocation dossier (deadline Dec 2026) | Sustainability | Killed: Koltiva, Satelligence, Agridence, TraceX, Farmforce. Crowded |
| 8 | Vietnam household-business tax switch (lump-sum tax abolished Jan 2026) | BFSI | Killed: MISA, KiotViet, Sapo and Viettel already ship tools, and BFSI is the most crowded theme |
| 9 | India DPDP Rules consent-notice copilot | FoW | Killed: privacy-tech vendors are crowded, and the demo isn't exciting |
| 10 | Korea AI Basic Act (Jan 2026) / India SGI-label rules (Feb 2026) compliance | Media | Killed: the work sits on the platform side, there's no named small user, and C2PA/SynthID already exist |
| 11 | Australia Aged Care Act (Nov 2025) documentation | FoW | Killed: AI care-notes tools are crowded |
| 12 | India Labour Codes (Nov 2025) MSME registers | FoW | Killed: HR SaaS (greytHR etc.) already does this |
| 13 | Unclaimed assets recovery ("Your Money, Your Right" campaign, ₹1.84 lakh cr) | BFSI | Killed: BFSI is crowded (~27), IEPF claim consultants exist, and there's no visual wow |
| 14 | Japan Foods-with-Function-Claims dossier check (after the beni-koji deaths) | Retail | Killed: Japan-only, Japanese-only, a niche regulatory desk, and the judges are pan-JAPAC |
| 15 | Hong Kong scaffold-net / renovation fire-safety check (after the Wang Fuk Court fire, Nov 2025) | Manufacturing/Social | Killed: no public demo data and too HK-specific to build in 7 days |
| 16 | SIR electoral-roll helper (India) | Social | Killed: politically radioactive for a Google-judged event |

Also excluded per brief: scams, generic RAG, notetakers, predictive maintenance, audio description, disaster command, ESG, consumer fact-check, shift handover, CBAM.

---

## 2. Deep verification of the top 3

### A. SolventGate: the excipient receiving gate for MSME syrup makers (Manufacturing)

**User:** Priya, the one-person QA officer at a 40-person liquid-oral MSME in Baddi or Solan. Drums of propylene glycol arrive from a trader with a 1-page CoA and an invoice.

**Harm (quantified, current):**
- **Indonesia 2022:** more than 200 child deaths. The trader CV Samudera Chemical **downloaded Dow Chemical Thailand's logo from the internet**, stuck it on drums of ethylene glycol and sold them as PG; BPOM found 91–100% EG. ([Fox/Reuters](https://www.foxnews.com/health/indonesia-local-trader-forged-ingredient-label-led-cough-syrup-deaths-200-kids), [news24 court papers](https://www.news24.com/world/indonesian-court-papers-reveal-chain-of-events-that-led-to-200-cough-syrup-deaths-20231123))
- **India 2025 (Coldrif):** 24 children died in MP and Rajasthan from 48.6% DEG. Sresan bought 50 kg of PG from distributor Sunrise Biotech, which had bought it **the same day** from Jinkushal Aroma, a maker of fragrance blends for detergents. The PG was non-pharma grade and **never tested for DEG/EG**. Inspectors found 39 critical and 325 major violations. ([Tribune](https://www.tribuneindia.com/news/india/cough-syrup-deaths-drug-regulator-flags-lapses-in-testing-raw-material), [thenews/Reuters](https://www.thenews.pk/story/1381942-india-probes-safety-lapses-in-cough-syrup-supply-linked-to-24-child-deaths))
- **Total since 2022:** more than 300 children dead in Gambia, Indonesia and Uzbekistan, plus India in 2025 (WHO).
- **Telangana DCA:** seized excipient drums with **fabricated labels naming a manufacturing site that doesn't exist** ([Siasat](https://www.siasat.com/dca-seizes-pharmaceutical-excipient-worth-rs-70-56-l-in-alwal-3488029/)).

**New rules creating demand right now:**
- **Oct 2025:** the CDSCO directive says every batch of excipient must be tested before use, with a robust vendor-qualification system ([Medical Dialogues](https://medicaldialogues.in/news/industry/pharma/cdsco/after-cough-syrup-deaths-cdsco-tightens-oversight-on-drug-testing-compliance-156572)).
- **22 Oct 2025:** the ONDLS digital monitoring system went live for PG, glycerin and sorbitol. Pharma-grade solvent makers must upload batch-wise CoAs and their distribution ([CliniExperts](https://cliniexperts.com/regulatory-update/digital-monitoring-system-on-the-ondls-portal-for-monitoring-the-supply-chain-of-high-risk-solvents/)).
- **IP 2022 amendment:** DEG/EG testing of oral liquids before release is mandatory.
- **Revised Schedule M binding since 1 Jan 2026:** only ~26% of ~8,500 MSMEs filed upgrade plans, leaving **~6,300 units at licence risk**. Supplier qualification and computerised traceability are now required ([Laafon](https://laafon.com/?p=6455)).
- **Indonesia:** BPOM requires supplier qualification and testing **on every arrival and every container** ([BPOM](https://www.pom.go.id/berita/bpom-rilis-kembali-daftar-sirup-obat-aman-di-indonesia-penegakan-hukum-bagi-industri-yang-melakukan-pelanggaran)).

**Existing products and the gap:**
- Generic CoA extraction and spec comparison exists: IBM + AWS SAP CoA validation for big pharma, Algoscale DocumentIQ, Kognitos, a GitHub Gemini CoA extractor, and the PCoAD dataset. Pep Trust scores peptide CoAs for forgery, but only in the US grey market.
- **Nobody** combines these for an MSME receiving gate: (1) drum-label photo vs. the genuine manufacturer's label/CoA template, (2) supplier provenance via grounded web search ("this 'supplier' is a detergent-fragrance maker"), (3) chain-of-custody logic (same-day resale, quantity, dates), (4) a DEG/EG presence and limit check against the IP/USP monograph, and (5) output of the quarantine label, sampling plan, GC test request and Schedule-M deviation/vendor record.
- Searches found no hackathon prior art: GitHub "propylene glycol", "certificate of analysis", "excipient", "diethylene glycol"; Devpost/lablab "cough syrup DEG".

**In this hackathon:** Manufacturing is the **least crowded theme** (~11 entries). Its entries are about predictive maintenance, root cause analysis (RCA), handover and visual QC. **None touches pharma or raw materials.**

**Demo (3 min):**
1. 300+ children since 2022, two real supply chains on screen.
2. Priya photographs a drum label, a CoA and an invoice.
3. Gemini extracts them, then a deterministic spec check runs.
4. **Wow moment:** a replay of the Indonesian case. The "Dow" label is compared against a genuine Dow PG label and CoA reference, and the logo, batch-code format and plant address don't match. Grounded search identifies the seller as a soap-ingredient trader. A second replay of Coldrif shows the same-day trader-to-trader resale flagged and the DEG/EG result missing. The verdict is **HOLD: quarantine + mandatory GC test**, never "safe".
5. One tap produces the quarantine tag, the sampling plan, the deviation record and a vendor-disqualification note. The state drug inspector sees every gate decision.

**Data:** public genuine CoAs (Dow, Sigma-Aldrich and similar PG/glycerin USP CoAs), IP/USP monograph limits (DEG/EG ≤ 0.10%), CDSCO NSQ lists (syrups failing DEG), and synthetic forgeries rebuilt from the documented cases. ONDLS needs a login, so it is mocked.

**Risks:**
- The real safeguard is the GC test, and AI cannot replace it. Pitch SolventGate as "it makes sure the test happens and the paper trail is real".
- Visual forgery detection on a logo is unreliable on its own, so back it with deterministic checks and a reference library, and show a confidence score.
- The domain is niche for judges: open on the dead children, not on GMP jargon.
- Credibility: find a pharmacist or QA advisor and quote them.
- The user base is smaller than BatchWatch's (about 10k manufacturers vs 1.24M chemists).

### B. KLB Kit: food-poisoning outbreak investigation copilot (Indonesia MBG)

**Harm:** **5,482 victims in 71 MBG incidents from 62 kitchens between 22 Jul and Sept 2026**, out of 27,022 active SPPG kitchens. BGN says more than 80% came from SOP breaches, for example food cooked at 00:00 and eaten after 12:00 ([Katadata](https://katadata.co.id/berita/nasional/6a9a5b8dc9d81/5482-korban-keracunan-mbg-sejak-akhir-juli-2026-bgn-soroti-pelanggaran-sop)). Single outbreaks hit 566 people (Sidoarjo), 424 (Pati) and 411 (Batang). Kemenkes plans routine reporting "like during Covid".

**Concept:** a Puskesmas surveillance officer gets 400 sick children. Gemini Live interviews cases and parents in Bahasa, photos of menus and attendance lists feed in, and a **deterministic** attack-rate, relative-risk and epi-curve engine finds the suspect dish and the likely pathogen from the incubation period. The kitchen's cook-to-eat timeline comes in, and it drafts the PE/KLB report for human sign-off.

**Prior art:** **EpiFlow** (kzhanar/epiflow, a human-led AI outbreak-investigation framework) and a Chinese "食源性疾病暴发调查助手" (YRM-crypto/foodborne-outbreak-skill) use the *same* architecture (deterministic stats + LLM narrative + audit log). UKHSA has trialled LLMs on restaurant reviews. There are many Indonesian MBG/SPPG repos and an AI-CCTV product, so Indonesian teams in this hackathon may well enter MBG too. Politically sensitive: MBG is the President's flagship.

**Verdict:** the impact is excellent and the Live API makes it technically strong, but the **innovation is diluted** and so is MBG crowding.

### C. Wajib Halal Copilot (Indonesia)

**Urgency:** the halal-certification deadline for UMK food and beverage products ends **17 Oct 2026**, the day before submission; it becomes mandatory on 18 Oct. About **15.4M UMK** remain uncertified and there are only 1.35M free SEHATI quotas ([Kompas](https://www.kompas.tv/info-publik/646130/oktober-2026-wajib-halal-berlaku-ini-daftar-produk-yang-harus-bersertifikat), [BCA Sekuritas](https://bcasekuritas.co.id/latest-news/news/bpjph-buka-kuota-135-juta-sertifikat-halal-gratis-2026-bagi-umk)).

**Prior art (killed):**
- **AMANA** (hmhhmm/AMANA): an AI assistant that takes Malaysian SMEs through JAKIM certification, including the documents, with a demo video.
- **AMINRA** Halal Certification AI Platform.
- BPJPH's SiHalal already has AI document pre-checks and the "Lapor BABE" chatbot, and JAKIM is building its own AI.
- Consumer ingredient checkers are everywhere, including Halal Food AI on Gemini.
- A Halal-Self-Declare-untuk-UMK repo exists.

The harm is economic, not lives. **Killed.**

---

## 3. Scored comparison (1–5; weights 40/25/25/10)

| Criterion (weight) | BatchWatch | **SolventGate** | KLB Kit | Wajib Halal |
|---|---|---|---|---|
| Technical & GenAI (40%) | 3.5: invoice/strip OCR + fuzzy match + ADK. Solid but standard extract-and-match | **4.5**: cross-document multimodal forensics (label vs. reference, CoA vs. monograph, invoice chain), Google Search grounding for provenance, deterministic guardrails, ADK agents | 4.5: Live API voice interviews, multimodal intake, deterministic epi engine, report agent | 3.0: form/dossier generation and ingredient lookup |
| Problem & Impact (25%) | 4.5: 1.24M chemists, ~250 NSQ batches a month, WHO 1-in-10 | 4.5: more than 300 children dead since 2022 in two JAPAC countries; four new rules from Oct 2025 to Jan 2026; ~6,300 MSMEs at licence risk. Fewer users | 4.5: 5,482 victims in ~10 weeks of 2026, 27k kitchens | 3.5: 15.4M UMK and a hard deadline, but only economic harm |
| Innovation (25%) | 3.5: MedShield and Credo do single-batch lookups; stock-wide + paperwork is new | 4.0: generic CoA AI exists in big pharma; provenance + forgery + chain logic for MSMEs is new; no hackathon prior art | 3.0: EpiFlow and a Chinese copy share the architecture; MBG is crowded in Indonesia | 2.0: AMANA, AMINRA, BPJPH AI |
| UX (10%) | 4.0: photo-first, Hindi/English, one-tap | 3.5: a QA desk flow, fine but professional | 4.0: voice-first | 4.0 |
| **Weighted** | **3.80** | **4.18** | **4.00** | **3.05** |
| Theme crowding (not scored, matters for "ranked across all themes") | Retail ~15 | **Manufacturing ~11, none in pharma** | Sustainability ~25, plus Indonesian MBG teams likely | Retail ~15 |

**The honest read:** SolventGate beats BatchWatch mainly on the 40% technical weight. Its centrepiece is reasoning across several documents plus grounded search, which is harder and more Gemini-native than OCR-then-match. It also sits in the emptiest theme and has a more dramatic real-case replay. BatchWatch is still better on breadth of users, ease of explaining it, and UX. If the team has no one with a pharmacy or QA background and can't get an advisor quote, the gap narrows to almost nothing. In that case BatchWatch is the safer pick, because its domain is easier to explain.

## 4. Recommendation
1. **Switch to SolventGate if** within a day you can (a) collect 5–10 genuine public PG/glycerin CoAs and labels as references, and (b) get one pharmacist or QA person to sanity-check the gate logic and give a quote. Pitch: *"In 2022 a trader downloaded Dow's logo and killed 200 Indonesian children. In 2025 a detergent-fragrance PG killed 24 Indian children. SolventGate stops the drum at the factory gate."*
2. **Otherwise keep BatchWatch.** You can borrow SolventGate's best idea into it: Google Search grounding plus a "replay a real case" wow moment.
3. Both products sit on the same medicine-safety chain (factory gate → chemist shelf), so the CDSCO NSQ parsing work is reusable either way.

## Sources (beyond those inline)
- MBG AI-CCTV: [Antara](https://megapolitan.antaranews.com/berita/418621/peluncuran-sistem-cctv-ai-oleh-ifsr-dan-kbi)
- Allahabad HC on §105 BNSS: [LiveLaw](https://www.livelaw.in/high-court/allahabad-high-court/allahabad-high-court-police-non-compliance-section-105-bnss-videography-search-seizure-547230)
- Pesticide QR mandate: [QRCodeChimp summary](https://www.qrcodechimp.com/india-mandates-qr-codes-on-insecticide-labels/)
- CoA AI prior art: [Kognitos](https://www.kognitos.com/blog/certificate-of-analysis/), [Algoscale](https://documentiq.algoscale.com/blog/automating-certificate-of-analysis-coa-extraction-pharma-chemical-manufacturing), [PharmTech "don't trust, verify"](https://www.pharmtech.com/view/certificates-analysis-don-t-trust-verify)
- GitHub repos checked: kzhanar/epiflow, YRM-crypto/foodborne-outbreak-skill, hmhhmm/AMANA, Theology26/MBG-Smart-Logistics-FullDev, Alonso10102000/lab-pdf-data-extractor, xuyimingscnu/PCoAD
