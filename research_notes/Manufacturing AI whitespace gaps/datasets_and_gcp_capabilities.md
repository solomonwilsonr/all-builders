# Public Manufacturing Datasets and Gemini / Google Cloud Capabilities for a 10-Day AI Builder Cup 2026 Prototype

Research date: 2026-10-07. Covers about 17 searches and fetches. Model listings change quickly, so check model IDs again on build day.

## Q0. Competition constraints (context for buildability)

### Takeaway
The AI Builder Cup 2026 is a JAPAC hackathon for working professionals. Manufacturing is one of six themes. Prototypes must run on Gemini or Gemma (or Agent Platform, Antigravity or AI Studio) and be deployed on Cloud Run or Firebase. Registration and team formation close Oct 11, 2026 and prototypes are due Oct 18, 2026. The window is very tight.

### Cited Findings
- Event dates: Sep 23 to Oct 11, 2026 (registration and team formation). Prototype submission closes Oct 18. The Grand Finale is in Singapore on Dec 4, 2026. Total prize pool is USD 30,000. Teams have 2 to 4 members, each aged 21 or over, from the JAPAC region. — [Metropolis Japan event page](https://metropolisjapan.com/events/ai-builder-cup-2026/)
- There are six themes: BFSI, Retail & Commerce, Manufacturing, Media & Digital Experiences, Future of Work, and Sustainability & Social Impact. Solutions "must run on Google AI models like Gemini or Gemma, or be built on agentic platforms such as Agent Platform, Antigravity, or AI Studio" and be "deployed on Google Cloud via Cloud Run or Firebase." — [Metropolis Japan](https://metropolisjapan.com/events/ai-builder-cup-2026/); [opportunitiescorners (aggregator)](https://opportunitiescorners.com/google-cloud-ai-builder-cup-2026-in-singapore/)
- The event page did not state judging criteria or a credit allocation. — [Metropolis Japan](https://metropolisjapan.com/events/ai-builder-cup-2026/)

### Inferences
- "Agent Platform" in the rules almost certainly means the rebranded Vertex AI ("Gemini Enterprise Agent Platform", see Q2). Teams can therefore use Vertex AI Agent Engine and ADK and still count as compliant.
- The Sustainability theme overlaps with CBAM and energy ideas. A manufacturing-plus-emissions idea could fit either theme.

### Gaps
- I could not find the official judging rubric or the full manufacturing problem statement. The Google-hosted challenge page did not come up in searches.

---

## Q1. Public datasets by manufacturing problem type

### Takeaway
There is a lot of well-licensed public data for predictive maintenance (tabular, time series and audio), visual defects and process quality. Unstructured "factory text" is the thin area: work orders and CMMS logs, SOPs and manuals. The best public options there are MaintNet (small, about 6k aviation records) and OSHA Severe Injury Reports (large, with narratives). Several of the best vision datasets are licensed CC BY-NC-SA, which is fine for a hackathon demo but not for commercial use.

### Cited Findings

**Predictive maintenance (tabular / time-series)**
- **AI4I 2020 Predictive Maintenance (UCI #601)**: synthetic data, 10,000 instances, 6 features (air and process temperature, rotational speed, torque, tool wear, product type) plus failure labels (TWF, HDF, PWF, OSF, RNF). License is CC BY 4.0. Suits failure classification and root-cause explanation. — [UCI](https://archive.ics.uci.edu/dataset/601)
- **NASA C-MAPSS turbofan**: five run-to-failure datasets from a turbofan simulation, published in the NASA Prognostics Center of Excellence repository (established 2007). Suits RUL (remaining useful life) prediction. — [data.nasa.gov](https://data.nasa.gov/dataset/activity/c-mapss-aircraft-engine-simulator-data); [PHM Society mirror](https://data.phmsociety.org/nasa/); [data.gov catalog](https://catalog-old.data.gov/dataset/cmapss-jet-engine-simulated-data)

**Machine sound / acoustic anomaly**
- **MIMII**: sounds from valves, pumps, fans and slide rails. About 26,000 normal and about 6,000 abnormal clips, each 10 s at 16 kHz, about 100 GB in total. License is CC BY-SA 4.0. — [Zenodo](https://zenodo.org/record/3384387)
- **DCASE 2020 Task 2 dev set** (built from MIMII and ToyADMOS) is a smaller packaged option. — [Zenodo](https://zenodo.org/record/3678170)

**Visual defect / anomaly detection**
- **MVTec AD**: more than 5,000 high-resolution images in 15 object and texture categories, about 4.9 GB. License is CC BY-NC-SA 4.0, explicitly non-commercial. — [MVTec](https://www.mvtec.com/company/research/datasets/mvtec-ad); [Voxel51 / HF](https://docs.voxel51.com/dataset_zoo/datasets_hf/mvtec_ad.html)
- **VisA**: 10,821 images, roughly double MVTec AD. — [arXiv 2501.17289 (secondary description)](https://arxiv.org/pdf/2501.17289)
- **KolektorSDD2**: 3,335 colour images of production items with pixel-wise defect masks. License is CC BY-NC-SA 4.0. — [ViCoS](https://www2.vicos.si/resources/kolektorsdd2/)
- **DeepPCB**: 1,500 PCB image pairs (640x640 template plus tested image) covering 6 defect types: open, short, mousebite, spur, pin hole, spurious copper. License is MIT. — [GitHub](https://github.com/tangsanli5201/DeepPCB); [arXiv 1902.06197](https://arxiv.org/pdf/1902.06197)
- **NEU-DET (NEU surface defect)**: hot-rolled steel surface images covering 6 defect types. — [TIB surface-defect group](https://service.tib.eu/ldmservice/group/surface-defect-detection)

**Process / quality (tabular)**
- **SECOM (UCI #179)**: semiconductor process data, 1,567 instances by 591 features, with pass/fail labels and timestamps. Heavy missing values. — [UCI](https://archive.ics.uci.edu/dataset/179/secom)
- **Bosch Production Line Performance (Kaggle 2016)**: 1,183,747 parts, 4,264 features, 4 segments and 52 workstations, about 4,700 unique paths through the line. Suits detection of rare internal failures. — [arXiv 1701.00705](https://arxiv.org/html/1701.00705); [arXiv 2407.01644](https://arxiv.org/pdf/2407.01644)

**Maintenance logs / work-order text**
- **MaintNet**: an open-source library of maintenance logbook data from aviation, automotive and facility maintenance, with NLP tools for spell-check, segmentation, POS tagging, clustering and classification (COLING 2020 demo). — [ACL Anthology](https://aclanthology.org/2020.coling-demos.2); [AACL demo](https://aclanthology.org/2020.aacl-demo.5)
- The MaintNet aviation subset has 6,169 records and 76,866 tokens, with free-text "problem" and "action" fields. — [Baselight / Kaggle mirror](https://baselight.app/u/kaggle/dataset/merishnasuwal_aircraft_historical_maintenance_dataset)

**Industrial safety**
- **OSHA Severe Injury Reports (SIR)**: amputations, in-patient hospitalizations and eye losses reported since Jan 1, 2015. Each record includes a narrative description, the establishment name and address, NAICS code and OIICS codes. The full dataset downloads from the dashboard. It covers federal-OSHA jurisdiction only and excludes state-plan states. — [OSHA SIR](https://osha.gov/severe-injury-reports); [OSHA](https://osha.gov/severeinjury)

**Emissions / CBAM**
- The EU Commission published CBAM definitive-period default values and benchmarks in Excel, under Implementing Regulation (EU) 2025/2621. The file covers Annex I direct emissions only and does not include indirect emissions or electricity. — [Finnish Customs (tulli.fi)](https://tulli.fi/en/-/the-default-values-and-benchmarks-for-the-cbam-definitive-period-have-been-published-in-excel-format-there-are-also-new-guidance-videos-on-the-cbam-registry)
- The transitional-period default values PDF is on the EC site. — [EC PDF](https://taxation-customs.ec.europa.eu/system/files/2023-12/Default%20values%20transitional%20period.pdf)
- A corrected CBAM default-values Excel was released in Aug 2026, and most values went down. — [cbamguide.com (secondary)](https://cbamguide.com/news/2026-08-13-cbam-default-values-corrected-excel-values-down/)
- Secondary tools are available: the `opencbam` PyPI package, the cbamguide CSV export, and the Climatiq CBAM source. — [PyPI](https://pypi.org/project/opencbam/); [cbamguide](https://cbamguide.com/tools/data/); [Climatiq](https://climatiq.io/data/source/cbam)

### Inferences
- **Easiest datasets to build on in 10 days**: AI4I (small, clean CSV, CC BY), DeepPCB (MIT, small), MVTec AD (demo-only license), OSHA SIR (large narrative text, public domain US-gov data, though the license is not stated explicitly on the page) and the CBAM Excel.
- MIMII's 100 GB is too large to download in full. Use one machine type, or use the DCASE 2020 Task 2 dev subset.
- No public dataset joins sensor data, work orders, manuals and images for the same asset. Teams will have to synthesize the links between them, for example by generating work orders with Gemini against AI4I failures. Say this openly in the demo.

### Gaps (not verified in this session; check before relying on them)
- **Not verified this session**: Microsoft Azure Predictive Maintenance (Kaggle, about 876k telemetry rows plus errors, maintenance and failures tables), CWRU bearing data (Case Western engineering site), ToyADMOS, MVTec LOCO AD, DAGM 2007, the VisA license (believed CC BY 4.0, Amazon), the NEU-DET size and license (commonly cited as 1,800 images), and the C-MAPSS licence and exact size.
- **Not found**: a public CMMS work-order corpus beyond MaintNet, and a public SOP or manual corpus for manufacturing. Likely workarounds are OEM manual PDFs or synthetic SOPs.
- **Not researched (budget ran out)**: energy-consumption datasets (for example steel-industry energy on UCI) and supply-chain datasets (for example DataCo on Kaggle).

---

## Q2. Gemini / Google Cloud capabilities as of Oct 2026

### Takeaway
The Gemini 3.x family is current. Gemini 2.5 retires on Vertex on Oct 16, 2026, so do not build on it. Gemini's long-video, audio, PDF and image understanding, Live API voice agents, and Gemma 4 edge models (Apache 2.0) make multimodal "shop-floor copilot" ideas buildable in 10 days. ADK 2.x ships with MCP and A2A support. Vertex AI is now branded "Gemini Enterprise Agent Platform."

### Cited Findings

**Models**
- Gemini 3 timeline: 3 Pro and Deep Think on Nov 18, 2025; 3 Flash in Dec 2025; 3.1 Pro on Feb 19, 2026; 3.5 Flash at I/O on May 19, 2026. — [blog.mean.ceo (aggregator)](https://blog.mean.ceo/?p=5076)
- Vertex release notes list: Gemini 3.1 Pro Preview with a 1M-token context (Feb 19, 2026); Gemini 3 Flash Preview (Feb 10, 2026); Gemini 3.1 Flash-Lite, the most cost-efficient model (Mar 3, 2026); Gemini 3.1 Flash Image / "Nano Banana 2" (Feb 26, 2026). — [Vertex AI release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en)
- **Gemini 2.5 Pro, Flash and Flash-Lite retire on Oct 16, 2026.** — [Vertex AI release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en)
- The live Gemini API models page (fetched 2026-10-07) lists these stable models:
  - Text: `gemini-3.8-flash` (latest Flash, aimed at agents and coding), plus 3.7, 3.6 and 3.5 Flash, `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`.
  - Live: `gemini-3.8-live` and `gemini-3.8-live-extended-thinking`.
  - TTS: `gemini-3.8-flash-tts`.
  - Transcription: `gemini-3.5-transcribe` and `-live`, with diarization.
  - Image: `gemini-3-pro-image` and `gemini-3.1-flash-image`.
  - Other: `gemini-embedding-2-preview` (multimodal embeddings), `deep-research-preview-04-2026` and `antigravity-preview-09-2026` (managed agent).
  - Preview: `gemini-3.1-pro-preview`.

  Source: [Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- **Conflict**: the Vertex release-notes fetch did not surface the 3.6 to 3.8 entries (possibly truncated), and Vertex availability may lag the Gemini API. Check model IDs in your region before building. — [Vertex release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en) vs [Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- Gemma 4 on Vertex: Gemma 4 26B A4B IT (multimodal text and image) launched experimentally on Apr 3, 2026. — [Vertex release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en)
- The rebrand to "Gemini Enterprise Agent Platform" appears in 2026 entries. Vertex AI Extensions are deprecated and shut down after Nov 26, 2026, with migration to Agent Platform recommended. — [Vertex release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en)

**Video understanding (inspection video, operator videos, SOP-from-video)**
- 1M-context models handle up to 3 hours of video at low media resolution, or 1 hour at high resolution.
- Default sampling is 1 frame per second, and a custom fps is configurable.
- Token cost is about 100 tokens per second of video at low resolution and about 300 at high resolution.
- File API limits are 20 GB (paid) and 2 GB (free). Up to 10 videos per request. Public YouTube URLs are supported, with an 8 hours/day cap on the free tier. Timestamps can be referenced as MM:SS.

  Source: [Gemini video understanding docs](https://ai.google.dev/gemini-api/docs/video-understanding)

**Live API / voice**
- Gemini 2.5 Flash Native Audio reached GA on Vertex on Dec 12, 2025, with Proactive Audio and Affective Dialog. — [Vertex release notes](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes?hl=en)
- Newer `gemini-3.8-live` models are listed for low-latency voice agents. — [Gemini API models](https://ai.google.dev/gemini-api/docs/models)

**Gemma (edge / on-prem)**
- Gemma 4 was released Apr 2, 2026 under Apache 2.0, the first Gemma under an OSI licence. It comes in four sizes: E2B (2.3B effective), E4B (4.5B effective), 26B MoE (4B active) and 31B dense. — [Gigazine](https://www.gigazine.net/gsc_news/en/20260403-google-released-gemma-4); [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/google-releases-gemma-4-frontier-open-models-under-apache-2-0/)
- E2B and E4B run offline on phones, Raspberry Pi and Jetson Orin Nano, and accept native audio input. — [techwyse (secondary)](https://www.techwyse.com/news/ai-search/google-deepmind-gemma-4-open-models-apache-2-0-release)

**Agents: ADK / Agent Engine / A2A / MCP**
- ADK is open source and now at 2.x. Version 2.1 shipped in May 2026 for Python 3.11+ and Java 17+. It has sub-agents, tools, sessions, memory and callbacks, first-class MCP tool integration, and native A2A bindings. — [neurals.ca (secondary)](https://neurals.ca/tech/gemini/adk/)
- Agents can run locally, on Vertex AI Agent Engine, or on Cloud Run or Docker. — [Google Developers Blog](https://developers.googleblog.com/agents-adk-agent-engine-a2a-enhancements-google-io/)
- A2A uses Agent Cards for discovery and handles multi-turn async tasks. It now sits under AAIF alongside MCP. — [codeforweb substack (secondary)](https://codeforweb.substack.com/p/the-agent-stack-is-the-new-full-stack)
- **Source conflict**: that source says A2A was "proposed by Google in early 2026." A2A was actually announced in April 2025, so treat that source's dating as unreliable.
- An official codelab covers building a multi-agent system with ADK, deploying it to Agent Engine, and using A2A. — [Google Codelab](https://codelabs.developers.google.com/codelabs/create-multi-agents-adk-a2a)
- The `google/adk-samples` repo has samples in Python, TS, Go, Java, Kotlin and Android (for example customer-service, data-engineering, financial-advisor, llm-auditor). There is no manufacturing-specific sample. — [adk-samples README](https://cdn.jsdelivr.net/gh/google/adk-samples@main/README.md)

### Inferences (what is realistic in 10 days)
**Buildable in 10 days**
- An ADK multi-agent app on Cloud Run with Gemini 3.x Flash.
- RAG over PDFs: put manuals in Cloud Storage and use either the Gemini File API or Vertex AI Search.
- Image defect triage with Gemini vision used few-shot on MVTec or DeepPCB images.
- Video SOP extraction or compliance checks with Gemini video understanding.
- A Live API voice assistant for technicians.
- Tabular anomaly detection with BigQuery ML on AI4I or SECOM, with Gemini explaining the results.

**Risky in 10 days**
- Streaming pipelines (Pub/Sub plus Dataflow), unless the data source is simulated.
- Fine-tuning Gemma.
- On-device Gemma 4 deployment, which also falls outside the Cloud Run/Firebase deploy requirement unless the device is only a client.
- Manufacturing Data Engine, which is a partner-delivered enterprise product.

**Model choice**: use Flash or Flash-Lite for cost and Pro only where reasoning matters. Do not depend on any 2.5 model ID.

### Gaps
- I could not directly confirm current Gemini 3.x pricing per 1M tokens.
- I could not confirm the GA or preview status of each 3.6 to 3.8 model on Vertex.
- I did not verify Vertex AI Search, Document AI or Imagen/Veo specifics this session.

---

## Q3. Google Cloud manufacturing reference architectures and accelerators

### Takeaway
Manufacturing Data Engine (MDE) and Visual Inspection AI exist but are enterprise-oriented. MDE is often delivered through partners such as GFT. They are useful as architecture and pitch references, not as 10-day building blocks. The ADK codelabs and samples are the practical accelerators.

### Cited Findings
- MDE supports visual line inspection, predictive maintenance and production forecasting. In a demo, Visual Inspection AI checked laser engravings on keychains and fed QC metrics into MDE dashboards. — [GFT IMTS 2024 blog](https://gft.com/us/en/blog/in-case-you-missed-it-imts-2024)
- GFT and Google Cloud built Gemini apps covering:
  - defect root-cause analysis
  - natural-language querying of plant data
  - prediction of parts obsolescence
  - turning machine training manuals into avatar-led videos

  Sources: [GFT press release, Apr 2025](https://www.gft.com/us/en/about-us/newsroom/press-and-news/2025/press-releases/gft-and-google-cloud-collaborate-on-new-ai-application-for-gemini-models); [BusinessWire](https://www.businesswire.com/news/home/20250429700767/en)
- Google Cloud has a manufacturing solutions hub. — [cloud.google.com/solutions/manufacturing](https://cloud.google.com/solutions/manufacturing/)

### Inferences
- GFT's use cases (root cause, NL plant query, manuals-to-video) are already partly covered commercially. A hackathon entry should differentiate, for example on SME-scale deployment, JAPAC language support, or combining safety and maintenance text.

### Gaps
- I did not locate the current MDE GitHub reference repo, a Visual Inspection AI codelab, or its deprecation status for 2026.

---

## Q4. Free credits and cost

### Takeaway
New Google Cloud accounts get a $300, 90-day credit. That credit cannot pay for Gemini API usage through AI Studio, so use either the Gemini API free tier or Vertex AI billed against the credit. The event page states no hackathon-specific credits.

### Cited Findings
- The Free Trial gives $300 in credit for 90 days plus Free Tier limits. The $300 cannot be used for Gemini API costs in AI Studio, so use the Gemini API free tier there. — [Google Cloud Free docs](https://docs.cloud.google.com/free)
- Google events (Gemma hackathons, Vertex AI Builder campaigns) often award $300 to $1,000 in credits. — [tenten university forum (secondary)](https://university.tenten.co/t/free-google-vertex-ai-credits-up-to-us-1-000/2107)
- The File API limit is 2 GB on the free tier and 20 GB on paid. YouTube video input is capped at 8 hours/day on the free tier. — [Gemini video docs](https://ai.google.dev/gemini-api/docs/video-understanding)

### Inferences
- Video is the main cost driver at about 100 to 300 tokens per second, or roughly 360k to 1M tokens per hour of footage. Keep demo clips short and use low media resolution.
- Each team member can open their own trial project. Pick one billing project for the deployed Cloud Run app so the judges' demo is stable.

### Gaps
- I did not find whether AI Builder Cup participants get organizer-provided credits.
- I did not verify the Cloud Run free-tier numbers this session.
