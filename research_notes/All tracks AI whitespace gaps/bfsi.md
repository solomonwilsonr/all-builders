# BFSI whitespace gaps in JAPAC (2025-2026) for the Google Cloud AI Builder Cup 2026

Scope: Theme "BFSI: Intelligent Risk, Fraud & Financial Experiences". Stack: Gemini/Gemma on Cloud Run/Firebase, a team of 2-4 with about 10 days. Judging weights: Technical/GenAI 40%, Impact 25%, Innovation 25%, UX 10%.
Research date: 2026-10-07. About 17 web searches were run. Most figures come from search-result summaries of news and regulator coverage, and few primary PDFs were opened in full. Each figure is tagged with the URL it came from.

---

## Q1. Which GenAI BFSI areas are saturated (the "crowded, avoid" list)?

### Takeaway
Avoid anything a funded vendor already sells to banks as a turnkey API: KYC/OCR and deepfake liveness, generic transaction fraud scoring, scam-message checkers that warn before a scam happens, and generic chatbots. The open space is after a scam has happened, at small or rural institutions, and on the consumer/advocate side of insurance and claims.

### Cited Findings
- **Deepfake / KYC liveness is crowded.** HyperVerge sells "DeepfakeSafe", which detects deepfakes during passive liveness checks and is certified to ISO 30107-3 Level 2. It claims more than 1B identities verified across 450+ companies — [HyperVerge](https://hyperverge.co/); [Surepass roundup of Indian deepfake-detection API vendors, including IDfy and Signzy](https://surepass.io/blog/best-deepface-detection-api-providers-in-india/)
- Demand for deepfake/KYC detection is real but already served. Sumsub reports deepfake cases up 1,500% in Singapore and 1,900% in Hong Kong, synthetic ID document fraud up 233% in APAC, and synthetic personal data at 15.7% of APAC fraud attempts — [Fintech News SG](https://fintechnews.sg/122644/security/apac-deepfake-fraud-2025/); [Crowdfund Insider on Sumsub](https://www.crowdfundinsider.com/2025/06/242027-ai-powered-fraud-soars-in-apacs-healthtech-fintech-sectors-sumsub/)
- **Scam-message and call checkers that act before a scam are crowded, including by Google itself:**
  - Singapore's government app ScamShield checks, blocks and reports scam calls and SMS — [GovTech ScamShield](https://www.tech.gov.sg/products-and-services/for-citizens/scam-prevention/scamshield/)
  - Trend Micro ScamCheck/Check lets users submit messages, ads and posts for a verdict. Its 2025 "Scam Radar" adds real-time alerts — [Trend Micro 2024](https://trendmicro.com/en_sg/about/newsroom/press-releases/2024/2024-10-02.html); [Trend Micro 2025](https://www.trendmicro.com/en_sg/about/newsroom/press-releases/2025/2025-08-26.html)
  - Google runs on-device Gemini Nano call scam detection in India, but only on Pixel 9 and only in English. Pixel holds under 1% of India's phone market. Google also pilots screen-share scam alerts with Navi, Paytm and GPay — [TechCrunch](https://techcrunch.com/2025/11/20/google-steps-up-ai-scam-protection-in-india-but-gaps-remain); [Storyboard18](https://www.storyboard18.com/digital/google-rolls-out-on-device-scam-detection-in-india-as-digital-fraud-losses-top-%e2%82%b970-billion-84553.htm)
- **Mule detection at large banks is now served by a central-bank tool.** RBIH's MuleHunter.AI was live at 23 banks by Dec 10, 2025, up from about 15 in Aug 2025. It reportedly finds about 20,000 mule accounts a month — [MediaNama](https://www.medianama.com/2025/12/223-rti-23-banks-mulehunter-mule-accounts/); [Business Standard](https://www.business-standard.com/finance/news/rbi-innovation-hub-develops-mulehunter-ai-to-combat-mule-account-frauds-124120601042_1.html)
- Even regulatory-change AI for Indian BFSI already has entrants. OnFinance AI markets compliance AI built around RBI penalties and circulars — [OnFinance AI newsletter](https://onfinanceainewsletter.beehiiv.com/p/rbi-s-56-32-crore-penalty-surge-how-ai-can-prevent-compliance-lapses-in-bfsi)

### Inferences
- **Crowded — avoid (unless you take a sharp new angle):**
  1. Generic banking or insurance chatbots and FAQ bots (Kasisto, Personetics, every bank's own bot).
  2. KYC document OCR and extraction (HyperVerge, IDfy, Signzy, Perfios, Advance.ai).
  3. Deepfake and liveness detection for video KYC (HyperVerge DeepfakeSafe, IDfy, Sumsub). The judges are likely to know these products.
  4. Generic transaction fraud scoring on PaySim or IEEE-CIS (Feedzai, Featurespace, SEON, Sardine). Many hackathon teams build this, so it scores poorly on Innovation.
  5. Robo-advisors and personal-finance coaches (Cleo-style).
  6. Thin-file alternative credit scoring (Trusting Social, CredoLab, Perfios).
  7. Photo-based motor/property claims damage estimation (Tractable) and insurer-side claims fraud (Shift Technology).
  8. Scam checkers that work before a scam: paste a message and get a verdict (ScamShield, Trend Micro, Whoscall, Google Gemini Nano).
  9. Mule-account ML scoring for large Indian banks (MuleHunter.AI).
- The vendor names in items 1, 4, 5, 6 and 7 come from background knowledge and the task brief. Their presence in JAPAC was not re-checked in this session.

### Gaps
- Product pages for Feedzai, Featurespace, SEON, Sardine, Kasisto, Personetics, Cleo, Tractable and Shift were not fetched, so their exact APAC footprint is unconfirmed.
- I did not check whether Gogolook/Whoscall has added GenAI features since 2025.

---

## Q2. Candidate gaps with evidence (ranked for this hackathon)

### Takeaway
The strongest gap is a multilingual, multimodal "post-scam golden-hour recovery copilot". Losses are huge, recovery depends on how fast and complete the report is, regulators have just created formal dispute and hold mechanisms, and existing tools only work before the scam. Five more gaps follow in the inferences, ranked.

### Cited Findings

**Gap A — Post-scam "golden hour" recovery and dispute copilot (multilingual, multimodal)**
- **Size of losses:**
  - GASA estimates US$23.6B lost to scams in Southeast Asia, with 22% of adults losing money in 2024. Malaysia has the highest prevalence (32%), then the Philippines (31%) and Singapore (21%). Singapore has the highest average loss per victim (US$2,132) — [Vietnam News on GASA SEA 2025](https://vietnamnews.vn/world/1725271/singapore-scam-victims-top-southeast-asia-losses-at-us-2-132-per-person-malaysia-second.html)
  - Country figures: Thailand ฿115.3B (US$3.2B) — [GASA Thailand 2025](https://gasa.org/knowledge-base/reports/state-of-scams-in-thailand-report-2025); Taiwan US$2B with 61% of adults victimised — [GASA Taiwan 2025](https://gasa.org/knowledge-base/reports/state-of-scams-in-taiwan-report-2025); South Korea US$1.4B — [GASA Korea 2025](https://gasa.org/knowledge-base/reports/state-of-scams-in-south-korea-report-2025); Philippines ₱280.5B — [Philstar](https://www.philstar.com/business/2025/11/26/2489831/pinoys-lose-p280-billion-scammers-report)
- **Victims authorised the transfer themselves, so bank-side fraud models miss them.** Singapore scam losses were S$913.1M in 2025, down from S$1.1B in 2024. In 81.8% of cases the victim authorised the transfer — [ai2.work, a secondary source; check against SPF annual scam statistics](https://ai2.work/blog/singapore-s-mas-recruits-banks-and-ai-to-stop-scams-early)
- **India:**
  - I4C recorded about ₹19,813 crore in losses and 2.18M cheating complaints in 2025 — [Moneylife](https://moneylife.in/article/fraud-alert-india-is-losing-over-22000-crore-a-year-in-cyber-scams-and-the-worst-is-yet-to-come/80612.html)
  - ThePrint reports ₹22,495 crore lost in 2025, mostly to investment scams — [ThePrint](https://theprint.in/india/cybercrime-saw-24-spike-in-2025-indians-lost-rs-22495-crore-mainly-in-investment-scams/2859930/). The two figures conflict; they likely count different things.
  - "Digital arrest" losses rose from ₹91 crore (2022) to ₹1,935 crore (2024) — [Frank on Fraud PDF](https://frankonfraud.com/wp-content/uploads/2026/01/Digital-Arrest-Scams-Explained.pdf)
  - The 1930 helpline logged 32.4M calls in 2025 — [Moneylife](https://moneylife.in/article/fraud-alert-india-is-losing-over-22000-crore-a-year-in-cyber-scams-and-the-worst-is-yet-to-come/80612.html)
- **Speed decides recovery:**
  - Recovery is 25-40% when reported within 24 hours, but 5-10% after 7 days — [Moneylife golden hour](https://moneylife.in/article/fraud-alert-use-golden-hour-to-report-scam-and-increase-your-chances-to-get-money-back/74091.html)
  - Odisha recovered only 2.7% of ₹370 crore lost over 3 years — [The420](https://the420.in/?p=96456)
  - Uttar Pradesh reached a 47% recovery rate with real-time bank-police coordination — [The420 UP](https://the420.in/uttar-pradesh-cyber-fraud-recovery-1930-cfmc-golden-hour/)
- **Regulators have just created formal dispute and hold mechanisms:**
  - Philippines: AFASA (RA 12010) implementing rules took effect June 25, 2025. They include "Regulations on Temporary Holding of Disputed Funds and Coordinated Verification Process" — [Context.ph](https://context.ph/2025/06/11/bsp-issues-implementing-rules-for-afasa-law/); [Malaya](https://malaya.com.ph/business/business-news/anti-financial-scam-laws-irr-to-take-effect-june-25-bsp)
  - Australia: the Scams Prevention Framework Act 2025 requires banks, telcos and platforms to "Prevent, Detect, Disrupt, Respond, Report", with penalties up to A$50M — [Vixio](https://www.vixio.com/insights/pc-australia-enacts-world-leading-scams-prevention-framework); [BankInfoSecurity](https://www.bankinfosecurity.net/new-australian-law-makes-banks-telecoms-liable-for-scams-a-27516)
  - Singapore: the MAS/IMDA Shared Responsibility Framework assigns phishing losses first to financial institutions, then telcos, if they breach their duties — [Baker McKenzie](https://insightplus.bakermckenzie.com/bm/data-technology/singapore-mas-and-imda-seek-comments-on-proposed-shared-responsibility-framework-for-phishing-scams)
- **Existing tools act before the scam, not after it** (ScamShield, Trend Micro, Google Gemini Nano; see Q1 sources). None I found turns a victim's screenshots into a complete, jurisdiction-correct report and bank-dispute packet.

**Gap B — Japan elderly "pause-and-verify" companion against police-impersonation scams**
- Losses to "special fraud" in Japan roughly doubled in 2025 to ¥142.3B, a record. Including SNS investment and romance scams, the total was ¥325.7B — [Nippon.com](https://www.nippon.com/en/japan-data/h02795/fake-police-scams-double-in-japan-as-financial-losses-from-fraud-soar.html)
- Fake-police scams more than doubled to 11,014 cases and ¥100.5B. People aged 65+ account for 51.3% of cases and 59.2% of losses — [Nippon.com](https://www.nippon.com/en/japan-data/h02795/fake-police-scams-double-in-japan-as-financial-losses-from-fraud-soar.html)
- Current responses are blunt: police proposed ATM limits for the elderly — [SCMP](https://scmp.com/week-asia/economics/article/3304007/japan-police-propose-atm-curbs-elderly-combat-fraud). Japan's MIC issued a July 2026 request to strengthen countermeasures — [MIC press release](https://www.soumu.go.jp/main_sosiki/joho_tsusin/eng/pressrelease/2026/7/29_1.html)
- Related dementia problem: financial assets held by people with dementia are projected at about ¥215T by 2030. About 30% of patients and families report financial losses. The Japanese Bankers Association allows relatives to withdraw on the patient's behalf, if it is in the patient's interest — [Bloomberg 2018, older but structural](https://www.bloomberg.com/news/articles/2018-10-16/the-captive-capital-of-japan-s-millions-of-dementia-sufferers); [Jiji](https://sp.m.jiji.com/english/show/10493)
- Australia shows the same pattern: people over 65 lost A$99.6M across 62,147 reports in 2024 — [ShuftiPro summarising Scamwatch](https://shuftipro.com/blog/fraud-prevention-australia-banking/)

**Gap C — Mule-network investigation copilot for small, rural and co-operative banks (India UCBs, Indonesia BPRs, Philippines rural banks)**
- MuleHunter.AI covers only 23 banks (Q1). India has hundreds of co-operative banks; that count is not sourced here.
- In 2024 the RBI imposed ₹56.32 crore in fines across 304 actions. Co-operative banks received 234 penalties (₹16.66 crore) for lapses including cyber-security failures — [OnFinance AI newsletter, secondary](https://onfinanceainewsletter.beehiiv.com/p/rbi-s-56-32-crore-penalty-surge-how-ai-can-prevent-compliance-lapses-in-bfsi)
- Indonesia has 1,468 BPR/BPRS left, down 171 in five years. OJK revoked 7 licences in 2025 and is forcing consolidation under POJK 7/2024 — [Kontan](https://keuangan.kontan.co.id/news/ojk-percepat-konsolidasi-sejumlah-bpr-berguguran-sepanjang-2025); [Bisnis](https://finansial.bisnis.com/read/20250514/90/1876861/jumlah-bpr-makin-sedikit-perbarindo-jelaskan-penyebabnya)
- The Philippines' AFASA makes money muling a crime (Sec. 4(a)) and adds rules on account inquiry and information sharing — [SunStar](https://www.sunstar.com.ph/cebu/bsp-unveils-rules-to-combat-financial-scams); [Inquirer](https://business.inquirer.net/502848/bsp-sharpens-framework-for-probing-suspicious-accounts)

**Gap D — Vernacular insurance "policy X-ray" and mis-selling detector, checked before the free-look window ends (India first)**
- IRDAI's FY25 annual report: "unfair business practice" (mis-selling) grievances rose to 26,667 from 23,335 (+14%), now 22.14% of life-insurer complaints. The Bima Bharosa portal received 257,790 grievances — [Insurance Business Asia](https://www.insurancebusinessmag.com/asia/news/breaking-news/irdai-sees-misselling-complaints-rise-amid-stable-grievances-561149.aspx); [Outlook Money](https://www.outlookmoney.com/insurance/insurance-claims-mis-selling-account-for-most-insurance-complaints-in-fy25-reveals-irdai-annual-report)
- IRDAI tells insurers to assess suitability and do root-cause analysis on mis-selling — [Outlook Money](https://www.outlookmoney.com/personal-finance/irdai-flags-mis-selling-tells-insurers-to-look-inward-as-profits-climb)
- Business Standard (Jan 2026) on reviewing the benefit illustration and premium table to spot mis-selling — [Business Standard](https://www.business-standard.com/finance/personal-finance/life-insurance-mis-selling-review-benefit-illustration-premium-table-126010800557_1.html)
- Insurance Samadhan reports complaints up 45% in Q2 2025; endowment plans are the most mis-sold — [Business Standard](https://www.business-standard.com/amp/finance/personal-finance/insurance-complaints-up-45-in-q2-2025-most-about-health-policies-report-125092401017_1.html); [StartupTalky](https://startuptalky.com/news/insurance-samadhan-q2-report-mis-selling-claims/)
- **Existing players:** Insurance Samadhan is mainly a human-assisted grievance service — [Insurance Samadhan profile](https://valueforstartups.in/insurancesamadhan). Polifyx has a "Know Your Policy" feature — [Outlook Money](https://www.outlookmoney.com/amp/story/insurance/mis-selling-complaints-grew-112-since-2024-value-of-disputed-claims-rose-10-report). **This gap is partly occupied.** The differentiation would be a voice-first, regional-language tool that compares what the agent promised (a voice note or WhatsApp chat) against the policy wording, applied to IRDAI rules.

**Gap E — Farmer-side crop insurance claim advocate (PMFBY and similar schemes)**
- States have defaulted on about ₹6,450 crore of PMFBY claims since FY20, and about ₹947 crore is reported unpaid. Field verification is poor. Rajasthan's agriculture minister alleged insurers rejected claims from 170,000 farmers without surveys and with forged signatures (Oct 2025). The PMFBY budget for 2025-26 is ₹12,242 crore, 23% lower — [IASGyan](https://www.iasgyan.in/daily-current-affairs/pradhan-mantri-fasal-bima-yojana-systemic-failures); [Down To Earth](https://www.downtoearth.org.in/amp/story/agriculture/pradhan-mantri-fasal-bima-yojana-why-are-farmers-in-rajasthan-protesting-about-insurance-claims)
- Late payment carries a 12% interest penalty on insurers, which a tool can calculate and demand — [Cafemutual](https://cafemutual.com/news/press-news/35315-insurance-companies-urged-to-pay-interest-on-delayed-crop-insurance-claims-in-karnataka)

**Gap F — Regulatory-change copilot for very small regulated entities (BPRs, UCBs, rural banks, small NBFCs)**
- The RBI directive of Jan 31, 2024 requires NBFCs, small finance banks and others to adopt technology-based compliance monitoring — [AMLegals](https://amlegals.com/regtech-in-india-revolutionizing-compliance-in-a-digital-economy/); [TimesTech](https://timestech.in/unveiling-the-future-exploring-surge-in-bank-spending-on-regtech-in-2024/)
- Co-operative banks dominate RBI penalties (above). Indonesia's BPR consolidation under POJK 7/2024 raises supervisory pressure (above).
- **Partly crowded:** OnFinance AI and global RegTech vendors exist. This is weaker on Innovation.

**Gap G (weakest evidence) — Migrant-worker remittance and scam literacy (OFWs, Indonesian PMI)**
- Indonesian migrant workers sent about US$15.7B in remittances in 2024. Low financial and digital literacy and exposure to illegal investment scams are documented, mostly in academic and community studies — [Unnes journal](https://journal.unnes.ac.id/journals/abdimas/article/download/62079/10950/183455); [UNY journal](https://journal.uny.ac.id/index.php/inotek/article/view/88865)
- Philippines House Bill 10914 proposes mandatory OFW financial education — [Malaya editorial](https://malaya.com.ph/opinion/editorial/financial-literacy-and-ofws)

### Inferences

Suggested ranking for this hackathon:

1. **Gap A — "Golden Hour" scam recovery copilot.** Best overall fit.
   - The victim uploads screenshots, UPI/PayNow/GCash receipts, chat exports and a voice note in Hindi, Tagalog, Bahasa, Thai, Japanese and so on.
   - Gemini then:
     - extracts a structured timeline: amounts, UTR/reference IDs, beneficiary accounts, the scammer's handles;
     - classifies the scam type (digital arrest, pig-butchering, phishing, fake police);
     - picks the jurisdiction's route: India 1930/NCRP and the bank's fraud desk; Philippines AFASA disputed-funds hold; Singapore SRF and SPF; Australia SPF and IDCARE;
     - drafts a pre-filled complaint and bank dispute letter in both English and the local language, with a live golden-hour countdown and checklist.
   - On the bank side, a triage console clusters incoming reports by shared beneficiary accounts, which also surfaces mule accounts and links to Gap C.
   - Why it wins: multimodal plus multilingual plus tool-calling plus grounded RAG over regulations gives high GenAI depth. The impact numbers are huge, and no product owns post-incident recovery. Demo data can be synthetic screenshots plus PaySim-style transfers.
2. **Gap B — Japan elder "pause-and-verify" agent.** Gemini Live voice in Japanese:
   - the family or bank sets a trusted contact;
   - before a large transfer, a short conversation checks intent and asks about known script patterns ("police said your account is used for crime");
   - it escalates to the family with an explanation.
   - Strong impact and Japan-specific, but the demo is narrower and the transaction trigger would be mocked.
3. **Gap C — Mule investigation copilot for small banks.** A graph built from PaySim/AMLSim plus Gemini-written explanations, AFASA/STR-style report drafts, and analyst Q&A. Novelty comes from the target user (a 2-person compliance team at a BPR or co-op bank). The weakness is that it is close to existing AML vendors (Tookitaki, Feedzai).
4. **Gap D — Vernacular policy X-ray and mis-selling detector.** Strong Gemini document plus audio fit; partly occupied.
5. **Gap E — Farmer crop-claim advocate.** Earth Engine or Sentinel imagery plus geotagged photos plus a Gemini-drafted grievance with the 12% interest calculation. High impact; claim data access is the hard part.
6. **Gap F — Regulatory-change copilot for micro-regulated entities.** Feasible, but less novel.
7. **Gap G — Migrant remittance coach.** Thin evidence; better used as a feature inside Gap A.

Ideas that combine well: A+C (victim intake feeds the mule graph) or A+B (one scam-response agent with a Japan elder mode).

**Public demo data:**
- PaySim — https://www.kaggle.com/datasets/ealaxi/paysim1
- IEEE-CIS Fraud — https://www.kaggle.com/c/ieee-fraud-detection
- IBM AMLSim — https://github.com/IBM/AMLSim
- IBM synthetic AML transactions — https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml
- Regulator documents for RAG: BSP AFASA circulars, the MAS SRF, the Australian SPF Act, IRDAI circulars, OJK POJK 7/2024

These dataset URLs come from background knowledge and were not fetched in this session.

### Gaps
- Exact Singapore 2025 police statistics (S$913.1M; 81.8% self-authorised) come from a secondary blog. Check them against the SPF Annual Scams & Cybercrime Brief.
- I found no figures for the count of Indian urban co-op banks, Philippine rural banks, or their fraud-tooling penetration.
- The IRDAI free-look period length (reportedly extended to 30 days in 2024) was not verified this session.
- Small-merchant dispute and chargeback handling in JAPAC was not researched (no evidence collected).
- Microinsurance and parametric cover for gig workers was not researched; only crop insurance was.
- I did not confirm that no startup offers an end-to-end post-scam recovery assistant in Southeast Asia. GASA, IDCARE (Australia) and bank hotlines provide human support; a targeted product search is recommended before committing.

---

## Q3. Buildability with Gemini in about 10 days, and public data or demo sources

### Takeaway
Gaps A-D can be built as a Cloud Run backend with Gemini 2.5 (multimodal, function calling, structured JSON), a Firebase frontend, and synthetic demo data. The main risk is data realism rather than model capability.

### Cited Findings
- Google already ships Gemini Nano scam detection on device, but only on Pixel 9 and in English. That shows the gap in Indic and SEA languages and on non-Pixel phones that a cloud Gemini app can fill — [TechCrunch](https://techcrunch.com/2025/11/20/google-steps-up-ai-scam-protection-in-india-but-gaps-remain)
- The regulatory documents to ground on are public (AFASA IRR, SPF Act, SRF, IRDAI reports) — [Context.ph](https://context.ph/2025/06/11/bsp-issues-implementing-rules-for-afasa-law/); [Vixio](https://www.vixio.com/insights/pc-australia-enacts-world-leading-scams-prevention-framework); [Baker McKenzie](https://insightplus.bakermckenzie.com/bm/data-technology/singapore-mas-and-imda-seek-comments-on-proposed-shared-responsibility-framework-for-phishing-scams)

### Inferences
- Gap A architecture:
  - Firebase app with upload, voice and chat;
  - Cloud Run agent: Gemini multimodal extraction into a JSON schema, a scam-type classifier, and function calls to jurisdiction "playbooks" (RAG over regulator PDFs);
  - generated complaint PDFs;
  - a Firestore case store;
  - a bank-side console that clusters reports by beneficiary account (BigQuery or simple graph).
  - Gemma could run a privacy-preserving on-device redaction step, which would add technical merit.
- Using Gemma for on-device or edge pre-screening in Gap B also matches the "Gemini/Gemma" requirement and supports a privacy story.

### Gaps
- I did not verify Gemini's current support for low-resource languages such as Bahasa Jawa or Cebuano, or its speech accuracy in Hindi, Tagalog and Thai. Test early.
