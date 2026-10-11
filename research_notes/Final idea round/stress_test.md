# Final idea round: stress test under the "no real people" constraint

Date: 2026-10-11 · Judge lens: skeptical Google Cloud JAPAC engineer + industry expert · Team of 2 · Submit Oct 18 (aim Oct 17)

**Constraint:** no advisors, interviews or user testing. Only public or synthetic data.

**Inputs read:**
- IDEA.md (BatchWatch), MEDIA_IDEA.md (NightDesk), IDEA_SOLVENTGATE.md
- solventgate/reference_docs/ (10 WHO alerts, 4 forged-label images, 5 genuine CoAs, specs, FDA/IPC/IPEC guidance)
- counter_check.md, open_search.md, COMPETITOR_ENTRIES.md

Fresh web and GitHub searches were run on Oct 10–11.

---

## 0. TL;DR

| Rank | Option | Tech 40% | Impact 25% | Innov 25% | UX 10% | **Weighted** |
|---|---|---|---|---|---|---|
| **1** | **SolventGate+**: SolventGate plus BatchWatch's known-bad registry matcher, with an optional one-screen "downstream recall" stretch | 4.5 | 4.25 | 4.5 | 3.5 | **4.34** |
| 2 | SolventGate (as written, advisor removed) | 4.5 | 4.0 | 4.5 | 3.5 | **4.28** |
| 3 | Full merge: "pharma supply-chain gate" (manufacturer gate + chemist app) | 3.75 | 4.5 | 4.0 | 3.0 | **3.90** |
| 4 | NightDesk | 4.0 | 3.5 | 3.25 | 4.0 | **3.69** |
| 5 | BatchWatch | 3.5 | 3.75 | 2.75 | 4.0 | **3.43** |

**Recommendation:** build **SolventGate+** in the Manufacturing theme. **Do not** do the full two-user merge.

**Biggest finding:** the real WHO forged Dow label (batch F9600L7PPA4) **looks genuine**. Do not pitch "Gemini spots forged logos". Pitch "even a perfect forgery fails the cross-checks". Section 1 has the signals that actually catch it.

---

## 1. SolventGate (re-scored)

### What the constraint changes
**Lost**
- The advisor quote and the domain sanity check.
- The "why you?" answer gets weaker, and a domain error in the rules could embarrass the team in front of an industry judge.

**Gained or still available (all public)**
- **Real ground truth.**
  - 4 forged-label photos from WHO Alerts N1-2024 and N4-2024. Dow confirmed these batch numbers are falsified, and one had **0.7624% EG**.
  - 10 WHO DEG/EG alerts.
  - 5 genuine CoAs: Thermo/Avantor PG USP lists "Identification B – DEG / EG". Lab Alley CoAs are public online too.
  - Hedinger and Greenfield PG specs.
  - FDA 2023 guidance, **IPC GD-11 v2.0 (2026)**, the IPEC Europe 2026 position paper and the NPRA Malaysia directive.
- **Replacement for the advisor:** every rule in the rule engine cites a clause from these documents (the "rulebook with citations" pattern). On screen, each flag shows the document and section it comes from. This **replaces the advisor's authority with the regulator's**. It is also stronger technical evidence.

### What the forged labels actually show (looked at the images)
- **F9600L7PPA4 ("Dow Europe GmbH, Werk Stade, Made in Germany"):** a clean, plausible label. The body text is a trilingual EU *food-additive E1520* use table. **Gemini looking at the label alone will very likely say "appears genuine."**
- **SS8900B3PPD5 ("The Dow Chemical Company … distributed by Dow Chemical Thailand"):** there is a small box reading **"REPACKED BY: … LOGISTICS (THAILAND) CO., LTD"**, the notice panel is torn, and "Shelf-life: 2 years" appears with no expiry date. **These are machine-readable chain-of-custody red flags.** A repacker breaks the GDP chain; IPEC GDP / WHO TRS guidance treats repackers as needing their own qualification.
- **Across alerts:** the same "Dow USP/EP PG" product shows **different stated manufacturers and batch-number formats**, so a label-to-label consistency check against a reference set is legitimate.

**Signals that actually work, in priority order:**
1. **Exact hit on the falsified-batch registry** (WHO, DRAP). Deterministic. This is BatchWatch's engine pointed upstream.
2. **Cross-document mismatch:** label vs CoA vs invoice, comparing batch, manufacturer, site and dates.
3. **Chain of custody:**
   - a repacker or trader is present;
   - the invoice seller is not the stated manufacturer or a known distributor;
   - same-day resale (Coldrif).
