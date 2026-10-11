# Retail and Media idea scan (2026-10-11)

**36 ideas checked** against existing products and the ~125 public cup entries: 4 research passes plus the earlier round. Scores are rough, weighted **0.4 Tech · 0.25 Impact · 0.25 Innovation · 0.1 UX**. For reference: ClearSight ~4.45, PitStop ~4.39.

## The honest result
After checking competitors, **no Retail or Media idea scored a clear 4.5.** Every strong candidate turned out to be partly built somewhere. Two ideas reach ~4.45, and each has a clear route to 4.5 if one measured result comes in (listed below). The other 10 range from 4.0 to 4.4. We did not raise any scores to meet the 4.5 target.

## Top 12 (Retail + Media)

| # | Idea | Theme | T / I / N / U | Score | Originality |
|---|---|---|---|---|---|
| 1 | **SafeShelf** (pre-recall hazard radar + certification registry check) | Retail | 4.5 / 4.5 / 4.5 / 4 | **4.45 → 4.5** | Partly open |
| 2 | **Akshara Ladder** (decodable readers in Indic scripts) | Media (education/publishing) | 4.5 / 4.5 / 4.5 / 4 | **4.45 → 4.5** | Open |
| 3 | **ShopTest** (AI mystery shopper with a coaching loop) | Retail | 4.5 / 4 / 4.5 / 4.5 | 4.38 | Partly open |
| 4 | **LQA Lens** (game localization QA from gameplay video) | Media | 4.5 / 4 / 4.5 / 4 | 4.33 | Open (per Nimdzi 2025) |
| 5 | **ImageHonest** (listing photos vs buyer photos) | Retail | 4.5 / 4 / 4 / 4.5 | 4.25 | Partly open |
| 6 | **Sansad Clips** (parliament debate → cited regional-language explainers) | Media | 4.5 / 4 / 4 / 4.5 | 4.25 | Partly taken |
| 7 | **ShopReel** (one shop video with spoken prices → ONDC catalog) | Retail | 4.5 / 4 / 3.5 / 4.5 | 4.13 | Partly taken |
| 8 | **VM Fix** (brand guideline PDF → display check + generated "fixed" image) | Retail | 4.5 / 4 / 3.5 / 4.5 | 4.13 | Largely taken |
| 9 | **CaptionAudit** (live-caption accuracy score + regulator evidence pack) | Media | 4.25 / 3.75 / 4.25 / 3.75 | 4.08 | Partly taken |
| 10 | **PackTruth** (pack photo vs listing, Legal Metrology) | Retail | 4.25 / 4.25 / 3.5 / 4 | 4.04 | Partly taken (Woflow) |
| 11 | Manga/webtoon → audio drama for blind readers | Media | 4.5 / 3.5 / 3.5 / 4.5 | 4.0 | Partly taken (ComicCast) |
| 12 | Community-radio archive → new local-language bulletins | Media | 4 / 4 / 4 / 4 | 4.0 | Partly open |

---

