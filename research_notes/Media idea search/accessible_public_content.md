# Accessible Public-Interest Content: JAPAC Gap Research

Date: 2026-10-10 | For: Google Cloud AI Builder Cup 2026, theme "Media, Content & Digital Experiences" (deadline Oct 18)
Constraint: skip what other Media teams already do (audio description/Gapline, ad localization/OmniLocate, cricket analytics/SEEN, textbook-to-lessons).

---

## TL;DR

- **Generic "simplify any document with an LLM" already exists.** Japan: Hitachi Social Information Service, 伝えるウェブ (Alphasade), Yonago City's whole-site AI conversion, Setagaya's chat rewriter. Global: Photosymbols EasyMaker, Dentsu "Easy Reading" (on AWS), UK "Simply Readable" (AWS, NDX catalogue), Intelife/UWA Easy Read Generator (Australia), Korea EQ4ALL 쉬운정보. Hackathons: PlainSpeak on Devpost (Gemini + ElevenLabs) and cleardoc. (Gemini API competition, medical simplifier). A generic simplifier will score low on Innovation.
- **The open gap is narrower: issuer-side, safety-checked conversion of high-stakes instructions.** Today nothing checks that the critical facts (doses, dates, amounts, red-flag symptoms, where to go) survive the simplification, and nothing produces the multi-format pack (Yasashii Nihongo with furigana, native language, audio, pictograms) with a staff sign-off step. Japanese research says plainly that LLM simplification "omits information or produces incorrect sentences, so human review is needed". That review step is what we would build.
- **Sign language: too hard for 8 days. Confirmed.** Minority-language radio archives: poor demo data, consent issues, and weak model quality for Ainu and Aboriginal languages. Skip both.

---

## 1. Plain language / Yasashii Nihongo / Easy Read

### Demand evidence (verified)
- **Foreign residents in Japan: 4,125,395 at end of 2025.** That is +9.5% year on year, 3.36% of the population, and the first time above 4M. It is the 4th straight record (ISA, reported Mar 2026). Mid-2025 was 3.95M. Top nationalities: China ~930k, Vietnam ~681k, Korea ~407k, Philippines ~356k, Nepal ~300k. Specified Skilled Worker status: 390k (+37.2%). Sources: nippon.com/ja/japan-data/h02750/, sakigake.jp 20260327.
- **76% of foreign residents name Yasashii Nihongo as their preferred information language.** That is the top choice, ahead of English at 44% for daily-life language. Source: ISA/Agency for Cultural Affairs, 在留支援のためのやさしい日本語ガイドライン (Aug 2020). The guideline also has rules we can encode: short sentences, no double negatives, ruby (furigana) on kanji, Western-calendar dates, and so on.
- **Disasters:** after the Noto earthquake (2024), studies found foreign residents could not tell whether to go home or go to a shelter, and got unclear instructions from employers. The studies recommend putting Yasashii Nihongo first. NTT Docomo Area Mail added Yasashii Nihongo for emergency alerts.
- **Municipal generative-AI adoption (2025):** prefectures 87.2%, designated cities 90.0%, other municipalities 29.9%. So small towns, where many technical-intern workers live, are the least served.
- **Australia:** in PIAAC 2011-12, 3.7% (620k) of adults were below Level 1 literacy and 10% (1.7M) were at Level 1. A new national study is due mid-2026.
  - Human Easy Read production takes 2-3 weeks for documents up to 1,000 words, 3-4 weeks up to 2,000, and 5+ weeks for longer ones.
  - Cost is about £120/page, or £290 (≤1k words) to £1,452 (5k words) (DES Scotland 2026 price list).
  - Australian vendor: Information Access Group.
- **Korea:** "쉬운 정보" (easy information) is required for people with developmental disabilities. Easy-read provision in Korea is mostly still manual.