4. **CoA content:** a DEG/EG test is missing, a limit other than ≤0.10% is reported, or the method isn't GC.
5. **Grounded supplier search:** a detergent or fragrance maker is selling "pharma PG".
6. **Visual label cues:** **advisory only**, never decisive.

### Scores
| Criterion | Score | Why |
|---|---|---|
| Tech 40% | 4.5 | Reads 3 document types with Gemini; deterministic rules with citations; Search grounding; agent pipeline; measurable eval harness (section 1.4) |
| Impact 25% | 4.0 | 300+ child deaths; binding Schedule M (Jan 2026); ONDLS. Loses 0.5 because nobody has validated that "Anil" would use it |
| Innovation 25% | 4.5 | No product or hackathon project does an MSME receiving-gate cross-check (section 1.5) |
| UX 10% | 3.5 | 3 photos → verdict is clean, but the persona is untested and the workflow is hypothetical |

**Weighted: 4.28**

### 1.1 The 3 hardest judge questions
1. **"Would it have stopped the drum *before* it appeared in a WHO alert? A registry hit is hindsight."**
   - **Answerable with public data: yes, partly.**
   - Run the demo with the **registry check turned off** and show that the other signals still produce HOLD on both replays:
     - SS8900B3PPD5: repacker, plus no expiry.
     - Coldrif (from Tribune/Reuters): seller is a fragrance firm, same-day resale, no DEG/EG on the CoA.
     - Indonesia (court papers): seller is a chemical trader, not Dow.
   - Admit honestly that the F9600L7PPA4 label alone would pass. It is only caught if its CoA or invoice is inconsistent, or once it's in the registry. **Turn this into a demo beat** (section 1.3).
2. **"If every drum ends at 'HOLD until the GC test', what does the AI add? Testing is already mandatory since Oct 2025."**
   - **Answerable: yes,** from public sources:
     - The Coldrif inspection found **39 critical and 325 major violations**, and the PG was **never tested** even though rules existed.
     - The Pakistan alert notes a **falsified Dow CoA**, so a supplier CoA cannot be trusted.
   - What the AI adds:
     - It enforces that a test happened. Release is blocked without a lab entry, and the batch, sample and drum IDs must match.
     - It catches **paper fraud that the GC test never looks at**.
     - It sets the testing level (per container for BPOM; high-risk tier).
     - It writes the Schedule M records.
   - Framing: "**Rules exist; enforcement at the gate doesn't.**"
3. **"You have no pharma background and spoke to no QA officer. Why should we believe the rules are right, and that MSMEs would adopt it?"**
   - **Rules: answerable.** Every rule cites FDA 2023, IPC GD-11 2026, USP/EP monographs or IPEC 2026.
   - **Adoption: only partly.**
     - Public proxies: ~6,300 MSMEs at licence risk under Schedule M; free Cloud Run tier and phone-only use (no QMS needed); ONDLS already requires CoA uploads, so the paperwork exists.
     - **There is no direct user evidence.** Say so plainly in the deck, and list "pilot with 3 Baddi units" as the next step.

### 1.2 Biggest demo failure and mitigation
**Failure:** the live "forgery detection" claim collapses. Gemini rates the real forged Dow label as genuine. Or grounded search gives a different (or no) answer on the day for obscure traders like Jinkushal Aroma or CV Samudera. The headline wow moment then becomes a visible false negative.

**Mitigation:**
1. **Never make the logo the decisive signal.** The verdict comes from the deterministic rules. The Gemini visual note is shown as "advisory".
2. **Cache grounded-search results** with citations and timestamps for the replay cases (show as "evidence retrieved 2026-10-xx"). Run grounding live only on a third, fresh supplier.
3. **Build an eval set of 30–40 synthetic cases** from the 5 genuine CoAs, perturbed: DEG row deleted, batch mismatched, manufacturer swapped, "industrial grade", repacker added, dates impossible. Report per-rule precision and recall in the README and deck. Robustness without real users is shown with numbers.
4. **Record the video on frozen inputs.** Keep a live deployed path for judges.

### 1.3 Demo beat to add (turns the weakness into a wow moment)
1. Show the real forged label.
2. Ask Gemini: "Is this genuine?" It answers: "appears genuine."
3. Caption: **"Even AI can't tell by looking. That's why SolventGate never trusts the label."**
4. Run the cross-check:
   - the registry hits;
   - the CoA's batch doesn't match;
   - the seller is a trader.
5. Verdict: **HOLD.**

