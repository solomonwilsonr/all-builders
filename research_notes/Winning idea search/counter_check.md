# Counter Check: idea validation (AI Builder Cup 2026, Retail & Commerce)

Date: 2026-10-11. Deadline Oct 18. Team of 2.

**Idea:** at the point of sale in a small Indian (later SEA) chemist, the counter person photographs (1) the prescription and (2) the strips or packs being handed over. Gemini cross-checks the two for:
- right drug, strength and form
- look-alike/sound-alike (LASA) brand confusion
- quantity against the prescribed duration
- interactions and duplicate therapy
- expiry
- batch against the CDSCO NSQ/spurious lists

It then drafts the Schedule H1 register entry and a sale record. The pharmacist approves. Every flag means "verify", never a verdict.

---

## TL;DR verdict

- **Full combination: PARTIALLY DONE.**
  - Reading the prescription is crowded.
  - Turning a prescription photo into a bill plus an automatic H1 register entry already ships: **Nesayo**, 2026, ₹399-2,999/month, uses Claude Vision.
  - Gemini-based interaction and dosage "RED ALERT"s at the pharmacy point of sale already exist as a lablab project: **RXPro**, Nov 2025.
- **What is still open:**
  - The **two-photo reconciliation**: "does the pack in the chemist's hand match what the doctor wrote?"
  - Combined with a LASA warning, an expiry check and an NSQ batch check on that same pack, at the counter.
  - We found no Indian product, ERP, hackathon project or GitHub repo that does this.
  - The global equivalents are US hardware for pill counting and vial imaging (InterLink AI, formerly PerceptiMed; Omnicell/Parata robots). They do not work for small chemists or handwritten prescriptions.
- **Biggest risk:** handwriting accuracy. On Indian handwritten prescriptions, frontier vision-language models get only **47-58% of the medicine table right** and invent about **3 fields per prescription** (RxScribe Bench, Sep 2026).
  - Mitigation: frame the task as *verification*, not transcription. Read the printed pack first, then ask whether the prescription is consistent with it. Abstain when unsure.
  - Even so, the risk of a wrong "match" in a live demo is real.
- **Against BatchWatch:**
  - Counter Check has a higher ceiling: more visible multimodal reasoning, a stronger live demo and a more emotional story.
  - BatchWatch has a higher floor: deterministic matching, a reliable demo, a backtest metric, and it is clearly more novel.
  - **Recommendation:** build Counter Check *scoped to dispensing reconciliation*, with BatchWatch's NSQ database as one of its checks and the H1 register as a by-product, not the headline. Fall back to BatchWatch if the day-3 accuracy check on a seeded test set fails (details in section 7).

---

## 1. Demand and stakes