### Existing tools (prior art)
| Tool | What | Gap |
|---|---|---|
| NHK News Web Easy | Human-edited easy news with furigana and audio | News only, a few stories a day, not local or personal |
| Hitachi SIS やさしい日本語変換 (2022) | Website-wide AI conversion plus ruby. ¥150k setup + ¥35k/month | Web pages only, no fact-fidelity check, no audio or pictograms |
| 伝えるウェブ (Alphasade) | AI paraphrase to Yasashii Nihongo plus an editor. Used across Tokyo since 2022 and has disaster webinars | Web CMS, reader-side output only |
| Yonago City / Setagaya | AI conversion of the whole site; generative-AI rewrite in a chat tool | Same |
| Docomo Area Mail | Yasashii Nihongo emergency alerts | Fixed template messages |
| SNOW T15/T23, JADOS, MultiLS-JA | Simplification corpora (Hugging Face) | Data we can use for evaluation |
| Photosymbols EasyMaker (UK) | AI Easy Read with symbol images, exports to PDF/audio/web | UK English, paid, not JAPAC |
| Simply Readable (UK gov NDX, AWS) | LLM Easy Read | UK |
| Intelife + UWA Easy Read Document Generator (WA) | Student-intern prototype since 2024 | Early, English only |
| Dentsu Creative "Easy Reading" | AWS, Easy-to-Read standard | Marketing showcase |
| EQ4ALL (Korea) | AI 쉬운정보 plus a sign avatar; used on Jeju disaster texts and the National Pension Service | Korea, commercial |
| arXiv 2603.13695 | Easy Read pictogram generation with Stable Diffusion + LoRA | Research; it validates pictogram generation |
| PlainSpeak (Devpost) and cleardoc. (Gemini competition) | Generic Gemini simplifier with TTS | Generic, no fidelity check, no issuer workflow |

GitHub has no strong open-source "Yasashii Nihongo plus fact-verification" project. Searches for "yasashii nihongo LLM" return learning tools (Yasashii Sensei) and corpora.

### Verdict
- Generic converter: **ALREADY EXISTS**.
- Issuer-side "critical-fact-locked" multi-format pack with human sign-off: **PARTIALLY DONE**. Nobody verifies fidelity, and nobody combines pictograms, audio and native language in one output.

---

## 2. Patient-facing medical content in local languages

### Demand evidence
- **Japan MHLW 2025 survey of foreign-patient acceptance (published Sep 2026):**
  - 54.6% of hospitals have treated foreign patients.
  - 66.8% don't track foreign-patient visits, 87.7% have no reception policy, and only 2.8% employ a foreign-patient coordinator.
  - 47.9% of medical regions have on-site interpreters.
  - 15.7% of hospitals reported unpaid bills (avg ¥583k). Misunderstanding is a common root cause.
- **Patient experience:** in Musashino City's survey of foreign residents, 26.1% "cannot communicate with doctors/nurses due to language", the #2 inconvenience. A 2025 survey of 302 foreign residents rated "clarity of explanations" 2.67/5. A NINJAL survey found more than 80% had trouble with doctors' terminology.
- **Research:** a KAKEN 2024-26 project is testing Yasashii Nihongo in medical interpreting. Juntendo/Teikyo/Seishin published video phrase sets in Yasashii Nihongo for clinics. That is static content, not generated per patient.
- **India and Southeast Asia:**
  - Yogyakarta: 67.3% of patients have limited health literacy.
  - Philippines: in user testing of medicine leaflets, fewer than half the participants understood them.
  - Sri Lanka RCT: native-language discharge summaries improved knowledge, and 92.1% of patients preferred them.
  - Punjab paediatrics: 27% of caregivers did not understand medication instructions.
  - US: only 8% of patients with a non-English preference got discharge instructions in their language.

