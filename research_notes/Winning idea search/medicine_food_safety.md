# Medicine and Food Safety Gaps (JAPAC): Research Notes

Researched on 2026-10-10 for the Google Cloud AI Builder Cup 2026 (deadline Oct 18). Fits the Retail & Commerce theme (pharmacy retail), with Manufacturing or Social Impact as alternates.

## 1. The pain, quantified

### Medicines (India is the strongest data story)
- **NSQ volume per month (CDSCO, central and state labs combined):**
  - July 2026: 280 samples NSQ or spurious (40 central, 240 state), including 1 spurious from Bihar. [ETV Bharat](https://www.etvbharat.com/en/bharat/cdsco-flags-280-drug-samples-as-nsq-or-spurious-in-july-enn26082107816)
  - August 2026: 220 NSQ (29 central, 191 state) plus 1 spurious from Delhi. [Daily Pioneer](https://dailypioneer.com/news/220-drug-samples-fail-quality-tests-august), [Asianet](https://newsable.asianetnews.com/india/cdsco-finds-220-substandard-drug-samples-one-spurious-drug-in-delhi-articleshow-7bg7lqo)
  - FY2025-26: 3,012 NSQ and 283 spurious out of 1.41 lakh samples tested (from the same ETV article).
  - Rule of thumb: about 200-280 flagged batches every month.
- **What gets flagged:** everyday medicines such as paracetamol, pantoprazole, cefixime, telmisartan, antibiotics, and also injectables. About half of Karnataka's 305 failed batches (Jan-May 2025) were injectables. [Newslaundry](https://www.newslaundry.com/2025/06/24/is-your-medicine-safe-karnataka-flags-305-faulty-drug-batches-but-recall-system-patchy)
- **The recall reaching the shop is the weak link.** Newslaundry's conclusion: "the system is simply not rigorous – people can still end up buying their medicines from unaware pharmacists."
- **Flagged stock is still sellable:** in the March 2025 NSQ PDF, many listed batches expire in 2026-2028 (for example amoxicillin-clavulanate batch 4032409004, expiry 08/2028). Those batches can still be on shelves and sold for years after the alert.
- **Time lag:** the NSQ list for month M is published around the 3rd week of month M+1, and samples are often drawn earlier. Stock moves the whole time, so the shop needs to act the same day.
- **Global framing (WHO, 2017):** about 1 in 10 medical products in low- and middle-income countries is substandard or falsified (10.5% failure rate; 88 countries; 48,000 samples). This causes an estimated 72k-169k child pneumonia deaths a year from bad antibiotics. [WHO](https://www.who.int/news/item/28-11-2017-1-in-10-medical-products-in-developinG-countries-is-substandard-or-falsified)
- **Number of users:**
  - India: about 12.4 lakh (1.24M) chemists, according to AIOCD.
  - Indonesia: about 31,000 licensed apotek; the top 5 chains run only about 10%. [L.E.K.](https://www.lek.com/insights/hea/sea/ei/indonesias-retail-pharmacy-landscape-why-global-investors-should-take-closer)
  - Philippines: 16,300 Botika ng Barangay outlets, some already caught reselling counterfeits bought from the cheapest suppliers. [SafeMedicines](https://safemedicines.org/?p=4085)
  - Vietnam: tens of thousands of nhà thuốc; chains hold only about 16% of the market.
- **Regional regulators keep issuing batch-level recalls:**
  - **Indonesia:** BPOM Regulation No. 12 of 2026 (in force 9 Jul 2026) widens drug recall and destruction duties to hypermarkets, supermarkets and minimarkets. [veritask](https://veritask.ai/en/artikel/peraturan-bpom-nomor-12-tahun-2026-mengatur-mekanisme-penarikan-dan-pemusnahan-obat-serta-bahan-obat-yang-tidak-memenuhi-standar)
  - **Vietnam:** the Drug Administration (DAV) issues national batch recalls such as Pyfaclor Kid, Diclofen and Aceclofenac STELLA in July 2026. Pharmacies must take back stock from patients.

### Food
- **India FY26:** 40,023 of 2,23,808 food samples were non-conforming (about 18%). For milk and dairy it was 37.3%. There were 5.2 lakh inspections but only 1,918 convictions. [LatestLY](https://www.latestly.com/agency-news/business-news-over-40000-food-samples-failed-safety-tests-in-fy26-govt-tells-parliament-7530414.html), [RuralVoice](https://eng.ruralvoice.in/milk-quality-concerns-deepen-37-pc-of-samples-fail-fssai-standards-in-fy26-over-11700-cases-filed)
- **FSSAI recall module:** went live in FoSCoS by order dated 18 Mar 2026. [FSSAI order](https://www.fssai.gov.in/upload/advisories/2026/03/69bbb3b762053Order%20dt.%2018.03.2026_Implementation%20of%20Food%20Recall%20functionality%20in%20FoSCoS.pdf)
  - Analysis of 154 recalls (Feb 2024 - Jul 2026): **only 11% are marked "Completed"**; 55.8% are stuck at "Initiated". [FoodSafetyWorks](https://foodsafetyworks.com/insights/food-recall-trends-in-india-what-the-foscos-data-reveals/)
- **Singapore:** SFA's SAFE framework started 19 Jan 2026. Under an SFA recall direction, businesses must clear affected products from all distribution points within **48 hours** and report completion. [ChemLinked](https://food.chemlinked.com/news/food-news/singapore-implements-safety-assurance-for-food-establishment-framework-to-strengthen-food-safety)

## 2. Existing tools and the gap

| Tool | What it does | Gap |
|---|---|---|
| CDSCO NSQ monthly PDFs, plus a searchable NSQ link (notice of 28 Aug 2025) | You search one product or batch at a time on the portal | Pull-only and manual. No stock matching, no alerts, no paperwork. State lists are scattered. |
| Telangana DCA bulk SMS alerts | Pushes an SMS to shops when the state lab declares a batch NSQ | One state, state-lab results only. The chemist still checks stock by hand. No closure tracking. [MedicalDialogues](https://medicaldialogues.in/news/industry/pharma/telangana-dca-introduces-sms-alert-system-to-warn-pharmacies-about-substandard-medicines-166301) |
| Kerala MedWatch (Drugs Control Dept) | Type a batch and name to get the quality result | Single lookup. Was labs/hospitals only and "coming soon" in mid-2025. [Kerala Kaumudi](https://keralakaumudi.com/en/lifestyle/general/want-to-know-quality-of-medicine-you-buy-mobile-app-to-check-it-yourself-coming-soon-1549847) |
| Marg ERP, Gofrugal, Medeil | Batch and expiry tracking; expiry, non-moving and returns-by-batch alerts | **No NSQ or recall feed found** in any feature list. Many small chemists don't keep batch-level stock in software at all. |
| QR track-and-trace (top-300 brands since Aug 2023; vaccines, NDPS and oncology by Jul 2027; antimicrobials by Jul 2028) | Checks a pack is authentic and shows its batch | Proves a pack is genuine, not that the batch passed testing. A genuine batch can still be NSQ. Coverage stays partial until 2028. [RAPS](https://www.raps.org/resource/asia-pacific-roundup-india-expands-mandatory-use-of-qr-codes-for-traceability-starts-phased-transition.html) |
| PharmaSecure psVerify, mPedigree, Sproxil, BPOM "Cek BPOM" | Check one pack's code or registration number | Consumer authenticity checks, one pack at a time. They don't check NSQ or recall status across a shop's stock. |
| **MedShield (Devpost)** | **Closest competitor.** Google ADK plus Gemini 2.5 Flash-Lite agent. A chemist **types** a drug name and batch; it runs an 11-step check (registry, manufacturer capacity, **parsed CDSCO NSQ PDFs**, geospatial counterfeit clusters) and generates complaints. Uses MongoDB vector search over 254k Indian medicines. | One batch at a time, typed in, focused on counterfeits. Doesn't import whole-shop stock from invoices, doesn't re-match automatically each month, and has no quarantine, return or closure loop. [Devpost](https://devpost.com/software/mshield) |
| Credo (Devpost) | Offline OCR in the browser (Tesseract WASM) reads a pack's batch and checks a local database | Single pack, offline, no regulator feed or paperwork. [Devpost](https://devpost.com/software/credo-siqz05) |
| Medical Patrol (lablab, Jul 2025), ExpiryMitra (HackQuest) | Label OCR for counterfeit or expiry checks | Consumer-facing, Africa or expiry focus. |
| HermesRX, Med-Data, DrugXafe | US FDA recall feeds, consumer apps | US only. |
| GitHub `kaif007219/cdsco-nsq-analysis` | Analyses NSQ failure patterns | Analytics only. No product. |
| GitHub FSSAI label checkers (labelguard at IIT KGP Arch Hackathon, AI-Powered-FSSAI-Compliance-Checker, Foody, and about 5 more) | Label compliance from a photo | **Saturated. Avoid.** |

GitHub searches for "NSQ CDSCO", "CDSCO drug alert", "drug recall pharmacy invoice", "spurious drug india" and "FSSAI recall" all returned 0 repos.

## 3. Key insight to build on
India's Drugs Rules require batch number and expiry on every pharma sale and purchase invoice. A chemist's **purchase invoice stack is therefore a batch-level inventory**, even if the shop has no ERP. Gemini multimodal reads those invoices well, including messy thermal prints, Hindi or English, and handwritten notes.

The NSQ PDFs are text-based with a stable 8-column table (S.No, Product, Batch, Mfg date, Expiry, Manufacturer, NSQ result, Reporting lab). I verified this with pdftotext on the March 2025 alert, so the lists can be parsed into a structured database reliably.

## 4. Idea framings

### A. "RecallRadar for Chemists": invoice-to-quarantine in 2 minutes (RECOMMENDED)
- **Named user:** Ramesh, owner of a single-counter chemist shop in Lucknow. About 3,000 SKUs, no ERP, and supplier invoices in a box file.
- **Workflow:**
  1. Ramesh photographs the last 90 days of purchase invoices, or uploads a Marg/Gofrugal CSV export.
  2. Gemini 2.5 Flash extracts line items to a schema: product, strength, batch, expiry, supplier, quantity.
  3. A Cloud Run job ingests each month's CDSCO, state and spurious PDFs, plus DAV and BPOM notices for other countries. Gemini normalizes these into a recall database.
  4. Matching is exact on batch after normalization (O/0, spaces, hyphens), then fuzzy on product and manufacturer. Gemini embeddings tell "Pantoprazole 40 (Pantoshang)" apart from other pantoprazole brands.
  5. **Human in the loop:** every likely match shows the invoice crop next to the NSQ row. The chemist then takes a shelf photo of the strip, and Gemini reads the printed batch to confirm before anything is filed.
  6. One tap generates a quarantine register entry, a "do not sell" flag, a return-to-supplier debit note or letter citing the NSQ alert, and an intimation to the area Drug Inspector. These come as PDFs in English, Hindi or another local language.
  7. Each month, new NSQ lists are re-matched against stored stock and a push or WhatsApp alert goes out.
- **Before/after metric:**
  - Before: checking about 250 new NSQ batches against about 3,000 SKUs by hand is effectively never done. Realistically it's 0% coverage, or hours a month per shop.
  - After: 90 days of invoices (about 60 invoices, about 1,500 lines) matched in under 3 minutes. Recall paperwork goes from about 45 minutes to under 2 minutes.
  - **Backtest headline:** replay 12 months of real NSQ PDFs against a synthetic shop and report "X flagged batches would have been caught N days earlier."
- **Gemini depth:** multimodal invoice extraction, PDF table parsing, embeddings for brand/generic matching, structured output, multilingual document drafting, and an ADK agent orchestrating the monthly sweep. Deploy on Cloud Run with Firestore and Cloud Scheduler.
- **Gap vs MedShield:** MedShield checks one batch you type in, aimed at counterfeits. This product turns a whole shop's paper trail into protected inventory and closes the loop with paperwork. Pitch it as "stock-wide, retroactive, and actionable."
- **Buildability in 8 days: high.** NSQ PDFs are public and text-based. Invoices can be mocked from real templates. No external APIs are needed beyond Gemini.

### B. "Recall Closure Console": a two-sided version for regulators (an extension of A)
- **Named user:** a district Drug Inspector or Assistant Drugs Controller. For food, a Designated Officer in FSSAI.
- **What it does:**
  - Every chemist acknowledgment from A ("checked, nil stock" or "quarantined 14 strips, photo attached") feeds a dashboard.
  - The dashboard shows recall penetration by district, shops that haven't responded, and AI-summarized exceptions.
  - It can also run on the food side: FoSCoS recalls are only 11% marked complete. Same closure-loop pattern, and SFA's 48-hour deadline is another hook.
- **Metric:** recall closure visibility goes from "unknown / 11% documented" to a percentage of shops confirmed within 72 hours.
- **Buildability:** medium. Build it as the second screen of A; it makes a strong demo.

### C. "Batch-Trace for Food MSMEs": recall readiness and a mock-recall drill
- **Named user:** Priya, who runs a 12-person masala/spice unit. Spices and sauces are the top FSSAI recall category at 35.7%.
- **What it does:**
  - She photographs production logs, raw-material invoices and sales invoices.
  - Gemini builds a one-up/one-down trace graph by batch.
  - The tool runs a mock recall to show who got lot 2409-B, and drafts the FSSAI Food Recall Procedure plan, the distributor notices and the FoSCoS recall entry.
- **Metric:** mock-recall trace time goes from hours or days to minutes, measured against the SFA 48-hour benchmark.
- **Weaknesses:** no public batch-level food recall dataset like CDSCO's (FoSCoS recall data is thinner). The demo would rely on synthetic data, and it is a less emotional story than medicine.
- **Buildability:** medium.

## 5. Demo data
- CDSCO NSQ monthly alerts, central and state, as PDFs: https://cdsco.gov.in/opencms/opencms/en/Notifications/Alerts. Mirrors on medicaldialogues.in/pdf_upload/ cover Sep 2024 - Apr 2025 and later.
- Spurious drug lists, same page.
- Vietnam DAV recall notices (thuvienphapluat.vn "thông báo thu hồi thuốc vi phạm mức độ 2/3"). Philippines FDA advisories at fda.gov.ph.
- Medicine master list: the public dataset of 254k Indian medicines that MedShield used (A-Z Indian medicine dataset on Kaggle), for brand-to-generic normalization.
- Invoices: synthesize 40-60 GST pharma invoices with realistic batches, seeding about 5 batches that really appear in NSQ lists. Add 2-3 photographed printouts so the OCR has to handle real noise.

## 6. Risks
- **Liability:** an NSQ finding covers only the tested batch. CDSCO says so explicitly. The app must say "flagged, verify" rather than "unsafe" and keep a human confirmation step. This supports the human-in-the-loop story.
- **Batch-number noise:** different formatting or OCR confusion between O and 0 or I and 1. Use a confirmation photo and show confidence for each match.
- **MedShield overlap:** judges who have seen MedShield, which uses Google ADK and so may have come from a Google hackathon, could see this as derivative. The demo should open on the invoice-stack-to-quarantine flow, not on single-batch lookup.

## 7. Verdict on novelty
- **Single-batch NSQ lookup: NOT novel.** CDSCO's search link, Kerala MedWatch, MedShield (Gemini plus CDSCO PDFs) and Credo all do it.
- **Invoice/stock-wide retroactive matching, a shelf-photo confirmation step, auto-generated return and quarantine paperwork, and a regulator closure dashboard: NOVEL as far as this search could find.**
  - No ERP feature, GitHub repo, Devpost or lablab project, or government app does it.
  - Telangana's SMS alert shows regulators want push alerts, but nobody has built the shop-side action loop.
- It fits the 2026 winner pattern: a named user (the chemist), a risky slow workflow (recalls that never reach the shelf), a measurable before/after (backtest days-earlier and minutes of paperwork), human-in-the-loop, deep Gemini use, and a health story close to Peel's.
- **Recommendation:** build A, with B's dashboard as the second screen. Don't use food (C) as the lead; at most mention it as the expansion slide. **Novelty: moderate-high** if framed as "turn the invoice box into recall protection"; **low** if framed as "check if a medicine is substandard."
