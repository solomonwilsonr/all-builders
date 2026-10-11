# Prior-Art Check: Genba Proof (Manufacturing, JAPAC)

Date of check: 2026-10-08
Idea: "Verify, don't author" for SME factories with migrant workers.
- (a) Novice films self on a phone; multimodal AI (Gemini) compares to expert reference video step by step; flags missed / out-of-order / unsafe steps with timestamps.
- (b) Spoken comprehension quiz in the worker's native language (Nepali, Burmese, Vietnamese, Indonesian) with per-worker pass/fail audit record.
- (c) "Why" interviewer that asks the expert follow-up questions about their knack while they film.

## Verdict: PARTIALLY DONE (leaning crowded on component a)

Each component exists somewhere in Japan's 2024-2026 market, and component (a) in particular is now a shipping feature at three Japanese vendors. No single product found combines all three, and none found does spoken free-answer quizzes in Nepali/Burmese or a live "why" interviewer during filming. The pitch cannot claim "first to compare novice video to expert/standard"; it must win on the combination, the language set, the SME/phone-only form factor and the audit record.

---

## Findings

### Component (a): trainee video vs expert / standard

| Name | URL | What it does | Overlap |
|---|---|---|---|
| **Dive (Episotech)** "手順書との比較" | https://divedx.com/blog/video-manual-ai | Japanese video-manual SaaS. Takes the manual held in Dive as the reference, matches a filmed work video step by step, lists each step as "as written" vs "needs review", and jumps straight to that playback point. Also "かんたん分析" flags moments that look dangerous from a single video. 192-language translation. Blog dated 2026-10-08. | **FULL on (a)** (step-level deviation + timestamp jump + unsafe moments). Reference is the written/video manual, not a raw expert video. Explicitly frames output as "points for a human to check", not pass/fail. |
| **AI Manual Coach (Career Survival, Nagoya)** | https://career-survival.com/ai_manualcoach/ | Upload video, get the manual. "Expert vs novice comparison": the AI compares two work videos and writes a diff and improvement report. Also gives a skill score dashboard per person, **auto-generated comprehension tests**, 12-language translation (incl. Vietnamese, Thai) for foreign-worker OJT, and TPS standard work sheets. | **FULL on (a)**, **PARTIAL on (b)** (auto tests + multilingual + per-person tracking; no evidence of spoken/native-voice quizzes or Nepali/Burmese). Closest single competitor. |
| **Ollo Factory (Ollo Inc.)** | https://ascii.jp/elem/000/004/310/4310814/ ; https://finance.yahoo.com/news/suzuki-rolls-ai-based-analysis-160640693.html | Work-analysis AI. Upload work videos; it auto-builds manuals, classifies value-add vs waste, does **veteran-vs-novice comparison**, and detects anomalies. Deployed at Nissan and Suzuki; JR East trial from Apr 2026. | **PARTIAL to FULL on (a)**. IE/productivity focus, big OEMs, not SME/migrant comprehension. |
| **MHI + Algomatic (GENIAC-PRIZE 2nd place)** | https://www.mhi.com/news/26040801.html | Agentic AI compares expert vs novice TIG welding videos, extracts and illustrates skill differences, and gives feedback to less-skilled welders. | **PARTIAL (a)**. R&D/contest, single trade. (Already known.) |
| **Mitsubishi Electric behavior-analysis AI** | https://monoist.itmedia.co.jp/mn/articles/2402/01/news037.html ; https://newswitch.jp/p/16522 | Skeleton tracking of hands. Flags swapped order or unknown motions as non-standard procedure, with no training data needed (2024). Also does skill-evaluation AI comparing expert and non-expert polishing motions. | **PARTIAL (a)** (order deviation). Fixed camera, pose-based, no LLM explanation. |
| **Hitachi Advanced Workplace Safety / AI Debriefing** | https://www.hitachi.co.jp/New/cnews/month/2025/07/0708a.pdf | AI agents trained on expert safety standards plus an Omniverse digital twin to confirm procedures. "AI debriefing" for post-work reflection. | PARTIAL (a), weak (c). Enterprise. |
| **Fujitsu Actlyzer** | https://www.fujitsu.com/global/about/research/article/202008-actlyzer.html | Recognises about 100 basic actions without training data; detects deviations as combinations and orders of actions. | PARTIAL (a). Building block, not a training product. |
| **Retrocausal (RetroActivity / Pathfinder)** | https://www.automateshow.com/prior-exhibitors/retrocausal-inc | Learns an assembly task from a few demonstrations, tracks steps on live video, verifies each step, alerts on errors, offers "independent training". | **PARTIAL to FULL (a)** for fixed stations (US). Not phone or SME, and no multilingual comprehension. |
| **Drishti / Invisible AI / Spot AI / Vidizmo** | https://techcrunch.com/?p=1982837 ; https://vidizmo.ai/blog/assembly-verification-and-missing-component-checks | Fixed-camera line analytics, cycle and step compliance, SOP verification. | PARTIAL (a). Infrastructure-heavy. |
| **Fairy Devices THINKLET + "FPV Video Analysis Plan" / COROKO** | https://www.techno-edge.net/release/prtimes2/20260915/24572.html | Neck-worn first-person camera. Multimodal AI turns first-person video into manuals and work reports, and analyses assembly/repair records. | PARTIAL (a)/(c) (capture side). No novice grading or quiz found. |
| **Teachme Biz / Teachme AI / "Studio" (Studist)** | https://cloud.watch.impress.co.jp/docs/news/2126809.html ; https://www.notebookcheck.net/Studist-launches-Teachme-AI-to-automate-multilingual-work-manual-creation-while-reducing-labor-by-over-80.863069.0.html | Video → step-split multilingual manuals (auto step split since Feb 2026). "Studio" (Jul 2026) merges many videos and docs into a manual. "Teachme Check" covers inspection execution. **No evidence it grades trainee attempt videos.** | NONE on (a). Authoring only, which matches the pitch's "don't author" framing. |
| **tebiki 現場教育** | https://www.itreview.jp/products/tebiki | Video manuals, 100+ language subtitles, viewing logs, tests, skill map. **No AI grading of trainee videos found.** | PARTIAL (b) (tests, records, translation). |
| **Augmentir / Tulip / Poka / Dozuki / SwipeGuide** | https://www.augmentir.com/tag/ai-in-manufacturing-training | Connected-worker platforms: digital work instructions, skills matrices, gen-AI assistant "Augie" and expertise capture by speech or video. No phone-video grading against an expert. | PARTIAL (b)/(c) (records, expertise capture). |
| **Cloud Assess (AU)** | https://cloudassess.com/blog/ai-marking-assistant/ | Workplace competency platform. Learners or assessors capture video evidence on mobile, and an AI marking assistant suggests outcomes. | PARTIAL (a)/(b) (video evidence + AI marking + audit). Not step-by-step video-vs-expert. |
| **VR training (Strivr, Interplay)** | — | Scripted VR scenarios with scoring. | NONE on real-video verification. |

