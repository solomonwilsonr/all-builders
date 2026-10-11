# Project NADI — AI Builder Cup 4.6+ version

## Recommended hackathon positioning

**Theme:** Sustainability & Social Impact  
**Solution:** NADI — an offline maternal-care gap and referral network for rural communities  
**Target user:** an ASHA/ANM or community-health worker serving mothers across villages with intermittent connectivity  
**Primary promise:** help existing rural health teams choose the safest, highest-value next action under limited time, travel, connectivity, and referral capacity—and prove whether care actually reached the mother.

## Submission-ready pitch

> **NADI is an offline-first maternal-care navigation network for rural communities. It finds mothers who are being missed, detects worsening needs over time, recommends the next safe human action, and verifies whether a referral became real care.**

## Competitive reality

Offline records, maternal worklists, risk flags, multilingual support, referral tracking, and follow-up coordination already exist in platforms such as Khushi Baby CHIP, CommCare, Community Health Toolkit, OpenSRP, and SHELY Assist. NADI must not claim those capabilities as novel or ask workers to maintain another disconnected register.

NADI's differentiator is the **explainable next-best-action layer**:

> Given incomplete information, limited worker capacity, travel constraints, patient preferences, and competing referral barriers, what should this health worker do next—and why?

The hackathon prototype should demonstrate that decision layer on top of a small adapter interface. The long-term product should integrate with existing health systems rather than replace them.

## The product boundary

Rural mothers face interconnected mental-health, medical, nutrition, transport, safety, and record-keeping problems. NADI should acknowledge that whole system without pretending to diagnose twenty conditions in a hackathon.

NADI has two layers:

- **MVP:** postpartum mental-health screening support plus missed postnatal-visit and referral tracking.
- **Long-term platform:** validated modules for anemia, gestational diabetes, danger signs, nutrition, breastfeeding support, newborn follow-up, transport, benefits, and safe social-risk referrals.

The common intelligence layer is not a universal diagnostic model. It answers: **What is missing? Who needs a human follow-up? Which established danger sign requires urgent escalation? Where did the care pathway break?**

## NADI is also a field-operations system

NADI solves the everyday workflow failures that make care disappear: failed home visits become revisit tasks; temporary relocation becomes an authorized care handover; paper referrals become trackable referral IDs; transport, childcare, cost, and language barriers become assigned actions; and every unresolved referral has an owner and due date.

Clinic attendance, assessment, and care received are tracked separately. Offline, pending-sync, and synchronized records are clearly visible, while supervisors receive aggregate reports without manually counting registers.

The product distinction is: **every identified care gap becomes a traceable human action, and every action has an outcome.**

NADI does not diagnose depression or prescribe treatment. It supports validated screening, prioritization, referral coordination, and outcome tracking, with a human health worker and clinician retaining control.

## Why it fits the official theme

The hackathon's Sustainability & Social Impact theme explicitly includes accessibility and community services. NADI addresses a concrete social-access problem: rural mothers may be geographically, digitally, linguistically, or socially disconnected from mental-health support. Its value is not only a model prediction; it is making an underserved care pathway visible and actionable.

## Required Google technology mapping

| Hackathon requirement | NADI implementation |
|---|---|
| Gemini or Gemma | Gemini handles local-language conversational assistance, structured screening support, barrier summarization, and referral explanations. A compact Gemma or conventional small model can support the on-device risk-priority experiment. |
| Agentic platform | Google ADK / Agent Platform coordinates screening intake, timeline update, referral drafting, safety escalation, and follow-up tasks. |
| Google Cloud deployment | Cloud Run hosts the health-worker dashboard and sync API; Firebase provides authentication, hosting, and a lightweight application data layer. |
| Cloud data/analytics | Firestore stores consented demo records and follow-up states; BigQuery can hold de-identified aggregate coverage metrics for the community dashboard. |
| Offline operation | The mobile prototype caches screening forms, approved language prompts, encrypted demo records, and follow-up tasks locally, then syncs through the Cloud Run API when connectivity returns. |

## The 4.6+ strategic change

Do not pitch NADI as “AI that detects postpartum depression.” That puts it in a crowded and medically risky category.

Pitch it as **care-gap intelligence**:

> The problem is not only that a mother may be struggling. The problem is that the health system often cannot see who was missed, who is worsening, why a referral failed, or whether anyone followed up.

NADI's central technical contribution is an **uncertainty-aware, capacity-aware next-best-action engine**. It combines:

- current validated screening signals;
- change since the previous visit;
- postpartum stage and care history;
- missed-visit and overdue-referral status;
- reported access barriers; and
- available worker/clinic capacity.

It produces a transparent priority reason, a feasible action plan, and alternatives when constraints change—not a diagnosis. This gives NADI a defensible AI problem: allocating scarce follow-up attention under uncertainty.

