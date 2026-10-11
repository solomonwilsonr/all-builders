# PitStop: an F1 pit-stop plan from one phone video of a changeover

Researched 2026-10-11 · Theme: **Manufacturing** · Rough score **~4.39** (ClearSight ~4.45, SolventGate+ 4.34; a gap under 0.3 is a tie)

> **Pitch:** In the 1950s an F1 pit stop took over a minute; today it takes 2 seconds, because crews moved every possible task to *before* the car stops. Factories use the same method, called SMED, to cut machine changeovers in half, but it needs a lean consultant with a stopwatch for days. PitStop gives one engineer that consultant: film the changeover on a phone, and Gemini turns it into a timed step-by-step breakdown, a redesigned changeover plan and a new work sheet in the operator's language. A second video then proves how much time was saved.

**What judges should remember:** *Gemini watches a messy, one-off, 40-minute changeover it has never seen and turns it into a pit-stop plan. Then a second video proves the saving.*

---

## 1. The existing idea we are reinventing
- **SMED (Single-Minute Exchange of Die)**: Shingo/Toyota, 1950s–80s. It is the standard method for cutting changeover time. Published cases show **50–64%** reductions ([cjournal](https://www.cjournal.cz/files/218.pdf); a northern-India small-unit case is at [Inderscience](https://www.inderscience.com/filter.php?aid=84580)).
- **Today it is done by hand.** Film the changeover, then sit with a stopwatch or tagging software (Timer Pro, AviX, Iteros) labelling every step. Classify each step as **internal** (machine must be stopped) or **external** (could be done while the machine runs). Then redesign and retrain.
- **Why small and mid-size factories don't do it:** it needs a trained lean engineer for days. India's MSME LEAN scheme pays **90% of consultant fees** (₹1.2–2.4 lakh per engagement) because firms can't do it themselves ([India Briefing](https://www.india-briefing.com/news/revised-msme-competitive-lean-scheme-launched-in-india-to-boost-industry-27393.html/), [Invest India](https://investindia.gov.in/schemes-msmes-india/lean-manufacturing-competitiveness-msmes)).

## 2. The problem
- Changeovers take **3% of capacity on average and 14% in pharma** (17,000 production weeks, 700+ plants) ([FiercePharma](https://www.fiercepharma.com/manufacturing/pharma-struggles-changeovers)).
- In high-mix plants they take **15–30% of production time**, and 30–50% of each changeover is waste ([Fabrico](https://www.fabrico.io/blog/changeover-time-reduction-oee-smed-software/)). This is a vendor figure, so quote it carefully.
- JAPAC contract manufacturing (moulding, packaging, garments, pharma, auto parts) is shifting toward smaller batches and more SKUs, so changeovers happen more often and the waste grows.

## 3. The user
**Ravi, the only process engineer at a 120-person injection-moulding plant in Pune** that supplies 40+ part numbers. He runs about 6 mould changes a day at about 45 minutes each, which is roughly 4.5 hours of a press doing nothing. He knows SMED from training but never has the 3 days to do a study.

## 4. How it works
1. **Film.** Ravi films one changeover on a phone and narrates as he goes ("machine stopped", "unclamping mould"). Narration roughly lifts Gemini's step-boundary F1@50 from **55 to about 86** ([EgoInstruct, Table 6](https://arxiv.org/pdf/2509.22019)).
2. **Segment.** Gemini on Vertex reads the video, audio and narration together (custom `fps`, `start_offset`/`end_offset` chunking for long videos). It returns structured JSON with one entry per step:
   - start and end time,
   - action and tool,
   - who does it,
   - the machine state it implies,
   - waste type (searching, walking, waiting, adjusting, rework).
3. **Correct (human in the loop).** Ravi sees a timeline next to the video and drags step boundaries, renames steps, and fixes internal/external labels. The machine stop and start points are anchors he confirms. **All times are calculated in code, never by the LLM.**
4. **Redesign.** Gemini draws on world knowledge ("mould pre-heating can happen outside the stop", "the hunt for the 19 mm spanner is a missing shadow board"). It proposes, step by step:
   - external-ise this step,
   - run it in parallel with a second person,
   - remove it,
   - standardise it (quick clamps, pre-staged cart).

   It also gives the cost and difficulty of each change. Code then builds the **before/after Gantt chart** and the predicted changeover time, e.g. **45 → 26 min**.
5. **Deliver.** PitStop generates:
   - a **pre-stop checklist**,
   - a **crew Gantt chart**,
   - a **one-page standard work sheet**, illustrated with key frames taken from his own video at each step, in Hindi, Thai, Bahasa, Vietnamese or English, with optional Gemini TTS for operators who can't read.
6. **Verify the saving.** Ravi films the next changeover done with the new plan. PitStop lines up the two videos step by step and reports:
   - which steps really moved before the stop,
   - which were skipped,
   - the real time saved compared with the prediction.

   The result goes into the plant's changeover history in BigQuery. **No competitor we found closes this loop.**
7. **Learn across crews (stretch goal).** Compare changeovers of the same mould by different crews and build a "best of best" sequence, the way F1 teams study every stop.

## 5. Why this is new (competitor check)
| Who | What it does | Gap PitStop fills |
|---|---|---|
| [Coats GSD RealMotion](https://www.imarcengineering.com/news/coats-digital-gsd-realmotion-ai-time-motion-studies) (Aug 2026), [MTM AI Video](https://mtm.org/en/software/ai-video-analysis), [Retrocausal](https://industrialmachinerydigest.com/software/factory-floor-software/retrocausal-revolutionizes-manufacturing-process-management-with-industry-first-generative-ai-leangpt-offering) | Phone-video **time study** of short, repetitive work cycles | Not built for changeovers. Coats is apparel-only, MTM is expensive and certified, Retrocausal is US enterprise. No SMED internal/external analysis, no checked redesign |
| [OTRS (Japan)](https://www.strasse.co.jp/pdf/flyer_OTRS.pdf), [Fujitsu Actlyzer](https://www.fujitsu.com/global/about/resources/news/press-releases/2021/0218-01.html), [Mitsubishi Electric](https://monoist.itmedia.co.jp/mn/articles/2402/01/news037.html) | Classic computer vision that learns from one labelled cycle | Changeovers are **one-off, 20–120 min, unscripted and multi-person**, so there is no repeated cycle to learn from. Gemini works without examples |
| Timer Pro, AviX, Iteros | SMED templates, manual tagging | The engineer still tags every second by hand |
| [Spot AI](https://www.spot.ai/blog/video-analytics-smed-manufacturing), [TeepTrak](https://teeptrak.com/en/what-is-smed-single-minute-exchange-of-die-in-2026/), Drishti, Tarsyer | Fixed-camera or OEE systems | Need installed cameras and contracts. PitStop needs a phone and nothing else |
| AI Builder Cup entries (~14 manufacturing) | Maintenance, root cause, visual QC, CBAM | **None about changeovers, SMED or video work analysis** |

**Verdict:** general AI time study is taken; **zero-shot SMED from a phone video, with a generated redesign, local-language work sheets and a second video that verifies the saving, is open.** Pitch it as SMED and pit stops, never as "AI time study".

## 6. Why the Gen AI is essential, not decoration (40% of the score)
- **Without examples:** Gemini segments long, unscripted, multi-person video using video, audio and narration together. Classic CV cannot do this without training data.
- **World knowledge:** knowing that a step could be external ("pre-heat", "pre-stage the bolts") is industrial know-how, not pixel matching.
- **Comparing two videos:** checking a second video against the first is plain-language reasoning over two long videos at once.
- **Local-language output:** generated work sheets (text plus frames, optional TTS) let operators who don't read English use the new standard.
- **Guardrails:** the LLM never computes times. Code does, and the engineer approves every boundary and label.

## 7. Demo (3 minutes)
| Time | Beat |
|---|---|
| 0:00–0:20 | F1 pit stop, 1950s (over a minute) vs today (~2 s; check the exact numbers for the clip we use). "Same idea, every factory, no consultant." |
| 0:20–0:40 | Ravi's problem: 6 changeovers a day, 4.5 press-hours lost |
| 0:40–1:30 | Upload our filmed **before** changeover. Timeline appears, Ravi fixes 2 boundaries, internal/external colours update |
| 1:30–2:10 | Redesign: Gantt chart animates **45 → 26 min**. Hindi work sheet with key frames from the video |
| 2:10–2:40 | **Wow:** the **after** video is analysed, and the saving is real and measured, e.g. predicted −42%, achieved −38% |
| 2:40–3:00 | Accuracy numbers, Google stack, "every changeover in JAPAC is a pit stop waiting to happen" |

**Demo material:** we film our own changeover (we can't count on factory access in 6 days). Options:
- a 3D-printer nozzle and filament swap,
- a sewing-machine needle, bobbin and thread change,
- a bench-vise or drill-press fixture change,
- a bike wheel and brake swap.

Film it badly the first time, with real searching and walking, then re-film following PitStop's plan. Use 1–2 public mould-change videos only to show that segmentation also works on real factory footage.

## 8. Evaluation (the performance slide)
- **Step segmentation:**
  - 20–30 clips from [Assembly101](https://assembly101.github.io/) / [HA-ViD](https://iai-hrc.github.io/ha-vid) (CC BY-NC, evaluation only).
  - Score with F1@10/25/50 and the Edit score, compared with or without narration and at different fps settings.
- **Our own changeovers:** 4–6 recordings labelled by hand. Measure:
  - boundary error in seconds,
  - internal/external accuracy,
  - time from video to approved plan compared with manual stopwatch tagging (target: **hours → under 15 min**).
- **Saving check:** predicted vs achieved changeover time on our before/after pairs.

## 9. Google stack
- **Gemini 3.x on Vertex AI** (model ID in an env var; 2.5 retires 16 Oct): video and audio understanding, structured output, redesign, comparing two videos.
- **Gemini TTS**: spoken work sheet.
- **Cloud Storage**: videos. **ffmpeg on Cloud Run**: key frames and chunking.
- **Cloud Run**: FastAPI backend and React timeline editor. **Firestore**: studies. **BigQuery**: changeover history and crew comparison.
- **ADK agent** (optional): Segmenter → Classifier → Redesigner → Verifier.

**Cost:** video tokens are about 100–300 per second, so a 45-minute video is roughly 0.3–0.8M tokens per pass. The whole hackathon fits easily in the $300 credit.

## 10. 6-day plan
| Day | Work |
|---|---|
| Oct 12 | Confirm Gemini 3.x model IDs. Film the "before" changeover. First segmentation prompt with JSON schema, tested on 2 Assembly101 clips |
| Oct 13 | Chunking for long video, timeline editor UI, internal/external rules, calculations in code |
| Oct 14 | Redesign step, before/after Gantt chart, work sheet with key frames, local language and TTS |
| Oct 15 | Film the "after" changeover. Video comparison check. Evaluation runs |
| Oct 16 | Polish, deploy, fix bugs, freeze |
| Oct 17 | Record the video, finish the deck, submit (deadline Oct 18) |

## 11. Risks and hard questions
| Risk / judge question | Answer |
|---|---|
| "Coats, MTM and Retrocausal already do AI time study" | They time short, repeated cycles. We redesign one-off changeovers and prove the saving with a second video. Show the comparison table |
| Step boundaries are imprecise (video-only F1@50 ≈ 55%) | Narration, higher fps on short clips, and an engineer correction UI. Show measured error on our labelled set |
| Gemini can't see whether the machine is running | The engineer confirms the stop and start points, and narration or motor sound helps. Classification is relative to those confirmed points |
| "Our demo isn't a real factory" | Say so plainly. Show segmentation on public mould-change footage and Assembly101 numbers. Factory pilot goes on the roadmap |
| Privacy (filming workers) | Faces are blurred in key frames, videos stay in the plant's own GCS bucket, workers consent |

## 12. Runner-ups from the same research round
| Idea | Theme | Score | Verdict |
|---|---|---|---|
| **PackTruth**: checks pack photos against live listings for India's Legal Metrology rules (MRP, net qty, origin, best-before), with an evidence pack for replies to CCPA notices | Retail | ~4.04 | Strong regulatory pull: [CCPA notices to 11 platforms](https://inc42.com/buzz/ccpa-sends-notices-to-11-ecommerce-quick-commerce-companies/), and 48% of shoppers can't find best-before dates online ([The Week, Jun 2026](https://www.theweek.in/news/biz-tech/2026/06/18/quick-commerce-food-packaging-expiry-dates-online-grocery.amp.html)). Easy evaluation with Open Food Facts India. **Partly taken** ([Woflow](https://www.woflow.com/customers/supply-chain)), and judges may see it as "OCR plus a diff" |
| **CaptionAudit**: scores the accuracy of live broadcast captions (NER), including errors only visible on screen, and builds an ACMA/CRTC evidence pack | Media | ~4.08 | Real enforcement: [WIN breached captioning rules](https://www.acma.gov.au/articles/2025-03/win-television-queensland-breaches-captioning-rules), and [CRTC requires NER ≥ 98](https://crtc.gc.ca/eng/archive/2019/2019-308.htm). **Partly taken** (NER Buddy research tool, Interra BATON). Narrow user base, broadcast clip rights are a risk |
| Poka-Yoke Studio: defect photo plus process clip, then mistake-proofing designs and a PFMEA update | Manufacturing | ~3.9 | Open, but the before/after is hard to measure in 6 days |
| Dropped this round | | | TRAI ad-cap logger (cap repealed 10 Sep 2026); returns-reason analysis (Clootrack, Enterpret); shrinkflation tracker (Frugl); generic AI time study (Coats, MTM) |

**Scores:**
- **PitStop:** Tech 4.5 · Impact 4.25 · Innovation 4.5 · UX 4.0 → **4.39**
- **PackTruth:** 4.25 / 4.25 / 3.5 / 4.0 → 4.04
- **CaptionAudit:** 4.25 / 3.75 / 4.25 / 3.75 → 4.08