Academic (shows the technique is known; useful as citations, not competitors):
- Sakai, Cao, Kimura, "Anomalous Frame Detection ... Two Videos ... VLM to Extract Expert Workers' Unique Actions" (2026). A VLM compares expert vs manual-following videos to find expert-only actions: https://arxiv.org/abs/2607.10598 and companion https://arxiv.org/pdf/2607.11957
- ExpertAF: actionable feedback by comparing a learner video to expert examples: https://arxiv.org/pdf/2408.00672
- Video Action Differencing (VidDiff): https://arxiv.org/pdf/2503.07860
- Procedural mistake detection benchmarks: EgoOops, MATT-Bench (CVPR 2026), PIE-V: https://aclanthology.org/2025.emnlp-main.706 ; https://arxiv.org/abs/2604.15134
- Nursing competency from egocentric video (CVPRW 2026): https://arxiv.org/pdf/2605.20233
- Paper finding: VLMs recognise *what* happened but struggle to judge *whether it was correct*. This is a known limitation the demo must handle with care.

Hackathon/GitHub:
- **Indra (Devpost)**: https://devpost.com/software/indra-kl7fj2. Multi-agent lab-SOP supervisor. YOLO-World per frame, escalating to Gemini Flash for temporal reasoning. Flags deviations with timestamps, SOP citations and evidence clips. Overlap: **PARTIAL to FULL on (a)** (Gemini + SOP step verification + timestamps). The reference is a written protocol on fixed cameras in a clinical lab; there is no expert video, no worker quiz and no interviewer.
- GitHub `thr-0731/paired-videos-action-seg` ("SOP video alignment and segmentation", 2026-07): research code for paired-video alignment. `pogJames/camera-demo` does object-detection assembly step verification. Neither is a product.
- No Devpost/lablab project found that combines phone video-vs-expert, native-language spoken quiz and expert interviewer. (GitHub search got rate-limited partway, so coverage is partial.)

### Component (b): native-language comprehension check + audit record

| Name | URL | What | Overlap |
|---|---|---|---|
| **AI Manual Coach** | (above) | Auto comprehension tests, 12 languages, per-person dashboard | PARTIAL: text tests; no spoken free answers; Nepali/Burmese not listed |
| **カミナシ 教育 (Kaminashi)** | https://www.itreview.jp/products/kaminashi-kyo-iku/profile | Video manuals, comprehension tests, learner management, 24-language AI subtitles and **voice translation** | PARTIAL: closest on multilingual test + records |
| **tebiki** | (above) | Tests + viewing logs + 100+ languages | PARTIAL |
| **SafetyCulture Training (ex-EdApp)** | https://training.safetyculture.com/ai-translation/ | 100+ language course translation, TTS narration, quizzes, completion records | PARTIAL: MCQ, not spoken answers |
| **KOSHA (Korea) 16-language materials; Incheon game-show quizzes; Flitto / HD KSOE AI translators** | https://www.koreatimes.co.kr/southkorea/20260908/incheon-uses-game-show-format-in-safety-training-for-migrant-factory-workers ; https://en.edaily.co.kr/news/eda202609095110 | Native-language safety training and live interpretation. Quizzes are in-person events. | PARTIAL/NONE: translation, not per-worker AI verification |
| **Japanese labour inspectors (茂原労基署)** | https://www.rodo.co.jp/news/221306/ | Officially urge native-language safety education **plus a post-training comprehension test**, and suggest gen-AI for materials | Not a product. **Validates the need** (regulatory pull for "理解度確認") |
| **KLiK / Worxphere AI Korean test** | https://www.koreaherald.com/article/10722384 | 30-sec voice recording graded for Korean proficiency | NONE (language proficiency, not procedure comprehension) |