## 1. SafeShelf (Retail, 4.45 → 4.5)
**Pitch:** marketplaces sell dangerous products for weeks before regulators recall them. SafeShelf reads buyer review **text and photos** (melted chargers, burn marks, loose magnets), groups the same product relisted under different brand names, and checks listed certifications (BIS ISI/R-number, BEE star rating, mAh) against official registries. A safety analyst gets an evidence pack to approve **before** the recall.
- **User:** a product-safety analyst at a marketplace (or at the ACCC).
- **Why it matters:**
  - The OECD sweep found **87%** of banned or recalled products still on sale ([OECD](https://oecd.org/en/publications/online-product-safety-sweep-report_c1faa51e-en.html)).
  - The ACCC sued Amazon in May 2026, and Pledge signatories removed 31k unsafe listings in 2024–25 ([Bird & Bird](https://cm.twobirds.com/en/insights/2025/australia/safety-first-accc-targets-online-marketplaces-and-child-hazards)).
  - BIS raided Amazon and Flipkart warehouses and seized 3,500+ fake-ISI items ([Outlook Business](https://www.outlookbusiness.com/news/govts-e-commerce-crackdown-bis-raids-amazon-flipkart-warehouses-seizes-products-worth-rs-70-lakh)).
- **Gemini's role:**
  - spots hazards in review photos,
  - groups relisted products by image,
  - reads certification marks and cross-checks them against each other and the registry,
  - drafts the ACCC 2-day mandatory report or a GPSR notice.

  A human approves every step.
- **Competitors:**
  - [DeepRecall](https://f4.fund/startups/deeprecall) works only **after** a recall.
  - Prior research is text-only (~84% F1) ([arXiv](https://arxiv.org/pdf/1703.00518)).
  - CPSC lists this as a wished-for use case ([CPSC](https://www.cpsc.gov/s3fs-public/CPSC-AI-Use-Cases_FINAL.pdf)).
  - Hong Kong EMSD runs a text-only trial.
- **Evaluation and wow moment:** backtest the [CPSC recalls API](https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information) against timestamped [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/) (which includes review images). The headline is "flagged N weeks before the official recall", shown as a timeline replay. The Australian energy-rating registry is an open CSV, so the certification check has exact ground truth.
- **What gets it to 4.5:** the backtest shows a median lead time of ≥2 weeks on ≥20 recalls.
- **Risks:**
  - The BIS registry may sit behind a captcha; the fallback is the open Australian registry.
  - Review images are sparse for some categories.

## 2. Akshara Ladder (Media, 4.45 → 4.5)
**Pitch:** children learn to read from "decodable" books that use only the letters they've been taught. AI tools make these in English, but none work for Indian scripts. A teacher picks "week 3: these aksharas". Gemini rewrites an open StoryWeaver story using only those aksharas, and a **deterministic checker** (Unicode grapheme parsing) loops until the story is ≥95% decodable. Imagen adds consistent illustrations and TTS reads it aloud, and the teacher approves the book.
- **User:** a Grade-1 government-school teacher in Maharashtra.
- **Why it matters:** only **23.4%** of Std III children can read Std II text ([ASER 2024](https://asercentre.org/wp-content/uploads/2022/12/ASER_2024_National-findings.pdf)). The NIPUN Bharat foundational literacy mission needs graded readers.
- **Competitors:**
  - [LitLab](https://www.litlab.ai/decodables) and [Project Read AI](https://www.projectread.ai/decodable-generator) are English-only.
  - [Gemini Storybook](https://blog.google/products/gemini/storybooks/) makes books but doesn't restrict letters.
  - No Indic decodable generator found.
- **Evaluation:** decodability % for Akshara Ladder vs plain Gemini vs the original story, on 30 stories (LitLab reports ChatGPT at ~35%).
- **Wow moment:** "week 3 only" becomes a 10-page illustrated Marathi book with audio in about 60 s.
- **What gets it to 4.5:** a measured decodability of ≥95% vs <50% for plain Gemini, plus the akshara order taken from a real state syllabus.
- **Risks:**
  - Judges may read it as Education rather than Media. Frame it as publishing (a children's book pipeline for publishers like Pratham Books).
  - Use Hindi or Marathi only; low-resource languages are unverified.

## 3. ShopTest (Retail, 4.38)
**Pitch:** Gemini Live calls the store or chats on WhatsApp as a realistic shopper (e.g. Taglish, asking about EMI and warranty). It scores the staff's answers against the store's own SOP PDF with timestamped evidence. The manager approves the scorecard, and ShopTest generates a 3-minute role-play drill on the exact mistake.
- **User:** Maria, area manager of 40 eyewear/electronics stores in Manila.
- **Why it matters:** mystery shopping was a $2.8B market in 2025. EliseAI's 10k-call report found a 70% answer rate and a 7% callback rate ([EliseAI](https://eliseai.com/resources/2025-mystery-shop-report)).
- **Competitors:**
  - Second Nature and YOOBIC NEO run role-play training with no audit.
  - Invoca scores calls, but only for car dealers.
  - Human mystery-shopping firms.
- **Evaluation:** 30 scripted calls with planted SOP violations, measuring precision and recall. A teammate plays the staff member.
- **Gap to 4.5:** the impact figures are mostly vendor numbers; recording real stores covertly raises consent issues.

## 4. LQA Lens (Media, 4.33)
**Pitch:** Gemini watches 30–40 minutes of a tester's gameplay video in Japanese, Korean or Thai. It flags truncated text, untranslated strings, wrong honorifics, broken placeholders and cultural issues, maps each to a string ID, and suggests a translation that fits. A linguist approves before tickets are filed.
- **User:** localization QA (LQA) lead at a Tokyo publisher.
- **Why it matters:** the market was $2.5B in 2024, with LQA costing $41–65/h ([VoxBooster](https://voxbooster.com/blog/game-localization-statistics-2026)). Nimdzi 2025 says there is "no end-to-end solution" ([Nimdzi](https://www.nimdzi.com/the-linguist-the-bot-and-the-bug-report/)).
- **Competitors:**
  - Gridly AI LQA checks text only.
  - GameDriver tests gameplay, not language.
  - Research (VideoGameQA-Bench) covers visual glitches.
- **Evaluation:** inject ~100 bugs into an open-source game's localization (SuperTuxKart / 0 A.D.).
- **Gap to 4.5:** impact is a B2B niche; injected bugs may look easier than real ones.

## 5. ImageHonest (Retail, 4.25)
**Pitch:** compares listing photos with buyer review photos, one attribute at a time (colour, scale, material, count), shows matched crops side by side, and gives sellers a pre-check before a listing is suppressed.
- **Data:** Amazon Reviews 2023 (images included) plus 200 hand-labelled pairs.
- **Competitors:** Bellingcat guides and "is it AI?" detectors. Amazon only requires disclosure of AI-generated people.
- **Weakness:** ground truth is weak ("not as pictured" reviews), so pairs must be labelled by hand.

## 6. Sansad Clips (Media, 4.25)
**Pitch:** turns a 6-hour parliament debate into a 90-second neutral explainer per bill, in Tamil or Hindi.
- Every sentence is linked to the exact second of source video.
- An entailment check re-reads that clip before the editor sees the sentence.
- A speaker-balance rule guarantees both government and opposition voices are included.

**Why it matters:** 35% of 17th Lok Sabha bills passed with under an hour of debate ([PRS](https://prsindia.org/files/parliament/vital_stats/Functioning-17th_Lok_Sabha.pdf)).

**Competitors:** Hamlet and citymeetings.nyc (US councils), Sansad Bhashini (translation only), PRS (text).

**Weakness:** politically sensitive, and partly taken.

## 7–12 in brief
- **ShopReel (4.13):** 90-second shop video → 40 SKUs, linking each spoken price to the item on screen by timestamp. Partly built already (a Gemini competition project and Google's ONDC demo).
- **VM Fix (4.13):** the guideline PDF becomes a checking rubric, and Gemini generates the "after" image. YOOBIC VM Copilot, OneDoor and Trax crowd this space.
- **CaptionAudit (4.08):** see `PITSTOP.md` §12. Narrow user base, and rights to broadcast clips are a risk.
- **PackTruth (4.04):** see `PITSTOP.md` §12. Woflow exists, and judges may see it as "OCR plus a diff".
- **Manga → audio drama (4.0):** ComicCast (ONCE + AWS, Spanish) already exists. The open angle is Asian reading order and Indic languages; Manga109 needs an access request.
- **Community-radio bulletins (4.0):** Akashvani datasets on AIKosh. Speech recognition in low-resource languages is unproven.

## Checked and dropped (taken or weak, ≤3.9)
- **Retail:**
  - RecallSweep (DeepRecall, Recall Shadow)
  - PromoProof was/now pricing (arithmetic only)
  - checkout overcharge
  - display-scheme payouts (SalesCode)
  - quick-commerce substitutions (Instacart, Pick n Pay on Gemini)
  - multilingual defect warning (SentiSum)
  - supplier onboarding (Amazon, GS1 DataKart)
  - pre-sale Q&A (Rufus)
  - returns analysis
  - shrinkflation
  - blind shopping (Be My Eyes + Tesco)
  - festival demand
- **Media:**
  - screenplay coverage (Filmustage, Prescene)
  - flash-safety cut (Harding FPA)
  - cultural QA (Spherex)
  - ad suitability (Vionlabs)
  - podcast knowledge (Snipd)
  - language-learning stories
  - esports highlights (Eklipse)
  - grassroots sports (CricHeroes AI)
  - newsroom archive (Pinpoint)
  - mother-tongue picture books (Gemini Storybook)
  - chart accessibility
  - children's video QA
  - oral-history indexing
  - TRAI ad-cap logger (cap repealed 10 Sep 2026)