For every recommendation, show:

- evidence used;
- information missing;
- action selected;
- why it outranked alternatives;
- what would change the recommendation;
- the human approver.

## The one user story judges should remember

Meet **Meena**, an ASHA worker responsible for 86 mothers across four villages. She has only one clinic day available this week.

- Mother A screened below the mental-health concern threshold last month but is now deteriorating.
- Mother B has no documented postnatal follow-up because the visit was missed.
- Mother C needs additional assessment, but the referral failed because transport was unavailable.

NADI does not simply show three red flags. It explains which case needs attention first, why, what action is feasible, and whether the action was completed. The demo ends with Meena closing one referral and scheduling the next check.

## The focused MVP for the competition

Build one complete workflow rather than claiming a universal rural-health platform:

1. Meena signs in offline and sees her assigned village caseload.
2. NADI shows a **care-gap map**: screened, overdue, unreachable, referred, and unresolved—not mental-health labels in public view.
3. A health worker records an assisted local-language screening for Meena's mother.
4. The longitudinal engine compares two visits and explains: **“Priority increased: symptoms worsened + follow-up overdue + clinic access barrier.”**
5. The worker records a barrier and available capacity; NADI ranks the next three visits with reasons.
6. The worker approves a revisit/referral task; the app stores it locally and syncs when connectivity returns.
7. A simulated clinician outcome is entered. NADI changes the referral to completed, records the unresolved issue, and schedules the next review.

The MVP should also include an offline daily worklist, failed-visit tracking, a referral passport with a unique ID, barrier-aware follow-up, an assigned owner and due date, synchronization status, privacy-aware contact preferences, care verification, and an automatic aggregate supervisor report.

For differentiation, the demo must include a constraint-change interaction: when Meena loses one clinic slot or transport becomes unavailable, NADI recomputes the plan and explains the tradeoff. A static priority list is not enough.

The public demo should use a small, carefully designed synthetic cohort of 30–50 mothers across four villages. This is enough to make coverage gaps and prioritization visible without pretending to have clinical-scale evidence.

Use synthetic patient records for the public demonstration. Do not imply that the prototype has been clinically validated.

## The 3-minute demo story

1. **The caseload:** Meena opens NADI with no internet and sees 86 mothers represented as care states.
2. **The invisible population:** one village has low documented postnatal-care coverage and overdue visits. NADI labels this a coverage gap, not a disease cluster or prevalence estimate.
3. **The change:** a mother who initially screened below concern is now worsening. NADI shows the timeline and the evidence behind the priority increase.
4. **The constrained decision:** only two home visits are possible. NADI ranks the visits using urgency, deterioration, overdue status, travel distance, and capacity; Meena retains final control.
5. **The safety moment:** a self-harm response triggers a fixed clinician/emergency escalation pathway, with no automatic family disclosure.
6. **The proof:** after a simulated referral is completed, the dashboard changes from “flagged” to “care received,” while unresolved needs remain visible.

Show a complete daily worklist: Mother A needs clinical review; Mother B needs a home visit; Mother C needs transport assistance; Mother D has moved villages and needs an authorized handover; Mother E has unverified clinic attendance. Every item shows an owner, action, due date, status, and outcome.

The memorable line is:

> **A flag is not an outcome. NADI measures whether care actually reached the mother.**

## Judging rubric alignment

### Technical Merit & GenAI — 40%

- Gemini contributes directly to local-language assisted interaction, barrier extraction, timeline summarization, and transparent referral-task drafting.
- ADK/Agent Platform connects the screening, timeline, safety, referral, and follow-up steps.
- Cloud Run/Firebase provides a deployable end-to-end workflow.
- Deterministic code calculates score changes, overdue status, and referral state; the model does not invent clinical thresholds.
- Offline-first behavior demonstrates an important constraint of the target users.
- BigQuery aggregates de-identified workflow metrics such as screening coverage, median referral delay, unresolved cases, and village-level missed-visit rates.
- The demo includes an evaluation harness comparing NADI's transparent priority ranking with simple baselines such as “most recent positive screen” and “oldest overdue visit.”
- The evaluation harness also compares plans under changing capacity and travel constraints, measuring whether urgent cases remain covered while unnecessary travel and unresolved referrals decrease.
- The system logs why each recommendation was made, enabling replay and audit rather than opaque AI decisions.

### Problem Alignment & Impact — 25%

- One named user: the rural community-health worker.
- One painful workflow: finding mothers who are worsening or missed and closing the referral loop.
- Measurable prototype metrics: screening completion time, overdue follow-ups surfaced, referral status visibility, and time from flag to human action.
- Impact metric for future pilots: percentage of mothers needing care who receive timely, appropriate follow-up.
- Demonstration metrics: coverage-gap recall on synthetic ground truth, referral completion rate, median time-to-follow-up, and number of unresolved referrals surfaced.