No product found that asks *spoken*, open-ended "teach-back" questions in Nepali/Burmese/Indonesian/Vietnamese, grades the spoken answer against the specific procedure, and stores a signed per-worker pass/fail record.

### Component (c): AI interviewer extracting the expert's knack

| Name | URL | What | Overlap |
|---|---|---|---|
| **Konica Minolta COCOMITE "AI技能伝承インタビュー"** (Nov 2024; COCOMITE AI plan Jul 2026) | https://konicaminolta.com/jp-ja/newsroom/topics/2024/pdf/1106-01-01-ja.pdf | A gen-AI grounded in cognitive science interviews the skilled worker for about 30 min by voice and generates a manual | **FULL on interview-for-knack**, but it is a separate sit-down session and not tied to the video while filming |
| **NTT Data + Kawasaki Heavy (GENIAC-PRIZE ユーザー変革賞)** | https://www.nttdata.com/jp/ja/trends/data-insight/2026/0209 | Gen-AI interview agent for tacit knowledge | PARTIAL/FULL (interview), not live during filming |
| **Sensay** | (known) | AI offboarding interviews | PARTIAL |
| **Augmentir expertise capture** | (above) | Workers capture knowledge by speech or video in the flow of work | PARTIAL |
| **CHI "Tacit Knowledge Elicitation for Shop-floor Workers with an Intelligent Assistant"; APEX expert-anchored SOP demos** | (via search) | Research prototypes | PARTIAL |

No product found that watches the expert's live video *while they film* and asks context-triggered "why did you do that just now?" questions anchored to timestamps.

---

## Conclusion

**Has it been done?** Not as a bundle, but the core verification feature has been done.
- (a) **Already exists** in Japan: Dive's "手順書との比較" (step-level, timestamp jumps, unsafe-moment detection), AI Manual Coach (expert vs novice video diff + skill score) and Ollo Factory (veteran vs novice at Nissan/Suzuki). Indra on Devpost shows the Gemini + SOP + timestamps pattern in hackathons.
- (b) **Partially exists**: auto-generated multilingual *text* tests with learner records (AI Manual Coach, Kaminashi, tebiki, SC Training). Spoken native-language answers in Nepali/Burmese and a procedure-specific audit record appear novel.
- (c) **Partially exists**: AI knack interviews (COCOMITE, NTT Data/KHI, Sensay). Doing it *live during filming, anchored to video moments* appears novel.

**Closest prior art:** AI Manual Coach (Career Survival). It covers expert-vs-novice video comparison, auto comprehension tests, 12-language translation for foreign workers and per-person skill dashboards. Next closest are Dive (strongest on step-level, timestamped, unsafe-moment verification) and COCOMITE (for c).

**What remains genuinely novel**
1. **Spoken teach-back quiz in the worker's own language** (Nepali, Burmese, Indonesian, Vietnamese), graded against *this* procedure's steps and the hazards seen in *their* attempt video, rather than generic MCQ.
2. **Closed loop on one worker:** the steps they missed in the video drive the questions they are asked by voice, and the result goes into one per-worker sign-off record (video evidence + quiz + timestamps). That record is the evidence trail labour inspectors already ask for (理解度確認).
3. **Live "why" interviewer during the expert's filming**, which turns the reference video into a reference annotated with reasons. Those reasons then become the explanations and quiz content for novices.
4. **SME form factor:** phone only, no fixed cameras, no manual authoring, no enterprise rollout (versus Ollo/Retrocausal/Drishti/Hitachi). The reference is the expert's own video, which is useful when the SME has no written manual (Dive needs a manual as its reference).

**How to differentiate the pitch**
- Do not lead with "AI compares novice video to expert". Acknowledge Dive, AI Manual Coach and Ollo and position against them: "They help Japanese supervisors author and analyse. We prove that a Nepali worker understood and can do it, in their own language, with an audit trail."
- Lead with the migrant-worker comprehension gap and the regulatory hook (labour inspector guidance for native-language education plus comprehension checks; Korea's KOSHA push). Show the low-resource language set as a key feature.
- Demo the loop: the expert films while the AI asks why, giving an annotated reference; the novice films, and the AI flags step 4 skipped at 01:12; it then asks in Nepali by voice why step 4 matters; the worker answers aloud; a PASS/FAIL record is created with evidence.
- Be honest about VLM limits: flags are "needs review", with the supervisor signing off. Dive positions the same way; the research shows VLMs struggle to judge correctness.

**Verdict: PARTIALLY DONE.** Component (a) on its own would be ALREADY EXISTS. The combined bundle with (b) spoken native-language verification and (c) the live why-interviewer is defensible as novel.