### 1.4 Novelty spot-check (Oct 10–11)
- "AI certificate of analysis verification propylene glycol DEG excipient 2026": only vendor CoA pages (Lab Alley, Alliance, Hedinger, Fisher). **No AI gate product.**
- "cough syrup excipient supplier verification AI tool startup India ONDLS": only government ONDLS coverage (CDSCO, Haryana FDA digital monitoring). **No private AI tool.**
  - Note: Haryana FDA now runs its own state-level solvent tracking. Mention it as "state regulators are digitising, so gate-side records will need to feed them" (the export format stays mocked).
- GitHub (`gh search repos`, created ≥ Sep 2026, for "propylene glycol", "diethylene glycol", "certificate of analysis gemini", "AI Builder Cup pharma/excipient/drug"): **0 hits.**
- **Verdict: still open.**

### 1.5 Competitor entries
- Manufacturing has about 11 public entries: predictive maintenance, RCA, handover, visual QC (kaarigar), MechAI, PlantGuard, factorymind.
- **None touches pharma or raw-material intake.** No new overlap.

---

## 2. BatchWatch (re-scored)

### What the constraint changes
- **Almost nothing is lost.** CDSCO PDFs are public, and invoices were always going to be synthetic.
- **The cost:** synthetic invoices look clean, so the "Gemini reads a messy shoebox" claim is unproven unless we fake the messiness convincingly (print, crumple, write by hand, use thermal paper).

### Scores
| Criterion | Score | Why |
|---|---|---|
| Tech 40% | 3.5 | Invoice OCR + PDF parsing + fuzzy matching. Mostly deterministic and reliable, but GenAI depth is shallow and invoice extraction is now commodity |
| Impact 25% | 3.75 | 1.24M chemists. But NSQ ≠ dangerous, and the headline number needs fixing (below) |
| Innovation 25% | 2.75 | **Down from earlier estimates.** Pharmixa (India, live product) already does "upload supplier invoices → AI extracts every medicine, batch and expiry". Aushadhi Vault (AMD hackathon, May 2026) does vision billing and inventory. The stock-wide **recall match + paperwork** is still unseen, but the "invoices as inventory" insight is no longer ours |
| UX 10% | 4.0 | Photo-first, Hindi/English, one-tap paperwork |

**Weighted: 3.43**

### Number check (fix before any use)
- IDEA.md says "CDSCO flagged **280** batches in July 2026" and "~250/month".
- Fresh search found: April 2026 = **78** samples (NSQ + spurious + misbranded, including state labs); June 2026 = **27** batches (CDSCO labs only).
- So 280 is likely central + state combined, or a peak month. **Re-verify against the actual July 2026 PDF.** A skeptical judge will check.

### 2.1 The 3 hardest judge questions
1. **"CDSCO publishes 1–3 months after sampling. Isn't the batch already sold?"** **Answerable with public data:** compute alert date vs. expiry across 12 months of lists. Most batches have 1–2+ years of shelf life left at alert time. This is a real backtest; do it.
2. **"Batch numbers collide across manufacturers. What's your false-positive rate?"** **Answerable:** require batch + manufacturer (fuzzy) and measure collisions within the public lists themselves.
3. **"Pharmixa / MedShield / Marg already read invoices or check batches. What's new?"** **Partly answerable:** whole-stock recall matching and quarantine/return/inspector paperwork. But it is an incremental feature, and a judge can say "Marg could add a feed".

### 2.2 Biggest demo failure and mitigation
**Failure:** it looks like a CRUD app. Clean synthetic invoices plus a lookup table read as "OCR + VLOOKUP", and the GenAI score sinks.

**Mitigation:**
- Use ugly physical invoices (handwritten, carbon-copy and thermal).
- Show O/0 and I/1 ambiguity resolved by the strip-photo confirmation.
- Report extraction accuracy on a 50-invoice test set.

### 2.3 Competitor entries
- None in the AI Builder Cup.
- GitHub `Saniya-Sayyad144/PharmaGuard--CDSCO-Drug-Quality-Analysis` (Oct 10) is a Power BI / SQL analysis of NSQ data, not an AI Builder Cup entry. Low overlap, but it shows that NSQ data is being picked up.

---

## 3. NightDesk (re-scored)

### What the constraint changes
**Lost**
- The planned metric "harm-ranking agreement with an expert's picks".
- Any check that a real duty editor wants this queue.

**Substitute**
- Use fact-checkers' published ratings and ClaimReview data (Google Claim Search API, MultiClaim, SemEval-2025 T7) as proxy labels.
- Defensible, but these are retrieval labels, not harm labels. The harm ranking would be evaluated against labels we make up ourselves.