### Innovation & Creativity — 25%

- Moves beyond one-shot depression detection to longitudinal change, coverage gaps, barriers, and verified outcomes.
- Uses AI to coordinate scarce human care capacity, not to replace clinical judgment.
- Combines local-language access, offline operation, and a care-outcome loop in one product.
- Treats the unseen population and failed referral as first-class data problems, not only individual risk prediction.
- Demonstrates a decision layer that existing record systems could consume through APIs, rather than presenting another replacement database.

### User Experience & Solution Design — 10%

- Photo/voice-friendly, assisted workflow for low-literacy settings.
- Simple status language and visible uncertainty.
- Timeline, priority queue, and referral states make the result understandable to a busy worker.
- Consent, role-based access, minimal data, and safe escalation are visible in the interface.

## Safety and credibility rules

- Say **screening support** or **possible concern**, never “AI diagnosed depression.”
- Use a validated instrument only with appropriate permissions and a qualified partner; otherwise use clearly labelled simulated screening data.
- Do not use voice emotion analysis as a diagnostic signal.
- Never expose sensitive results to family members by default.
- Require human review before referral, escalation, or outreach assignment.
- Make self-harm escalation a fixed safety pathway, not an LLM-generated improvisation.
- Show uncertainty and allow “insufficient information.”
- State that clinical validation, fairness testing, and real-world deployment are future phases.
- Never combine unrelated symptoms into one unsupported “maternal health risk” score.
- Established emergency danger signs use a fixed, clinician-approved escalation flow; they never wait for model confidence.
- Domestic-violence or unsafe-home disclosures use private, consent-based pathways and never automatically notify a partner or family member.
- Use minimal-data care handovers when a mother moves between villages; sensitive screening details are shared only with consent and appropriate role access.
- Never use continuous location tracking. Record only the location information needed for a consented care handover.

## What not to build for this submission

- A universal platform for every rural disease.
- Twenty condition-specific AI detectors.
- Automatic family notifications or continuous location tracking.
- A claim that NADI is the first offline maternal-health or ASHA platform.
- A full replacement for CHIP, CommCare, CHT, OpenSRP, or government records.
- Federated learning.
- Autonomous diagnosis or treatment recommendations.
- A full hospital integration.
- Multiple languages unless one language works convincingly first.
- A research claim about sensitivity, specificity, or clinical effectiveness without evaluation data.

## Deliverables checklist

- Deployed Cloud Run or Firebase prototype.
- Public GitHub repository with setup instructions and architecture diagram.
- Three-minute demo video showing the complete offline-to-sync workflow.
- English proposal deck with the Sustainability & Social Impact theme clearly named.
- Synthetic demo dataset and explicit privacy/clinical-safety statement.
- Short evaluation section measuring workflow performance, not unsupported medical accuracy.

## Final recommendation

Keep NADI focused on postpartum mental-health support and missed postnatal/referral follow-up for this hackathon. Present the product as an explainable orchestration layer that can eventually integrate with existing systems, not as a new general-purpose maternal-health database.

To make a 4.6-level submission credible, the team must visibly demonstrate three things in the video and deployed app:

1. **A real system constraint:** the app works offline and syncs later.
2. **A real intelligence contribution:** it prioritizes longitudinal care gaps better than a one-shot positive-screen list, with reasons.
3. **A real outcome:** a referral moves from missed to completed care, with unresolved needs still tracked.

The 4.6+ version of NADI is therefore not the biggest version. It is the version that makes one hard promise and proves it end to end:

> **NADI helps one overextended health worker make better follow-up decisions for an entire rural caseload—and shows whether those decisions led to care.**

## Competitive proof required for a high score

The prototype should explicitly demonstrate a capability that public competitor materials do not clearly establish as a complete product:

1. Two plausible action plans for the same caseload.
2. A changed constraint, such as one fewer worker, a blocked route, or an unavailable clinic.
3. Recomputed next-best actions with an explanation of the tradeoff.
4. Human approval and an auditable outcome.

Without this proof, NADI is a competent but crowded maternal-health workflow app. With it, NADI becomes a focused research/product thesis: **can transparent AI improve care allocation under real-world constraints without replacing clinical judgment?**

## Roadmap beyond the hackathon

After clinical partnerships and validation, NADI can add separately governed modules for anemia-treatment follow-up, gestational-diabetes testing, nutrition support, breastfeeding and newborn follow-up, transport coordination, benefits navigation, and safe social-risk referrals. Each module must have its own clinical owner, evidence standard, escalation policy, and evaluation set.