### Prior art
- **PostVisit.ai** (Belgium cardiologist): 3rd place in Anthropic's Feb 2026 hackathon. It is a post-visit agent covering visit summary, medications and follow-up. English/EU, patient-side.
- **India:**
  - Amrita MedSum turns consultations into voice summaries in Hindi, Tamil and Bengali. This is close to "discharge audio in dialect".
  - Iksha Labs and Edesy run voice bots in 22 languages.
  - Commercial video makers (Leadde, InVideo, HeyGen) do discharge videos in 88 languages, but as generic marketing tools.
- **Google:** MedGemma Impact Challenge (850+ submissions). Gemma 3n Impact 2nd place went to Vite Vere (simple instructions for people with cognitive disabilities). Gemma 4 Good: PreVillage (Nepal government-services navigator), MindBridge (Hindi dialects), KawanIsyarat (Indonesian sign language, BISINDO). Judges have seen "LLM explains a medical document in my language" many times.
- **Japan:** medimo (AI summary of the doctor's explanation, for Japanese patients). Interpreter tablets are at 96.7% of regions. No product found that generates a Yasashii Nihongo after-visit pack plus native language, audio and pictograms, with a fact check.

### Verdict
- India/Indonesia/Philippines discharge audio or video in regional languages: **PARTIALLY DONE, crowded** (MedSum, vendors, many hackathon clones).
- Japan clinic to foreign-patient pack with Yasashii Nihongo + native language + dose-pictogram + audio, with a clinician-approved fact lock: **NOVEL in this exact combination.**

---

## 3. Sign language (JSL / KSL / Thai SL / ISL)

- Existing work:
  - NHK KIKI: photoreal digital human, first text-to-JSL engine for emergency alerts, Deaflympics 2025 ambassador.
  - NHK sign CG, in R&D since 2012.
  - Thai PBS avatar project for Thai Sign Language news.
  - EQ4ALL (Korea), Signapse (UK, GAN photoreal), Hand Talk (Brazil).
  - KawanIsyarat (Gemma 4 Good winner, Indonesian Sign Language recognition).
- Why it is too hard:
  - Sign production needs grammar (non-manual markers, use of space) and motion datasets.
  - Veo/Imagen cannot produce correct signs. Wrong signs are harmful, and Deaf communities push back on poor avatars.
  - A non-signer team can't validate output in 8 days.
- **Verdict: ALREADY EXISTS (well-funded) and NOT BUILDABLE. Skip.**

---

## 4. Minority-language public broadcasting / community radio archives

- Australia: First Nations media hold 40+ years of recordings, with a digitisation race against degrading tape. Community radio Code 7 (First Nations engagement) took effect 1 Jul 2025. Ainu has very few speakers. Philippine regional languages (Cebuano, Ilocano, Hiligaynon) are well covered by Gemini.
- Gemini Flash TTS now lists 130+ languages, including long-tail ones like Acehnese. Philippine and Indonesian regional languages are probably feasible; Aboriginal languages and Ainu are not.
- Problems:
  - Indigenous Cultural and Intellectual Property and data-sovereignty consent (CARE principles).
  - No public demo data we are allowed to process.
  - Low model quality.
  - Hard to show a before/after number.
- **Verdict: PARTIALLY DONE (archive digitisation and human projects). Risky and hard to demo. Skip**, except as a variant: a Philippine community-radio "public notice to Cebuano/Ilocano audio bulletin". That is weaker than idea A below.

---

## Ranked idea framings

### A. "Yasashii Clinic Pack" (rank 1): NOVEL (combination) / PARTIALLY DONE (parts)
**Named user:** the nurse or medical clerk at a Japanese community clinic or hospital international desk (e.g., Gunma Oizumi, Aichi Toyota, or a Tokyo ward clinic serving Vietnamese/Nepali/Filipino workers). Secondary user: the foreign patient.

**Workflow:**
1. Staff photograph or paste the after-visit sheet, prescription label or vaccine leaflet.
2. Gemini extracts a **Critical Facts Ledger** (drug, dose, times/day, days, before/after meals, red-flag symptoms, next appointment date/place, cost/insurance).
3. Gemini rewrites the content in Yasashii Nihongo following the ISA 2020 guideline (furigana, short sentences, Western dates) and adds the patient's native language (Vietnamese, Nepali, Tagalog, Indonesian, Portuguese).
4. **Fidelity checker:** a second Gemini pass back-extracts the facts from each output and diffs them against the ledger. Any mismatch is flagged red, plus a guideline lint score.
5. Imagen generates a dosing pictogram card (sun/moon, meal, pill count) and Gemini TTS creates an audio version.
6. Staff approve (human-in-the-loop), and the system issues a QR code. The patient scans it and gets a mobile page with audio plus a 3-question "teach-back" quiz. Quiz results go back to the clinic.

**Stack:** Gemini 2.5/3 Pro (structured output, long context), Gemini TTS, Imagen 4 (pictograms), Cloud Run + Firestore, optional Gemma for on-prem/PII redaction. Deep sponsor-tech usage.

**Before/after metrics:**
- Staff time per multilingual instruction sheet (manual or interpreter: about 20-40 min or unavailable, versus under 2 min plus review).
- Fact-fidelity: % of critical facts preserved. Report naive LLM simplification vs. our ledger-checked pipeline on 30 sample sheets. This makes a strong technical slide.
- Patient teach-back quiz score: original Japanese vs. pack.
- Guideline compliance score from the ISA rules.

**Demo data:**
- Public sample 説明書/お薬手帳 templates.
- MHLW and prefecture multilingual foreign-patient materials, which give ground-truth translations.
- Synthetic prescriptions.
- SNOW T23 corpus for evaluating simplification.

**Buildable in 8 days:** yes. The pipeline is text plus image plus TTS, and the hard part (the fidelity diff) is prompt-engineering plus JSON.

**Risks:** it may read as "healthcare" rather than "media", so frame it as accessible content creation, personalisation and understanding. Imagen pictogram consistency is a risk; mitigate with a fixed icon set plus Imagen only for the illustrations.

### B. "City Hall Letter to Easy Pack" (rank 2): PARTIALLY DONE
**Named user:** the 多文化共生 (multicultural coexistence) officer at a small municipality, the 70% that have no generative AI. Content: resident-tax, National Health Insurance, pension, garbage-rule and evacuation notices.

**What it does:** the same ledger-locked conversion, with deadline, amount and where-to-go facts. Outputs are Yasashii Nihongo with ruby, native language, an audio file for the disaster-radio or LINE broadcast, and an illustrated one-page notice.

**Metric:** officer hours per notice vs. outsourced translation (days and ¥), and fact fidelity.

**Prior art:** Hitachi, 伝えるウェブ and Yonago cover websites only, with no fact check and no audio or pictograms. Reader-side photo-translate apps (Google Lens and others) exist for individuals. Differentiation is moderate.

**Variant:** disaster-alert mode. Turn the JMA/municipal alert into Yasashii Nihongo plus 5 languages plus audio in under 60 seconds, with fact lock. Docomo does fixed templates only.

### C. "Easy Read Studio" for Australia/Korea (rank 3): PARTIALLY DONE / near ALREADY EXISTS
**Named user:** an NDIS provider or Australian government comms officer, or a Korean public agency that must publish 쉬운정보.

**What it does:** source document in, Easy Read out (one idea per line, a picture beside each point, 14pt+). Imagen pictograms use a consistent style, and the system adds a fidelity ledger, audio, and co-review by a person with intellectual disability (a "reviewer mode" with large-button approve/flag).

**Metric:** 2-5 weeks and £290-1,452 per document, versus minutes plus review.

**Prior art:** EasyMaker, Simply Readable and the Intelife generator already exist, so Innovation will suffer. The Korean 쉬운정보 version with Gemini Korean is less crowded, but EQ4ALL exists.

### Not recommended
- Sign language (too hard, incumbents).
- Indigenous archive radio (consent and data).
- Generic India/SEA discharge-video-in-dialect (MedSum, Leadde/HeyGen, many hackathon clones).

---

## Recommendation
Go with **A (Yasashii Clinic Pack)**, or merge A and B into a single "high-stakes instruction" engine with clinic as the hero demo and city notice or disaster alert as a second tab. The innovation claim is the **Critical Facts Ledger plus back-extraction diff plus ISA-guideline lint**. It turns LLM simplification from risky into auditable, which is exactly the gap the Japanese research names ("human review necessary because information can be omitted"). Pitch the number as "X% of critical facts lost by naive LLM simplification → 0 unflagged losses with ours" and "clinic staff time 30 min → 2 min".

## Sources
- https://www.nippon.com/ja/japan-data/h02750/ ; https://www.sakigake.jp/news/article/20260327CO0151/
- https://www.moj.go.jp/isa/content/001381623.pdf (ISA/Bunkacho Yasashii Nihongo guideline data)
- https://cir.nii.ac.jp/crid/1050298355878497024 (ChatGPT for administrative Yasashii Nihongo: human review needed)
- https://www.city.yonago.lg.jp/secure/49878/20230209_hishomachiki.pdf ; https://www.city.setagaya.lg.jp/documents/18436/ai-2.pdf
- https://ecnomikata.com/ecnews/35566/ (Hitachi SIS) ; https://tsutaeru.cloud/assets/20250620webinar3_tsutaeruweb_bousai.pdf
- https://weel.co.jp/media/generation-ai-local-government/ (municipal adoption rates)
- https://honichi.com/news/2026/09/18/hospital-inbound/ ; https://www.mhlw.go.jp/stf/newpage_41976.html
- https://www.city.musashino.lg.jp/_res/projects/default_project/_page_/001/035/851/2022houkokushogaiyouenglish.pdf
- https://kaken.nii.ac.jp/grant/KAKENHI-PROJECT-23K24580
- https://huggingface.co/datasets/SNOW-NLP/snow_simplified_japanese_corpus
- https://thiis.co.uk/ai-powered-reading-tool-created-in-collaboration-with-people-with-learning-disabilities-launches/ (EasyMaker)
- https://www.mccuskercentre.uwa.edu.au/news/intelife-easy-read ; https://ndx.digital.cabinet-office.gov.uk/catalogue/aws/simply-readable
- https://disabilityequality.scot/wp-content/uploads/2026/07/DES-Easy-Read-Service-Pricing-Policy-2026-FINAL.pdf
- https://arxiv.org/abs/2603.13695 (Easy Read pictograms) ; https://arxiv.org/abs/2407.20046
- https://devpost.com/software/plainspeak-u174s8 ; https://ai.google.dev/competition/projects/cleardoc
- https://letsdatascience.com/news/cardiologist-builds-ai-patient-care-platform-in-seven-days-6215e242 (PostVisit.ai)
- https://www.digitalhealthnews.com/amrita-unveils-medsum-an-ai-clinical-assistant-that-turns-doctor-patient-conversations-into-medical-records
- https://blog.google/innovation-and-ai/technology/developers-tools/winning-entries-gemma-4-good-challenge/
- https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/
- https://www.ibc.org/technical-papers/ibc2023-tech-papers-sign-language-interpreter-virtual-human-avatar-kiki/10289.article
- https://ai.google.dev/gemini-api/docs/speech-generation (Gemini TTS 130+ languages)
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11844009/ ; https://ajels.ust.edu.ph/ (PH leaflets) ; https://ir.lib.ugm.ac.id/id/eprint/5635/ (Yogyakarta)
- https://cbf.org.au/FirstNations ; https://www.sbs.com.au/news/the-race-against-the-clock-to-save-rare-recordings-of-indigenous-languages
- https://informationaccessgroup.com/literacy-levels-in-australia/
