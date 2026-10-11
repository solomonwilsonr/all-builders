# New top pick: "SolventGate": stop toxic solvent before it becomes cough syrup

**Theme:** Manufacturing (Intelligent Operations & Industrial Efficiency: quality, supply chain)
**Market:** India first (Schedule M, CDSCO solvent tracking), Indonesia second (BPOM tests every container)

> **One-line pitch:** Over 300 children have died since 2022 because a drum labelled "propylene glycol" actually held industrial ethylene glycol. SolventGate checks every drum at the receiving gate (label, CoA, invoice and supplier chain) and blocks it from production until the lab test and the paperwork are real.

## The problem (both real cases are the demo)
- **Indonesia 2022 (200+ child deaths):** trader CV Samudera downloaded Dow's logo, stuck it on drums of ethylene glycol and sold them as pharmaceutical-grade PG.
- **India 2025 (Coldrif, 24 child deaths):** the "PG" came from a detergent-fragrance company, was resold from trader to trader the same day, and was never tested.
- In both cases the documents existed. **Nobody cross-checked them.**

## Why now
| Date | Rule |
|---|---|
| Oct 2025 | CDSCO requires every excipient batch to be tested |
| 22 Oct 2025 | CDSCO's ONDLS portal tracks PG, glycerin and sorbitol batch by batch, with CoA uploads |
| 2025 | Indian Pharmacopoeia requires DEG/EG testing before oral liquids are released |
| **1 Jan 2026** | Revised Schedule M (GMP) becomes binding. **~6,300 small manufacturers didn't file upgrade plans** and risk losing their licence |
| Ongoing | Indonesia's BPOM requires testing on every arrival and every container |

## The user
**Anil, QA officer at a 40-person syrup maker in Baddi (Himachal Pradesh)**, a hub for small pharma. He signs off incoming material with paper checklists and has no budget for enterprise QMS software.

## What it does
1. **Gate photo:** Anil photographs the drum label, the supplier's CoA and the invoice.
2. **Gemini reads all three** and cross-checks them: grade (pharma vs industrial), batch and lot numbers match across all three documents, manufacturer named on the label vs on the CoA, CoA test methods and the DEG/EG limit (≤0.10%) actually reported, plausible dates.
3. **Supplier provenance (Google Search grounding):** is the "manufacturer" really a pharma-grade producer, or a detergent or fragrance company? Does the trader chain add hops? Is the label logo consistent with the real manufacturer's?
4. **Deterministic rules:** the model never decides alone. Hard rules flag a missing DEG/EG result, mismatched batch numbers, non-pharma grade or an unknown manufacturer.
5. **Verdict: "HOLD — mandatory GC test before release",** never "safe". It generates the quarantine label, the sampling request to the lab, the Schedule M-style receiving record and an ONDLS-ready upload entry (mocked).
6. **Release only after the lab result is entered.** The audit trail is the product.

## Wow moment (demo)
Replay the two real cases with reconstructed documents:
- the forged "Dow" label → flagged: *logo/manufacturer inconsistency + supplier is a chemical trader, not Dow*;
- the Coldrif chain → flagged: *manufacturer is a detergent-fragrance firm; same-day trader resale; no DEG/EG result on the CoA*.
Then a genuine CoA passes to "lab test pending". **On screen: "Two batches that killed 224+ children: both stopped at the gate."**

## Why it beats BatchWatch
| | BatchWatch | **SolventGate** |
|---|---|---|
| Harm | Substandard medicines on shelves | **Children's deaths; global WHO alerts** |
| Urgency | Monthly lists | **New 2025–26 rules plus a Schedule M licence threat** |
| Gemini depth | Invoice reading + matching | **Cross-checking several documents + Search grounding + forgery cues + agents** |
| Competition in this hackathon | Retail ~15, none close | **Manufacturing ~11, none in pharma** |
| Market prior art | Single-batch checkers (MedShield) | **Generic CoA AI for big pharma only (IBM, AWS, Kognitos). Nothing does a receiving-gate cross-check for small makers** |
| Weighted score (agent estimate) | 3.80 | **4.18** |

## Rubric map
- **Technical 40%:** multimodal reading of three documents, Search-grounded supplier verification, an ADK agent pipeline (extract → cross-check → provenance → rules → paperwork), deterministic gates, Cloud Run + Firestore, a full audit trail.
- **Impact 25%:** 300+ child deaths, ~6,300 small manufacturers at risk, a regulatory mandate.
- **Innovation 25%:** first gate check that combines document cross-checks, supplier provenance and test enforcement for SMEs.
- **UX 10%:** three photos → one verdict screen → one-tap paperwork.

## Conditions before committing (decide by Oct 12)
1. **Find 5–10 genuine public CoAs and drum labels** for PG, glycerin and sorbitol (supplier websites often publish sample CoAs) to use as references.
2. **Find one pharmacist or QA advisor** to sanity-check the logic and give a 20-second quote for the video (the credible-builder pattern).
3. If either fails, fall back to **BatchWatch** (IDEA.md). Reuse SolventGate's grounded supplier search and real-case replay there.

## Risks
- **Spotting a forged logo by eye is unreliable,** so present it as one signal among many, with confidence scores. The lab test is the real safeguard; SolventGate makes sure the test happens.
- **ONDLS needs a login,** so mock the upload format.
- **Liability:** "HOLD / verify", never "safe".
- **Team credibility:** without pharma/QA background, the judges' "why you?" question is harder. The advisor quote helps.

## Other options considered this round
- **Counter Check** (verifies the pack in the chemist's hand against the prescription): partly done (Nesayo already auto-fills the H1 register, Alkem DawAI reads prescriptions), and reading handwriting is risky (best model 57.8% line accuracy on Indian handwritten prescriptions).
- **KLB Kit** (food-poisoning outbreak investigation for Indonesia's school meals): big impact, but similar designs already exist and the topic is politically sensitive.
- **Wajib Halal copilot:** killed (AMANA, AMINRA and SiHalal already do it).

Notes: research_notes/Winning idea search/open_search.md, counter_check.md
