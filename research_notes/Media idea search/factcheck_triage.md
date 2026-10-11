# Prior-art and demand check: fact-check triage for vernacular short video and audio (JAPAC)

Researched 2026-10-10 for the Google Cloud AI Builder Cup 2026 (Media, Content & Digital Experiences track).

**Idea:** Ingest viral TikTok, Reels, Shorts and WhatsApp forwards in Hindi, Tamil, Bengali, Hinglish, Tagalog, Taglish, Bisaya, Bahasa, Thai or Vietnamese. Gemini long-video and audio understanding extracts check-worthy claims with timestamps. Each claim is matched against existing fact-checks (Fact Check Tools API / ClaimReview) and ranked by harm, with HEALTH first. The tool then drafts a fact-check in the local language, and an editor approves it.

## VERDICT: PARTIALLY DONE

Every individual piece exists somewhere, usually in English or European languages:
- timestamped video claim extraction (Factiverse, Full Fact's "Raphael", Logically Accelerate)
- health-harm prioritisation (Full Fact Raphael, which already uses Gemini)
- short-video check-worthiness (Factiverse ShortCheck, IJCNLP-AACL Dec 2025)
- claim matching and tiplines (Meedan Check, Full Fact)
- image provenance (Google DeepMind Backstory, Aug 2026)

I found no tool, product or hackathon project that does the full chain for JAPAC vernacular and code-mixed short video:
**video/forward → timestamped claims in Hinglish/Taglish → cross-lingual match to existing fact-checks → health-harm triage → draft in the local language → editor approval.**
The gap is in the Asian-language, code-mixed, WhatsApp-forward and drafting parts, not in the claim-extraction idea itself.

**Biggest risk:** a judge who knows Full Fact AI may say "Full Fact already did this with Gemini." The defence is that Raphael is English/UK-centric, paid-licence and monitoring-oriented, while Full Fact AI runs in only 3 languages (English, French, Arabic). None of the existing tools drafts the fact-check in Tagalog or Tamil.

---

## 1. Existing tools: what each one does with video in vernacular languages

| Tool | Video/audio? | Timestamped claims? | Vernacular Asian? | Claim-match to existing fact-checks? | Drafts fact-check? | Notes |
|---|---|---|---|---|---|---|
| **Full Fact AI** (UK, licensed to 40+ orgs in 30 countries incl. Africa Check, 25 Arab orgs) | TV, radio, podcasts, social (speech-to-text) | Yes (Raphael) | No. Runs in 3 languages (EN/FR/AR); BERT base model "supports 100+" | Yes (core feature) | No | **Raphael prototype (2025): Gemini finds harmful HEALTH claims in long videos and links to exact timestamps** (e.g. a 2-hour podcast with vaccine misinformation). Planned to fold into the client suite "later in 2025". Paid licence. Also selling to the healthcare sector (Oliver Wyman engagement). **Closest prior art.** |
| **Factiverse** (Norway) | Yes: live module transcribes audio/video, identifies speakers, **extracts timestamped claims** | Yes | Claims 110+ languages; check-worthiness in 114 languages at about 80% | Searches 100+ fact-check outlets in 52+ languages | Partial (verdict + sources, not a publishable article) | **ShortCheck** (IJCNLP-AACL 2025 demo, shortcheck.factiverse.ai): TikTok check-worthiness pipeline (Whisper + OCR + LLaVA + Llama3 + deepfake detection). Evaluated only on Norwegian/English TikTok (F1 about 0.70-0.73). Output is a binary "checkworthy" label. No Asian evaluation, no claim matching, no drafting. Not a Gemini pipeline. |
| **Logically Facts "Accelerate"** | Yes: automates claim extraction from video with check-worthiness scores | Yes | EN, AR, RU, ZH, **Hindi** | Unclear | No | Logically collapsed in 2025 (lost Meta/TikTok contracts, about 40 layoffs Feb 2025, assets pre-packed into "Kreatur"). Effectively gone as a supplier, which leaves a gap in India. |
| **Meedan Check** (open source; runs tiplines for AFP India, BOOM, Factly, Tsek.ph) | Takes video, images and audio via WhatsApp, Messenger, Telegram, LINE, Viber | No timestamped claim extraction found | 34 languages/dialects, 58 tiplines (2025) | Yes (NLP claim matching and clustering of similar tips) | No (newer: agentic RAG chatbot "Suwali" answering from verified reporting) | Main intake infrastructure in South and Southeast Asia. Clusters tips but does not break a video down into claims or draft a fact-check. Good integration target ("plugs into Check"). |
| **Google Fact Check Explorer / Fact Check Tools API** | Explorer has image search | n/a | Multilingual ClaimReview corpus | This *is* the match corpus | n/a | **Google deprecated the ClaimReview rich snippet in Search (June 2025)**, but the **Claim Search API and ClaimReview Read/Write API still work**. Gives a "close the loop" angle: approved drafts can be published *as* ClaimReview through the Read/Write API. |
| **Google DeepMind Backstory** (Trusted Testers, Aug 2026) | Images (provenance, SynthID, C2PA, manipulation, reverse search); agentic, built on Gemini | No | India Today testing it | No | No | First-pass verification: "50 minutes → about 3". Covers **image authenticity**, not spoken claims in video. Complementary, and the speed figure is a useful benchmark to quote. |
| **InVID-WeVerify / vera.ai plugin** (EU, 2022-2025) | Keyframes, reverse video search, OCR + translate, deepfake/voice-clone detectors | No | Translation only | No | No | Provenance/forensics toolkit, about 100k users/month (AFP, Bellingcat). No claim extraction. |
| **ClaimBuster** (UT Arlington) | Text (transcripts) | No | English | Limited | No | Classic check-worthiness scorer, English only. |
| **Deepfakes Analysis Unit (MCA India + Meta)** | WhatsApp tipline for audio/video; EN, Hindi, Tamil, Telugu | No | Yes, but scope is synthetic media | No | Publishes reports | 2024 data: only 2% deepfakes; **55% of tips were spam**. This is a strong triage-need data point. Scope is "is it AI-made?", not "is the claim true?". |
| **Shakti India Election Fact-Checking Collective (2024)** | Shared workflow among BOOM, The Quint, Vishvas, Factly, Newschecker etc. | No dedicated AI | Regional-language amplification | Shared tipline | No | Collaboration model, not a tool. Shows that a shared regional queue is how Indian fact-checkers actually work. |
| **Factly (India): Tagore AI, SACH, Dataful** | Text chatbot over Factly's own fact-checks; SACH searches 300k global fact-checks | No | EN, Telugu, Kannada | Yes (SACH retrieval) | Answers from existing content | Retrieval over past fact-checks. No video ingestion. |
| **Tattle (India)** | Feluda (multimodal media search for tipline archives), Uli (abuse filtering) | Media similarity matching | Indic | Media-level matching | No | Research ancestor: "Check Mate: Prioritizing User-Generated Multimedia Content for Fact-Checking" (ICWSM 2021, about WhatsApp tipline triage). |
| **Mafindo (Indonesia): Yudistira, Global Hoax Database, WhatsApp bot** | Bot searches about 3k-hoax database | No | Bahasa | Yes (DB lookup) | No | 2025: Komdigi + Mafindo + CekFakta building an AI deepfake/cross-format verification platform (soft launch). Focus is deepfakes. |
| **VERA Files (PH): SEEK chatbot** | RAG chatbot over 17 years of VERA Files journalism | No | EN/Filipino | Retrieval | Answers | Publishes Tagalog fact-checks of AI health-scam videos (see section 3). |
| **Rappler** | Uses deepfake detectors per check | No | — | — | — | No dedicated video claim-extraction tool found. PH government "TunAI" (May 2025 hackathon winner) is a citizen-facing fake-news checker. |
| **Cofacts / MyGoPen (Taiwan)** | LINE bots; MyGoPen got 1.3M requests (2023) | Not found | Mandarin/Taiwanese | Yes (crowd DB) | Cofacts reportedly has LLM "AI replies" (not verified this session) | Crowd model. Not a video claim extractor. |
| **Thailand AFNC (gov), Cofact TH** | AFNC plans hybrid AI + human verification | No | Thai | — | — | Government-led. Thailand is the fastest-growing market for TikTok-as-news (49%, DNR 2025). |

**Takeaway:** timestamped claim extraction from video exists (Factiverse, Raphael, Logically). Local-language drafting with an editor in the loop for South and Southeast Asian code-mixed short video does not. Meedan Check is the intake layer and Full Fact AI is the matching layer, but neither covers this lane, Full Fact has no APAC presence, and Logically Facts (the one with Hindi video) collapsed.

## 2. Hackathon and GitHub prior art (all shallow consumer "is this video true?" checkers)

- **Chestify** (Devpost): Gemini 1.5 Flash checks claims in Shorts/Reels/TikTok, gives a Verified/Misleading verdict, plus RAG chat over a video library. Consumer-facing.
- **itsarindrajit/FACT-CHECKER** (GitHub): paste a Shorts/Reels URL, get a fact-check report (Gemini 1.5 Flash + Groq Whisper + Tavily).
- **Ayushsri242/Instagram-Tech-Fact-Checker**: local multimodal checker for tech Reels, Hindi/Hinglish transcription.
- **alandaitch/live-fact-checker**: Gemini 2.0 Flash + Search grounding, live YouTube.
- **DylPorter/asterisk** (AI Tinkerers HK, Sep 2026): Android overlay that fact-checks YouTube Shorts (Gemini Flash + Exa).
- **Apify "Instagram Reel Fact Checker"**: web-grounded triage with verdicts and risk levels.
- **VeriFact AI, FactCheqr, Info Checker** (Devpost, Gemini 3 hackathon era): text/URL fact-checkers.
- **openstream/video-fact-checker, jfuentesa/video-fact-checker, VegarHauge/TikTokFactChecker** (Ollama), **jinto-joseph/vernacular-fact-checker** (text): 0-star repos.
- **Misinformation Guardian** (Feb 2026 sprint, Gemini Gem): an educational analyser.
- India **TruthTell Hackathon** (WAVES / Create in India 2025): real-time broadcast fact-checking, multilingual deepfake detection.

**Pattern:** dozens of "paste URL, get a verdict" consumer apps. **None** in this sample is built for a professional fact-checking desk: harm-ranked queue, ClaimReview cross-lingual match, local-language draft, editor approval, published back as ClaimReview. So the hackathon space is crowded at the generic level. The differentiation has to be the **newsroom workflow plus vernacular plus health-harm triage**. Judges will have seen "AI fact-checks a TikTok" many times.

## 3. Demand evidence (2024-2026)

**IFCN State of the Fact-Checkers 2025 report** (published Mar 2026; 141 orgs, 71 countries):
- **76% vulnerable or in crisis**; 45.3% saw revenue fall; funding is the top challenge (89.1%).
- **38.3% cut staff** in 2025, versus 14.9% in 2024. **61.7% have 10 or fewer full-time staff**, and 35.5% have 1-5.
- Meta third-party program: participation fell from 61.4% to 56.2%. **37.7% of Meta partners get more than half their revenue from Meta**, and 21.2% get 76-100%. USAID cuts hit Asia especially.
- Platforms cited as sources of false content: Meta platforms (FB/IG/**WhatsApp**) 78.1%, X 59.9%, **TikTok 59.1%**, YouTube 24.8%.
- **Public health** is covered by 86.1% of orgs.
- **53.3% have integrated AI** into workflows and only 5.1% use none. 73% expect AI to play a *supporting* role, which fits human-in-the-loop. Translation is an AI use case for 55.5%.
- **Short-form video** is the most effective format (72.3%); 60.6% publish in more than one language.

**Meta:** ended the US third-party program in Jan 2025. Outside the US, contracts were **renewed for 2026 at reduced funding**. Community Notes testing began in Latin America; the Oversight Board warned in Mar 2026 that Notes are not a global substitute. India's fact-checkers are the most Meta-dependent (Rest of World). **The premise "Meta ended fact-checking in Asia" is wrong. The accurate wording is "cut funding, US program ended, global rollout of Notes looming."**

**Google:** deprecated the ClaimReview snippet in Search in June 2025 without consulting fact-checkers (Poynter, Nieman Lab). The Fact Check Tools API (Claim Search + Read/Write) **still works**. Google.org gave Full Fact $2M (AI tools). The Google/YouTube $13.2M Global Fact Check Fund runs through IFCN. Google committed $1.2M to CekFakta (Indonesia). GNI has trained more than 222k journalists in APAC.

**Reuters Institute Digital News Report 2025:**
- In India, **WhatsApp is named the biggest misinformation threat by 53%**, the highest of any market.
- Top news sources in India: YouTube 55%, WhatsApp 46%, Instagram 37%.
- India, the Philippines (and Mexico) are "watch-first" markets.
- **Thailand: 49% use TikTok for news** (+10 points).
- **60% in APAC worry about telling real from fake.** Influencers are seen as a top source of false information (47%).

**Health misinformation cases (good demo material):**
- **Philippines:** a series of **AI-manipulated videos of cardiologist Dr. Willie Ong** selling fake cures (eye/lutein gummies Jul 2025, heart disease, prostatitis with Karen Davila, pertussis). VERA Files fact-checked them in English *and Tagalog*.
- **India:** Navjot Singh Sidhu's viral claim that his wife beat stage-4 cancer with diet and Ayurveda (Nov 2024, Newschecker; doctors debunked it).
- An India health-misinformation vectors report (Oct 2023 to Nov 2024) names cancer, reproductive health, vaccines and diabetes/obesity.
- BOOM has a dedicated health fact-check section.
- **Indonesia:** deepfake content up 550% (Sensity); most deepfakes are used for fraud, including health scams.

**Time and volume pain:**
- Full Fact detects about 500k checkable items a day, so the bottleneck is *choosing*, not finding.
- The DAU tipline was 55% spam, and only 2% of tips were real deepfakes, which argues for triage.
- Backstory cut first-pass image verification from 50 minutes to 3 (India Today).
- General literature: a professional fact-check takes "several hours to days" (TACL survey). I found **no authoritative hours-per-fact-check figure for Asia**. Treat any specific number as something to measure in the demo, not to cite.

**Limits of current LLMs:** Reuters Institute (Apr 2024) reports generative AI is "less useful in small languages and outside the West", citing ChatGPT problems in Bengali and Thai. This supports a vernacular-first tool, and is a risk to address with an eval.

## 4. Before/after metrics and public demo data

**Candidate metrics (measure on your own sample; do not claim them as industry numbers):**
1. **Time-to-first-claim-list:** watching or transcribing a 3-minute Hinglish reel by hand versus the tool. Target "about 15 min → under 1 min". For long video, use Raphael's framing: a 2-hour podcast reduced to the timestamped segments that matter.
2. **Triage precision:** of the top-k items the tool ranks as high-harm, how many a professional fact-checker would pick. Check-worthiness F1 against labelled data; ShortCheck's baseline is F1 about 0.70.
3. **Duplicate-catch rate:** the share of incoming forwards matched to an *existing* fact-check, including cross-lingual pairs (e.g. a Tamil video matched to an English BOOM article). Each match is a fact-check that never has to be written again.
4. **Draft acceptance:** the share of local-language drafts an editor approves with light edits, plus the edit distance.
5. **Time-to-publish** for a debunk: tip, then draft, then approved ClaimReview.

**Public data:**
- **MultiClaim** (Pikuliak et al. 2023): 28k social posts in 27 languages and 206k fact-checks in 39 languages, with 31k post-to-fact-check pairs (4.2k cross-lingual). Includes Hindi, Bengali, Tamil, Thai, Indonesian, Malay, Tagalog-adjacent languages. Also used by **SemEval-2025 Task 7** (multilingual and cross-lingual fact-checked claim retrieval). Use it to evaluate the matching step.
- **Google Fact Check Claim Search API**: live ClaimReview corpus by language (`languageCode=hi`, `ta`, `bn`, `tl`, `id`, `th`, `vi`) for retrieval at demo time.
- **ShortCheck datasets** (Faktisk TikTok set plus a TikTok-from-fact-check-sites set), FakeTT (English TikTok), FakeSV (Chinese Douyin/Kuaishou): check-worthiness and fake-video baselines.
- Indic sets: MMCFND (28k items, 7 Indic languages, multimodal), a Tamil multimodal fake-news dataset including 884 minutes of speech, HinFakeNews (68k Hindi items), BharatGather (2026).
- **Demo videos:** pick public, already-debunked viral clips whose fact-check URLs are in ClaimReview (e.g. VERA Files' Willie Ong deepfake ads, BOOM/Newschecker health claims). This gives ground truth for an honest before/after. Respect platform terms of service: download clips via embed links or use the fact-checkers' own archived copies, and do not redistribute.

## 5. Sharpest differentiated framing

**"The night-shift desk for a 5-person fact-checking team: one queue, 200 vernacular forwards, the 3 that can kill someone on top."**

- **Named user:** the lone duty editor at a small IFCN signatory (e.g. the Tagalog desk at VERA Files / Tsek.ph, or the Tamil desk at a Shakti-collective member). This is a real profile: 61.7% of orgs have 10 or fewer staff, 38% cut staff in 2025, and Meta money is shrinking.
- **Slow workflow:** watch each WhatsApp/TikTok forward, transcribe code-mixed speech, decide whether it is checkable, search for prior fact-checks across languages, write a debunk in the local language.
- **What makes it new** (together, these are not covered by Full Fact AI, Factiverse, Meedan Check or Backstory):
  1. **Code-mixed Asian speech plus on-screen text** (Hinglish, Taglish, Bisaya) handled natively by Gemini's video+audio model, with timestamps. No Whisper-plus-OCR stitching.
  2. **Cross-lingual "already debunked?" matching** of a Tamil reel against English, Hindi or Tagalog ClaimReview (Fact Check Tools API plus Gemini embeddings, evaluated on MultiClaim/SemEval-2025 T7). This turns repeat work into a 30-second reuse.
  3. **Health-harm triage:** a rubric for the cost of acting on the claim (stop medication, unproven cure, scam purchase), plus a deepfake-ad flag for the "fake doctor endorsement" pattern.
  4. **Draft in the local language with the timestamp cited**, editor approval, then **publish back as ClaimReview through Google's still-live Read/Write API**. This closes the loop and keeps the ClaimReview ecosystem alive after Google dropped the snippet. Strong Google-tech depth.
- **Integration story:** sits behind existing Meedan Check tiplines (WhatsApp/Messenger/LINE) as a triage-and-draft layer, so it complements tools fact-checkers already use instead of replacing them.
- **Sponsor depth:** Gemini 2.5/3 long-video and audio understanding with timestamps, Gemini embeddings for cross-lingual retrieval, Gemma for an on-prem or low-cost first-pass filter (spam: the DAU saw 55% spam), Cloud Run, Firestore editor queue, Fact Check Tools API.
- **Avoid:** pitching "AI decides true or false." IFCN respondents expect AI to support, not lead (73%), and judges have seen many verdict apps. Keep the human editor as the decision-maker.
- **Differentiation from other Media-track teams:** Gapline (audio description), OmniLocate (ad localisation), SEEN (cricket analytics) and curriculum projects do not overlap. This is the only public-interest and health-stakes entry in the list.

## Sources

- Full Fact Raphael/Gemini health video: https://newsmachines.beehiiv.com/p/how-full-fact-scales-human-fact-checking-with-ai-1 ; https://generative-ai-newsroom.com/how-full-fact-uses-generative-ai-to-find-harmful-health-advice-b0e05382ab90 ; https://fullfact.org/ai/
- Google.org and Full Fact: https://blog.google/outreach-initiatives/google-org/fullfact-and-google-fight-misinformation/
- Factiverse: https://hellofuture.orange.com/en/factiverse-reliable-ai-fact-checking-in-more-than-100-languages ; ShortCheck: https://aclanthology.org/2025.ijcnlp-demo.9.pdf
- Logically Accelerate: https://www.logically.ai/announcements/logically-accelerates-fact-checking-with-launch-of-new-product ; collapse: https://en.wikipedia.org/wiki/Logically_(company) ; https://sifted.eu/articles/anti-misinformation-startup-logically-lays-off-dozens-in-global-cost-cutting-drive
- Meedan Check: https://meedan.org/check ; https://meedan.org/post/2025-in-retrospect-toward-information-equity-together
- Backstory: https://www.niemanlab.org/2026/08/googles-new-ai-tool-helps-fact-checkers-investigate-ai-fakes/ ; https://mediacopilot.ai/google-backstory-image-verification-fact-checkers/
- ClaimReview snippet removal: https://www.niemanlab.org/2025/06/google-kills-the-fact-checking-snippet/ ; https://www.poynter.org/ifcn/2025/google-claimreview-fact-checks-snippets-removed/ ; API: https://developers.google.com/fact-check/tools/api
- IFCN 2025 report (pub. Mar 2026): https://www.poynter.org/wp-content/uploads/2026/03/2026-State-of-Fact-Checkers-4.pdf
- Meta: https://restofworld.org/2025/meta-drops-fact-checking-partnerships-global-watchdogs-scramble/ ; https://www.niemanlab.org/2026/03/metas-oversight-board-warns-that-community-notes-arent-a-proper-substitute-for-fact-checking-globally/ ; https://www.oversightboard.com/decision/pao-007g5zuv/
- Reuters DNR 2025: https://ruralindiaonline.org/en/library/resource/reuters-institute-digital-news-report-2025 ; Reuters Institute on GenAI and small languages: https://reutersinstitute.politics.ox.ac.uk/news/generative-ai-already-helping-fact-checkers-its-proving-less-useful-small-languages-and
- DAU: https://www.medianama.com/2024/09/223-deepfake-analysis-unit-report-most-media-alterations-done-with-basic-tools-only-2-deepfakes/
- Shakti: https://gijn.org/stories/lessons-learned-india-fact-checking-collective/ ; Factly: https://wan-ifra.org/2025/05/from-norway-to-india-how-ai-is-reshaping-global-fact-checking-efforts/
- Mafindo: https://civictech.guide/projects/mafindo ; https://en.antaranews.com/news/362473/indonesian-govt-csos-to-develop-tool-to-detect-deepfakes
- VERA Files Willie Ong deepfakes: https://verafiles.org/articles/fact-check-ai-manipulated-clips-of-willie-ong-used-for-fake-eye-product-endorsement
- India health misinformation: https://cyberpeace.org/resources/blogs/health-related-social-media-content-a-misinformation-vector-in-india ; https://newschecker.in/fact-check/weekly-wrap-misinformation-around-chinmoy-das-navjot-singh-sidhus-cancer-cure-claims-and-more
- Thailand AFNC: https://www.thaipbs.th/verify/en/news/content/10792
- vera.ai/InVID: https://media-and-learning.eu/type/tools/vera-ai-ai-tools-to-spot-deepfakes-and-disinformation/
- MultiClaim: https://arxiv.org/pdf/2305.07991 ; SemEval-2025 T7: https://arxiv.org/pdf/2505.10740
- FakeSV/FakeTT: https://arxiv.org/pdf/2504.21495 ; MMCFND: https://arxiv.org/pdf/2410.10407
- Check Mate (ICWSM): https://ojs.aaai.org/index.php/ICWSM/article/view/18126
- Hackathon/GitHub: https://devpost.com/software/chestify ; https://github.com/itsarindrajit/FACT-CHECKER ; https://github.com/Ayushsri242/Instagram-Tech-Fact-Checker ; https://github.com/alandaitch/live-fact-checker ; https://github.com/DylPorter/asterisk ; https://apify.com/rainminer/instagram-reel-fact-checker ; https://devpost.com/software/verifact-ai ; https://frankx.ai/blog/misinformation-guardian-hackathon-build-log-2026
