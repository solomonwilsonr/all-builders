# Recommended idea: "BatchWatch": invoice-to-quarantine for neighbourhood chemists

**Theme:** Retail & Commerce (inventory intelligence) · **Market:** India first, with Indonesia, Vietnam and the Philippines as expansion

> **One-line pitch:** India's drug regulator flags about 250 bad medicine batches every month, but the corner chemist never finds out. BatchWatch turns a shoebox of purchase invoices into a stock-wide recall check in 3 minutes and drafts the quarantine and return paperwork.

## Why this one
| Winner pattern (2026-hackathon-winners.md) | How BatchWatch fits |
|---|---|
| One named user | **Ramesh**, a one-counter chemist in Lucknow with no software (India has ~1.24M chemists) |
| Healthcare, a painful workflow | Substandard medicine stays on shelves. HackMIT's 2026 Grand Prize (Peel) was also about bad medicine |
| A before/after number | Checking stock against alerts by hand is effectively never done → **~1,500 invoice lines checked in under 3 min**; return/quarantine paperwork **~45 min → under 2 min** |
| A safeguard | Says "flagged, verify", never "unsafe". Ramesh confirms each match by photographing the strip, and every match shows a confidence score |
| A human story | WHO: about **1 in 10** medical products in low- and middle-income countries is substandard or falsified. CDSCO flagged **280** batches in July 2026 alone. Recalls often don't reach chemists (Newslaundry 2025) |
| Deep use of the sponsor's tech | Gemini reads invoices and strips (vision), ADK agents, Cloud Run, Firestore, a monthly scheduled job that re-checks stock |

## Competition check
- **In this hackathon:** 0 of ~70 public entries touch medicine recalls or substandard-drug checks. The Retail theme's entries are about COD, warung inventory, dark patterns, pet commerce and similar.
- **In the market:** MedShield (Devpost, Gemini) and Credo check **one batch at a time**. CDSCO's search page is manual, Telangana's SMS alerts cover one state, and pharmacy ERPs (Marg, Gofrugal) have no recall feed. **Nobody checks the whole stock from invoices or produces the paperwork.**
- **Pitch rule:** open the demo on the invoice stack → quarantine flow, never on a single-batch lookup, so it doesn't look like a MedShield clone.

## The key idea
Indian drug rules require **batch number and expiry on every purchase invoice**, so a chemist's pile of invoices is already a batch-level inventory, even with no software. CDSCO's monthly lists are public PDFs with a stable 8-column table.

## Demo flow (3-min video)
1. Ramesh's story, with the 280-batches number on screen.
2. Photograph a stack of ~50 invoices. Gemini extracts each line (product, batch, expiry, supplier), with live progress.
3. The stock is matched against 12 months of real CDSCO alert lists (fuzzy brand and generic matching): **"3 flagged batches in your stock."**
4. **Wow moment:** Ramesh photographs the strip on the shelf, Gemini confirms the batch, and one tap produces a quarantine entry, a return note to the supplier and a notice to the Drug Inspector in English and Hindi.
5. Replay: "With BatchWatch, this batch would have been caught **N days** earlier." Use real alert dates.
6. Second screen: a district Drug Inspector's dashboard showing recall coverage and shops that haven't responded.

## Judging rubric map
| Criterion | Feature / proof |
|---|---|
| Technical & GenAI 40% | Gemini reads messy invoices and strip photos; ADK agents (extract → match → verify → draft); deterministic fuzzy matching so the model never decides alone; monthly re-check job; Cloud Run deployment |
| Problem & Impact 25% | 1.24M chemists, ~250 flagged batches a month, WHO's 1-in-10 figure, the days-earlier replay |
| Innovation 25% | Invoices treated as an inventory (no ERP needed); stock-wide checks instead of single lookups; paperwork generated automatically |
| UX 10% | Hindi/English, a photo-first flow, one-tap paperwork, a confidence score on every match |

## Demo data
- CDSCO NSQ and spurious-drug PDFs (cdsco.gov.in → Alerts); mirrors on medicaldialogues.in
- Kaggle dataset of ~254k Indian medicines for brand ↔ generic matching
- ~50 synthetic invoices seeded with a few real flagged batch numbers

## 8-day plan (Oct 10 → submit Oct 17, a day early)
| Day | Work |
|---|---|
| 1 (Oct 10) | **Confirm the team on the portal before Oct 11.** Check which Gemini model IDs are callable (2.5 retires Oct 16, so use 3.x). Cloud Run skeleton deployed. Parse the CDSCO PDFs into Firestore |
| 2–3 | Invoice extraction with Gemini vision plus the matcher (exact batch + fuzzy brand) |
| 4 | Strip-photo confirmation and the paperwork drafts (EN/HI) |
| 5 | Drug Inspector dashboard and the "days earlier" replay |
| 6 | **Feature freeze.** UI polish, failure cases (blurry photos, O/0 confusion) |
| 7 | README with architecture diagram, PDF deck, 3-min video (record a backup take) |
| 8 (Oct 17) | Submit early; Oct 18 is the buffer |

## Risks
- **Liability:** an NSQ result covers only the tested batch, so always say "flagged, verify" and keep the human confirmation step.
- **Misreading batch numbers:** use the confirmation photo plus a confidence score per match.
- **Credibility:** if anyone on the team has pharmacy or healthcare background, put them up front (the "credible builder" pattern).

## Runners-up (in research_notes/Winning idea search/)
1. **PreAuth Copilot (BFSI):** reads handwritten case sheets for a 60-bed hospital's insurance desk and drafts the pre-authorisation. Strong numbers (≈₹30,000 cr of claims unpaid), but BFSI is the most crowded theme (20 entries), and Kavach already covers patient-side claim appeals.
2. **Timbang (Sustainability):** for Philippine Barangay Nutrition Scholars, a photo of the weighing register plus a Tagalog voice note produces the official e-OPT/FHSIS report. Open for the Philippines, but the India version (AshaAI) is a Google Solution Challenge Top-100, and there's no published hours-saved number.