### Dispensing errors
- **India:** a monitoring study (IJPER) found **160 dispensing errors in 12,340 prescriptions monitored, a 1.29% error rate**.
  - Error types: wrong drug, wrong strength, wrong dosage form, wrong quantity, omission.
  - Errors peaked at busy hours. The main cause was too few pharmacists. ([IJPER](https://www.ijper.org/article/1116))
  - This was a hospital outpatient setting. Data on independent chemists is thinner, and the same paper notes that error-reduction efforts are rarely in place at pharmacies not attached to a hospital.
- **Southern India:** community-pharmacy medication-error reporting was set up in a study that recorded 1,416 medication errors among 514 participants. ([ISPOR 2020](https://www.ispor.org/heor-resources/presentations-database/presentation/euro2020-3282/107429))
- **International:** a review of community pharmacies pooled 516 errors in 23,455 prescriptions (about 2.2%). ([PMC12091811](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12091811/))
- **SEA:** data is sparse. A systematic review found only one study each from the Philippines and Indonesia, so the evidence gap is itself a talking point. ([PLoS One SEA review](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4560405/))

### Illegible prescriptions
- **Kerala pharmacist survey (2024):**
  - 80.8% reported legibility problems.
  - 25% receive illegible prescriptions frequently.
  - **64.4% named dispensing errors as the most common outcome.**
  - ([IJPER survey PDF](https://www.ijper.org/sites/default/files/IndJPhaEdRes-55-2s-340.pdf), via search summary)
  - Other Indian audits put the illegible share at 11.5-17.6%. ([PMC3562966](https://pmc.ncbi.nlm.nih.gov/articles/PMC3562966))
- **Punjab & Haryana HC, 27 Aug 2025 (Yogesh v. State of Haryana, Justice J.S. Puri):**
  - A legible prescription is part of the right to health under Art. 21.
  - Doctors must write in capitals until prescriptions are typed or digital.
  - The government must roll out a digital prescription system within 2 years.
  - ([MedicalDialogues](https://medicaldialogues.in/news/health/doctors/legible-prescriptions-a-fundamental-right-punjab-and-haryana-hc-directs-doctors-to-use-capital-letters-154332), [Business Standard](https://www.business-standard.com/health/fix-handwriting-shift-to-digital-prescriptions-high-court-tells-doctors-125100600501_1.html))
  - A follow-up piece reports little change on the ground. ([SouthFirst](https://thesouthfirst.com/health/why-are-legible-prescriptions-still-mystery-in-indias-healthcare-despite-court-order/))
- **Orissa HC (Justice S.K. Panigrahi):** directed the Chief Secretary to require prescriptions and medico-legal reports to be in capitals or legible handwriting. ([LiveLaw](https://www.livelaw.in/high-court/orissa-high-court/orissa-high-court-orders-doctors-prescriptions-legible-handwriting-246119))
- **NMC, Dec 2025:**
  - Medical colleges must set up a prescription-monitoring sub-committee under the drugs and therapeutics committee, and add legible handwriting to the curriculum. ([Careers360](https://news.careers360.com/nmc-medical-colleges-directive-sub-committee-dtc-monitor-prescription-legible-handwriting-generic-drugs-right-to-health/amp))
  - IMC Regulations 2002, clause 1.5 already require legible prescriptions using generic names, preferably in capitals.
  - The Health Ministry says breaching the generic-prescribing rules is misconduct. ([MedicalDialogues](https://medicaldialogues.in/news/health/doctors/non-compliance-with-nmc-regulations-on-generic-prescriptions-is-professional-misconduct-attracts-disciplinary-action-health-ministry-160932))
  - **Why this helps the pitch:** more generic prescribing means the chemist must map a generic name to whatever brand they stock. That substitution step is where wrong-strength and LASA errors happen.

### LASA brand confusion in India
- **Lancet Regional Health SE Asia, July 2024** (Neelakantan, Sharma, Kulkarni), "LASA drugs in India", calls LASA an unaddressed public-health problem. ([DOAJ](https://doaj.org/article/356f0b1c9fd84768a6350339f5a8ae45), [SouthFirst](https://thesouthfirst.com/health/look-alike-sound-alike-medicine-in-indian-market-can-cause-significant-health-threat-lancet/))
  - Same name for different molecules:
    - **Linamac:** lenalidomide (cancer) and linagliptin (diabetes)
    - **Medzol:** pantoprazole and midazolam
    - **Flucor:** fluconazole and melitracen+flupentixol
  - Names that sound alike: **Olvance** (hypertension) vs **Oleanz** (schizophrenia).
- One Indian analysis looked at **304 LASA brand pairs with different generic compositions**. Another found LASA accounts for about 2.67% of reported hospital medication errors. ([STM Journals](https://stmjournals.nanoschool.in/index.php/RRJoP/article/view/6852), search summary)
- **Regulators:**
  - Jan 2024: DTAB recommended banning different drugs under the same brand name. ([Mondaq](https://www.mondaq.com/india/healthcare/1503746/look-a-like-sound-a-like-lasa-drugs-a-multifaceted-challenge))
  - 17 Nov 2025: the 67th Drugs Consultative Committee discussed it.
  - **6 Jul 2026:** CDSCO notice inviting comments on brand-name extensions, with a deadline of 17 Jul 2026. ([SpicyIP](https://spicyip.com/2026/07/brand-name-extensions-by-pharma-may-finally-be-receiving-scrutiny.html), [SouthFirst](https://thesouthfirst.com/health/why-one-drug-brand-can-no-longer-mean-one-medicine-cdsco-moves-to-tackle-confusing-brand-name-extensions/))
  - **There is no official CDSCO LASA list.** SpicyIP criticises CDSCO for ignoring LASA in that notice.
  - This is an opportunity: generating a LASA-risk index from the roughly 254k-brand dataset is itself a novel output (see section 5).

### Schedule H1 register
- **Rule 65(3A)** of the D&C Rules 1945, added by GSR 588(E) of 30 Aug 2013. ([Wikipedia](https://en.wikipedia.org/wiki/Drugs_and_Cosmetics_Rules,_1945), [CliniExperts](https://cliniexperts.com/fourth-amendment-in-drugs-cosmetics-rules-2013/), [NTEP](https://ntep.in/node/938))
  - Every supply of a Schedule H1 drug must go in a **separate register at the time of supply** with:
    - prescriber name and address
    - patient name
    - drug name
    - quantity
  - Records are kept **3 years** and open for inspection.
  - Schedule H1 covers 46 drugs: 3rd/4th-generation antibiotics, anti-TB drugs and habit-forming drugs. ([Herald Goa](https://www.heraldgoa.in/goa/sale-of-46-drugs-regulated/408807))
- **Enforcement is real:**
  - J&K: shops sealed and licences suspended over H1 violations, including not keeping computerised sale records. ([Greater Kashmir](https://m.greaterkashmir.com/article/shop-selling-schedule-h1-drugs-without-valid-prescription-sealed-in-poonch-licence-suspended/456599), [Kashmir Life](https://kashmirlife.net/drug-control-department-seals-medical-shop-over-schedule-h1-violations-441141/))
  - J&K drive: 278 inspections led to 54 licences suspended. ([Kashmir Reader](https://kashmirreader.com/?p=254876))
  - Bhopal: 32 stores acted on. ([FPJ](https://www.freepressjournal.in/bhopal/action-against-32-medical-stores-licences-of-three-suspended-eight-registrations-cancelled))
- **AMR motivation:** a simulated-patient study found antibiotics dispensed without a prescription at 76% of pharmacies, and sales without a prescription continued even after H1 education. ([IJCMPH](https://www.ijcmph.com/index.php/ijcmph/article/view/13853), [PMC8092171](https://pmc.ncbi.nlm.nih.gov/articles/PMC8092171))
- **How it is kept today:** a paper notebook, or typed fields in an ERP (Gofrugal and Marg prompt for doctor and patient details on H1 items). ([Gofrugal](https://gofrugal.com/blog/schedule-h1-drugs))
  - A vendor estimate puts manual register work at about **260 hours/year per shop**. This is Nesayo's marketing claim, not independent data. ([hunted.space](https://hunted.space/product/nesayo))

### Scale and staffing
- AIOCD says there are **12.4 lakh** chemists and druggists, about 1.24M. ([ETV Bharat](https://www.etvbharat.com/en/bharat/aiocd-seeks-pms-intervention-in-illegal-online-medicine-sales-enn26052005633))
- AIOCD itself cites a "severe shortage of qualified pharmacists" and has asked that staff with only a condensed pharmacy course be allowed to dispense. ([Tribune](https://www.tribuneindia.com/news/amritsar/consult-chemists-before-finalising-list-of-over-the-counter-medicines/amp))
- Inspections regularly find shops selling with no pharmacist present. ([FPJ](https://www.freepressjournal.in/bhopal/action-against-32-medical-stores-licences-of-three-suspended-eight-registrations-cancelled))
- **SEA analog for the expansion story:** in Malaysia, Group C poisons may be sold only with an entry in the **Prescription Book** (Form C, kept 5 years) under the Poisons Act 1952. ([MOH Malaysia](https://pharmacy.moh.gov.my/sites/default/files/document-upload/poisons-act-1952-act-3662_0.pdf))

---

## 2. Prior art: products

| Product | What it does | Pack-vs-Rx check? | H1 register? | LASA? | NSQ? |
|---|---|---|---|---|---|
| **Nesayo** (India, 2026) | Pharmacy operating system. Photo prescription scan with Claude Vision drafts the bill. Voice billing in 10 languages. FEFO batch selection. **Auto Schedule H1 register** (3-year retention, SHA256 audit chain). ₹399-2,999/mo. [techjockey](https://www.techjockey.com/detail/nesayo), [hunted.space](https://hunted.space/product/nesayo) | **No** (not documented) | **Yes** | No | No |
| **Alkem DawAI Reader** (2025-26, Lowe Lintas campaign, Spikes Asia shortlist) | Device for rural chemists. Trained on more than 1 lakh prescriptions; reads drug and dose aloud in local languages. Piloted in 250+ villages. Says it is not a medical device under MDR 2017. [lovethework](https://www.lovethework.com/work/campaigns/dawai-reader-1952472) | No | No | No | No |
| Google handwritten-prescription prototype (Dec 2022, Lens) | Highlights medicine names on a prescription. Still a research prototype; no confirmed rollout. [Fierce](https://www.fiercebiotech.com/medtech/google-aims-translate-hand-scribbled-doctors-notes-and-prescriptions-using-ai) | No | No | No | No |
| Tata 1mg, PharmEasy, Truemeds, Netmeds, MedPlus | Customer uploads a prescription; a pharmacist reviews it for the e-order | Only inside their own warehouse workflow | n/a | n/a | n/a |
| Marg, Gofrugal, LogicERP, BitMed | Typed billing. **Blocks H1 sale without doctor and patient fields**; H1 report. [Gofrugal](https://gofrugal.com/blog/schedule-h1-drugs), [LogicERP](https://kb.logicerp.com/logic-erp-in-action-a-feature-overview/distribution/billing/special-checks-for-schedule-h-and-narcotics-items-disallows-users-to-sell-the-products-without-patie) | No | Typed by hand | No | No |
| Hospital barcode dispensing / Omnicell / Parata robots | Scan the barcode against the order | Yes, but needs barcoded stock and an electronic prescription; not for small chemists | n/a | n/a | n/a |
| **InterLink AI (formerly PerceptiMed)**: identRx, veriFill (US) | Pill-level vision ID and remote pharmacist verification. [DrugStoreNews](https://www.drugstorenews.com/perceptimed-rebrands-become-interlink-ai) | **Yes**, for US vials and pills from e-prescriptions | n/a | n/a | n/a |
| Research: JMIR human-centred AI dispensing verification (US, 2023) | Neural network predicts the pill's NDC and the UI flags a mismatch. [PMC10775023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10775023/) | Yes (research only) | | | |
| Research: Qwen3-14B prescription review (India, JMIR Med Inform, Sep 2026) | Human plus AI reached 97.2% vs 82.6% for the pharmacist alone, on 213 outpatient prescriptions; drug-interaction catches. [Omnicuris summary](https://www.omnicuris.com/medshots/daily_updates/locally-deployed-ai-outpatient-prescription-review_15-Sep-26_05-04) | No (reviews the prescription, not the pack) | | | |
| **MedShield** (Devpost) | Batch number typed in, checked against CDSCO NSQ PDFs. [Devpost](https://devpost.com/software/mshield) | No | No | No | Yes (typed) |

**Takeaways:**
- In 2026, "photo of the prescription → bill → H1 register" is **already a product** (Nesayo).
- Nobody we found reconciles the **physical pack being handed over** against the prescription in a small-chemist setting. A US system (InterLink AI) does pack verification for e-prescriptions only.

## 3. Prior art: hackathons and GitHub

- **Prescription reading with Gemini or another VLM is very crowded:**
  - PharmaBot (Gemini OCR) ([ReadyTensor](https://app.readytensor.ai/publications/pharmabot-a-prescription-analyst-ircy6qc747ih))
  - MedScript / Clinnovators (OCR plus price comparison) ([GitHub](https://gh.nn.ci/Hiteshgottapu/Clinnovators))
  - Script+ Reader on Hugging Face ([HF](https://huggingface.co/shadowfurynon/prescription_reader))
  - **Aushadhi Vault** (lablab AMD hackathon, May 2026): Llama 3.2 Vision reads a handwritten prescription, auto-bills and deducts inventory. No pack verification, no H1 register, no NSQ, no LASA. ([lablab](https://lablab.ai/ai-hackathons/amd-developer/wtf-ninja/aushadhi-vault))
  - **RXPro** (lablab AI Genesis, Nov 2025): Gemini 2.5 Pro point-of-sale assistant with prescription analysis, interaction and dose "RED ALERT"s for pharmacist review, and counselling notes. **This is the closest hackathon overlap on the interactions part.** No pack photo, no H1 register, no NSQ. ([lablab](https://lablab.ai/ai-hackathons/ai-genesis/icare-ai/rxpro-ai-pharmacy-pos-assistant))
  - MediConnect (Devpost): OCR on a strip photo to autofill donations. ([Devpost](https://devpost.com/software/mediconnect-ecosysytem))
- **Pack-vs-prescription verification for dispensing:**
  - Searches on Devpost, lablab and GitHub ("verify dispensed medicine prescription", "medicine strip photo match prescription", "pharmacy dispensing check") returned **no matching project**, only US patents (e.g. US 9886751, 10896752, 12580061, which cover imaging pharmacy verification).
  - **Patent note:** the US vial-imaging patents exist, but they are not a concern for a hackathon in India.
- **LASA detection software:** University of Tasmania research tool; FDA POCA. ([UTAS](https://figshare.utas.edu.au/articles/journal_contribution/Development_and_exploratory_analysis_of_software_to_detect_look-alike_sound-alike_medicine_names/22987349)) No India-brand LASA tool or GitHub repo found.
- **Searches for an H1 register hackathon project or GitHub repo found nothing.** Nesayo is the commercial instance.

## 4. AI Builder Cup competitor list

- Searched `COMPETITOR_ENTRIES.md` (177 lines, about 105 entries) for pharm, prescri, medic, drug, chemist, dispens, health, batch, recall, H1.
- **No overlap.** The only health-adjacent entries:
  - Kavach: health-insurance claim appeals
  - Swasthya Sync: patient case-taking showcase
  - NextStep: medicine photo sent to a doctor
- The nearest Retail entry is Hanga (photograph an Indonesian warung's stock notebook to get restock advice). It is a different domain, but it shows the photo-to-ledger pattern is in the field.

## 5. Metrics and demo data

### Before and after metrics
1. **Seeded-error catch rate (the headline).**
   - Build 60-100 dispensing cases: prescription image plus pack photo.
   - About 40% contain a seeded error:
     - wrong strength (Pan 20 vs Pan 40)
     - LASA swap (Olvance vs Oleanz, Medzol pair)
     - wrong form (syrup vs tablet)
     - quantity short or over (5-day course vs 1 strip of 10 for BD dosing)
     - expired pack
     - an NSQ-listed batch (a real batch from a CDSCO PDF printed on a mock strip)
   - Report recall and precision per error type, and the **abstain rate**.
   - Compare against a baseline of "an untrained counter assistant reading the same prescription," using 2-3 human volunteers.
2. **Time per Schedule H1 entry:** a manual paper entry (time it, likely 60-120 s) vs one tap to approve (about 5 s).
   - With a typical count of H1 sales a day, convert this to hours a year. Cite Nesayo's 260 h/yr claim as a vendor estimate only.
3. **Missing H1 fields at inspection:** register completeness, measured as the share of entries with all 4 Rule 65(3A) fields. Before: an audit of a photographed sample register. After: 100%, enforced by the schema.
4. **NSQ exposure at the counter:** the share of dispensed packs checked against current NSQ lists. Before: about 0%. After: 100%.

### Data sources
- **Doctor's Handwritten Prescription BD** (Kaggle mamun1113 / Mendeley): 4,680 word crops, 78 brand classes. Words only, not full prescriptions. ([Mendeley](https://data.mendeley.com/datasets/zjjtptvn6f))
- **RxHandBD**: handwritten prescription word images. ([Mendeley](https://data.mendeley.com/datasets/dsb5r6vskg/3))
- **MIRAGE**: 743k simulated Indian prescription images (paper; check release). ([arXiv 2410.09729](https://arxiv.org/html/2410.09729v2))
- **RxScribe Bench**: 200 real Indian outpatient prescriptions. Release not stated; email the authors. ([arXiv 2609.13280](https://arxiv.org/html/2609.13280))
- **A-Z Medicine Dataset of India** (Kaggle shudhanshusingh): about 254k brands with composition and manufacturer, prices as of Nov 2022. Use it for brand-to-generic mapping and to **generate LASA candidate pairs** with Gemini embeddings plus string and phonetic similarity across different compositions. ([Baselight mirror](https://baselight.app/u/kaggle/dataset/shudhanshusingh_az_medicine_dataset_of_india))
- **CDSCO NSQ/spurious monthly PDFs**, already analysed in `medicine_food_safety.md`: text-based, stable 8-column table.
- **Seed LASA pairs:** the Lancet 2024 examples, the 304-pair study, and the ISMP confused-names list (US) as a template.
- **Practical approach:**
  - Have 5-10 people, ideally a doctor friend, handwrite about 40 realistic prescriptions on Indian letterhead templates.
  - Photograph real strips from a household medicine box and a cooperative local chemist.
  - Use public datasets for the eval and our own images for the stage demo.

## 6. Risks

- **Handwriting accuracy** (the critical risk):
  - **RxScribe Bench (Sep 2026)** tested 200 Indian handwritten prescriptions × 3 runs against GPT-5.6, Gemini 3.1 Pro, Muse Spark 1.2 and Claude Opus 5.
    - Medicine-table correctness peaks at **57.83%** (GPT-5.6), with a low of 47.08%.
    - The medicine table scores 20-29 points worse than other fields.
    - **Gemini 3.1 Pro:** about 3.06 fabrications per run, attempts the most hard fields, and is the least stable from run to run.
    - Most fabrications are inferred generic names.
  - **MIRAGE:** off-the-shelf Gemini 1.5 Pro scored 5.65% precision on its simulated set.
  - **Mitigation design:**
    - **(a) Read the printed pack first.** Printed text is easy.
    - **(b) Constrained verification:** ask whether this prescription line is consistent with the brand, generic and strength printed on the pack, with candidates from the 254k dataset. This is easier than open transcription.
    - **(c) Blind read before the comparison**, so the model does not just confirm what it expects (confirmation bias is the specific failure in "verification" framing).
    - **(d) Multiple samples with a self-consistency vote**; if they disagree, abstain and show "can't read: confirm with patient/doctor."
    - **(e) Generic/composition-level matching** through the dataset rather than brand-string matching.
  - Present the abstain rate honestly. Judges reward that more than inflated accuracy.
- **Regulatory and liability:**
  - Dispensing responsibility stays with the registered pharmacist (Pharmacy Act 1948; Pharmacy Practice Regulations 2015).
  - Keep the tool a **checklist and record assistant**: no "safe to dispense" verdicts, no dosing advice to patients.
  - Software that informs diagnosis or treatment can fall under Medical Device Rules 2017 as software-as-a-medical-device. A dispensing-verification and record tool is arguably outside it; DawAI Reader makes the same claim.
  - Interaction checking is the most "clinical" part. Keep it to well-known severe pairs from a cited source, labelled "verify".
- **H1 register legal form:**
  - The rule requires the record to be made "at the time of supply" and kept for 3 years.
  - A digital register is accepted in practice (ERPs print H1 reports; J&K cited missing "computerised" records). Still, state Drug Controllers may expect a printed or signed copy. Offer a daily signed PDF.
- **Privacy (DPDP Act 2023; Rules notified 13 Nov 2025; substantive duties from 13 May 2027):**
  - Prescriptions are sensitive personal data.
  - Needed: notice and consent at the counter, purpose limitation, retention matched to the legal 3 years then deletion, a 72-hour breach notice, and India-region storage (asia-south1). ([DPDPA timeline](https://www.dpdpa.com/blogs/DPDPA_Implementation_Timeline.html))
  - Do not use prescription images for training without consent.
- **Overlap perception:** a judge who has seen dozens of "Gemini reads doctor handwriting" projects may dismiss it in the first 10 seconds.
  - **Open the demo on the pack in hand, not the prescription:** "the strip is the wrong strength". Never open on "look, it reads handwriting."
- **Scope creep:** six checks plus register plus sale record is a lot for 2 people in 7 days.
  - **Core checks:** drug/strength/form match, LASA, quantity/duration, expiry, NSQ batch.
  - **Lighter:** interactions, limited to a short curated list.
  - **Last:** the H1 register.

## 7. Counter Check vs BatchWatch

| Criterion (weight) | Counter Check | BatchWatch (invoice → recall match → quarantine paperwork) |
|---|---|---|
| Technical and GenAI (40%) | **Stronger showcase:** cross-image multimodal reasoning (handwriting plus printed pack), constrained verification, abstention, embeddings over 254k brands for LASA, and an agentic checklist. **Also higher risk:** published accuracy is about 50-58% on the medicine table. | Solid but plainer: invoice extraction, PDF table parsing and fuzzy matching. Matching is mostly deterministic, so it is reliable but less "GenAI". |
| Problem and impact (25%) | **Strong and frequent:** every sale, every shop, and a patient-harm story (Linamac cancer vs diabetes). Ties to HC orders, NMC, CDSCO's 2026 brand notice, AMR and H1 inspections. | Strong but episodic: about 220-280 NSQ batches a month nationally, so an individual shop rarely has a hit. Impact is real, but the demo story is "what if". |
| Innovation (25%) | **Partially done:** prescription reading and the H1 register already exist (Nesayo, Aushadhi Vault, RXPro, DawAI). The novel part is pack-vs-prescription reconciliation plus LASA plus NSQ at the counter. Novelty is moderate and depends on framing. | **More clearly novel:** stock-wide, retroactive matching plus quarantine and return paperwork. Nearest is MedShield (single typed batch). No ERP does it. Novelty is moderate-high. |
| UX (10%) | **Great live demo:** two photos, a red "strength mismatch: Rx 40 mg, pack 20 mg" flag, one-tap register entry. | Good: a stack of invoices turns into alerts and PDFs. Less visceral. |
| Buildability, 2 people / 7 days | Medium-hard: the eval set has to be hand-made. | High: public PDFs, synthetic invoices. |
| Demo failure risk | Medium-high: live handwriting misreads. Use pre-tested prescriptions on stage. | Low. |

**Recommendation:**
- **Counter Check has the higher expected score, but only if scoped and framed well:**
  - Make "the pack in hand vs the prescription" the hero.
  - **Include BatchWatch's NSQ engine as one check on that pack** (batch read from the strip photo), so the recall novelty carries over.
  - Treat the H1 register as a by-product.
  - Report an honest seeded-error eval with abstention.
- **Gate on day 3 (Oct 13):**
  - On 30 seeded cases, catch at least 80% of strength, form and LASA mismatches with a false-alarm rate of 15% or less on clean cases (abstentions allowed).
  - If it falls short, pivot to BatchWatch, adding a counter-time "scan strip → NSQ/expiry" check as the UX hook.
- A combined pitch line works for either: **"One photo of the strip at the counter: is it what the doctor wrote, is it in date, is it on CDSCO's fail list? Then the H1 register writes itself."**

## 8. Suggested architecture (for completeness)
- **Front end:** Firebase Hosting PWA, camera-first. Two shots: prescription, then pack (or several packs).
- **Back end:** a Cloud Run (FastAPI) pipeline:
  1. Gemini 2.5 Pro / 3.x vision reads the pack into structured output: brand, generic, strength, form, batch, mfg and expiry dates, manufacturer.
  2. A blind read of the prescription produces line items with a per-field confidence.
  3. Candidate retrieval from the 254k medicine table (Firestore or BigQuery plus Gemini embeddings).
  4. Reconciliation agent (ADK): match, quantity versus duration, LASA index lookup, NSQ batch lookup, expiry, and a short curated interaction list.
  5. Flags with evidence crops, then pharmacist approval, then an H1 entry plus sale record in Firestore and a daily signed PDF.
- **Optional:** Gemma (on device) for a pack-only offline pre-read, to show "Gemma + Gemini".
- **Data:** asia-south1 region, a consent banner, and a 3-year retention TTL.