**Data available**
- Willie Ong deepfake ads (debunked by VERA Files / Rappler).
- The Charo Santos fake arthritis-cure ad (ABS-CBN fact check, Apr 2025).
- The Sidhu cancer-diet claim.

**Copyright / ToS**
- Downloading Facebook or TikTok videos into a **public repo** is risky. Store clips privately and reference them by URL.
- Showing a deepfake of a real doctor needs a careful caption.

### Scores
| Criterion | Score | Why |
|---|---|---|
| Tech 40% | 4.0 | Long-video, code-mixed audio, cross-lingual retrieval, Gemma filter, ADK |
| Impact 25% | 3.5 | Indirect (helps a small professional user base). Hard to quantify lives or money |
| Innovation 25% | 3.25 | Multilingual claim retrieval is a **standard academic task** (SemEval-2025 Task 7). New: **VERA Files SEEK** (public beta, Nov 2025) is an LLM chatbot over VERA's 17-year fact-check archive with Tagalog support, so "match to a past VERA fact-check" is something the target user already has in-house. Harm-ranked video triage is still open |
| UX 10% | 4.0 | Queue, timestamp jump, draft editor |

**Weighted: 3.69**

### 3.1 The 3 hardest judge questions
1. **"How do you know your harm ranking is right with no expert?"** **Weak.** Only self-made labels or ratings from published fact-checks.
2. **"Can you actually publish ClaimReview through Google's API? Is that pipeline still alive?"** **Unclear.** Write access requires a verified publisher site, and Google dropped ClaimReview rich results in 2025. Verify on day 1, or mock it. A Google judge will know the answer.
3. **"VERA Files already has SEEK, and Meedan Check runs the tiplines. Why would they adopt you?"** **Partly answerable:** NightDesk does video/audio triage and ranking before search, as a Check plug-in. But there is no user evidence.

### 3.2 Biggest demo failure and mitigation
**Failure:** Gemini mis-transcribes Taglish or Tamil and the cross-language match misses live. Or the source deepfake videos have been taken down.

**Mitigation:**
- Archive clips privately on day 1.
- Test languages on day 1 and pick the best one.
- Pre-index the fact-check corpus.
- Record on frozen inputs.

### 3.3 Competitor entries
- No misinformation entries in the hackathon. Media still has the fewest entries (~8–9).
- The structural advantage is real; the domain advantage is weaker than SolventGate's.

---

## 4. Merge analysis

### Option A: Full merge, "pharma supply-chain gate" (manufacturer gate → chemist shelf)
**For**
- One story from drum to shelf.
- The Coldrif timeline literally spans both ends: bad PG → syrup → shelves → state bans.

**Against**
- Two personas, two apps, two data pipelines and two UIs in 7 days for 2 people.
- It must still be entered under **one** theme (Manufacturing *or* Retail), so half the product is off-theme.
- The 3-minute video has to cover both and loses its wow moment.
- **Robustness (the 40% criterion) drops** because everything is half-built.

**Score: 3.90. Rejected.**

### Option B (recommended): **SolventGate+**, a lite merge
Reuse BatchWatch's *engine*, not its *user*.
1. **Known-bad registry matcher** (BatchWatch's core) pointed upstream: parse WHO alerts N1/N4-2024 + DRAP alerts into a falsified-excipient batch table. One deterministic rule. About a day of work, reusing the same PDF→table code.
2. **Stretch, day 6 only if ahead: a "downstream recall" screen.** When a drum is flagged *after* use, lot genealogy (synthetic production log: drum → syrup batches) produces a recall list and a CDSCO NSQ-style notice for those finished batches. This is one screen, still in the Manufacturing theme ("supply-chain intelligence"), and it echoes the BatchWatch story without building the chemist app.
3. **Deck slide only:** "Roadmap: the same engine at the chemist counter (BatchWatch)". Shows scalability, costs zero build time.

**Score: 4.34.** It adds +0.25 impact (the recall loop closes the harm story) and a deterministic check that strengthens robustness, with about 1–1.5 days of extra scope at most.

---

## 5. Final ranked recommendation

| Rank | Option | Weighted |
|---|---|---|
| 1 | **SolventGate+** (registry matcher + optional downstream recall screen) | **4.34** |
| 2 | SolventGate (as is) | 4.28 |
| 3 | Full merge | 3.90 |
| 4 | NightDesk | 3.69 |
| 5 | BatchWatch | 3.43 |

### Justification
- **Why SolventGate+ survives the constraint best:**
  - Its demo was always about *documents*, not people.
  - The constraint removes only the advisor quote, and a rulebook with clause citations (FDA 2023, IPC GD-11 2026, IPEC 2026, USP/EP) replaces that with something judges value more.
  - The public data is unusually strong: real WHO forged-label photos, confirmed-falsified batch numbers, genuine CoAs, and two court/inspection-documented supply chains. A synthetic perturbation eval gives hard robustness numbers that the 40% criterion rewards.
  - It is in the least crowded relevant theme, with zero pharma overlap among ~105 public entries. Fresh searches found no AI receiving-gate tool, only government ONDLS / Haryana tracking it can feed.
- **The one thing that must change:** stop selling visual forgery detection. The real forged Dow label looks genuine. Make that the demo's honesty beat and let the deterministic cross-checks and registry carry the verdict.
- **Why not BatchWatch:** its novelty eroded this week. Pharmixa already ships invoice → batch/expiry extraction, which leaves a thin GenAI story, and its headline "280 batches" figure needs re-verifying.
- **Why not NightDesk:** it has a structural theme advantage, but it loses its harm-ranking validation under the constraint. It also faces SEEK and SemEval-style "already solved" perceptions, plus an uncertain ClaimReview write path.
- **Why not the full merge:** it would double scope and split the theme. Borrowing BatchWatch's matcher upstream gets most of the merge's value for about a day of work.

### 7-day build sketch (SolventGate+)
| Day | Work |
|---|---|
| Oct 11 | Gemini 3.x model check; Cloud Run skeleton; parse WHO/DRAP falsified-batch annexes into Firestore; **test Gemini on the forged labels (expect "genuine")** |
| Oct 12–13 | Extraction for label, CoA and invoice (structured output). Deterministic rule engine where each rule carries a citation |
| Oct 14 | Search-grounded supplier check (cached evidence for replays); ADK pipeline; HOLD/quarantine/sampling/Schedule M record generation |
| Oct 15 | Synthetic eval set (30–40 perturbed cases) → precision/recall table; the two replays plus one genuine pass |
| Oct 16 | **Feature freeze.** Stretch: downstream recall screen. UI polish |
| Oct 17 | README + architecture, deck, 3-minute video (with backup take); **submit** |
| Oct 18 | Buffer |

---

## Sources (searches run Oct 10–11, 2026)
- Lab Alley PG CoA (DEG limit, GC): https://dashboard.laballey.com/coa/2295/propylene-glycol-reagent-usp-nf-grade-kosher-lot-product_COA__Lot-5000938/1.1
- Hedinger PG spec 2025: https://www.hedinger.de/fileadmin/content/03_Geschaeftsbereiche/Pharma/220_Propylene_Glycol_Ph._Eur._USP_JP/220_Spec_Propylene_glycol_EP-USP-JP_2025-04-08.pdf
- CDSCO ONDLS solvent monitoring: https://medicaldialogues.in/news/industry/pharma/cdsco/after-deg-contamination-scare-cdsco-launches-ondls-digital-monitoring-system-for-high-risk-solvents-157538
- Haryana FDA solvent tracking: https://www.digitalhealthnews.com/haryana-fda-launches-digital-monitoring-to-track-high-risk-pharmaceutical-solvents
- CDSCO NSQ June 2026 (27 batches): https://medicaldialogues.in/amp/news/industry/pharma/cdsco/cdsco-flags-27-drug-batches-including-paracetamol-ibuprofen-levetiracetam-as-not-of-standard-quality-175531
- CDSCO April 2026 (78 samples): https://medicaldialogues.in/news/industry/pharma/cdsco/state-drug-alert-cdsco-flags-78-nsq-spurious-misbranded-drug-samples-in-april-quality-checks-171331
- Pharmixa (invoice → batch/expiry): https://pay-per-vista.lovable.app/
- Aushadhi Vault (AMD hackathon, May 2026): https://lablab.ai/submissions/uvmwy4g2xlcx5htky7ic6nmp
- VERA Files SEEK: https://verafiles.org/articles/vera-files-launches-seek-an-ai-powered-chatbot-built-on-17-years-of-philippine-journalism
- Charo Santos fake ad fact check: https://www.abs-cbn.com/news/health-science/2025/4/25/fact-check-peke-ang-video-ni-charo-santos-na-nag-eendorso-ng-gamot-sa-arthritis-1420
- Meedan Check 2025 retrospective: https://meedan.org/post/2025-in-retrospect-toward-information-equity-together
- Local: solventgate/reference_docs/cases/WHO_MedicalProductAlert_N4-2024 (Dow confirms falsified batches; 0.7624% EG) and labels/*.jpg
