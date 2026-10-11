# Prior-Art Check: Gemini agent to auto-fill RDANA / DROMIC / OCD sitreps from citizen photos and voice notes (Philippines)

Check date: 2026-10-08. Sources: web search (standard and extended), GitHub API code and repo search, and direct reads of the WFP PRISM source code.

## The idea, split into components
- **C1 Multimodal citizen and responder intake.** Photos plus voice notes in Tagalog, Bisaya or English, sent after a typhoon or flood.
- **C2 LLM/VLM extraction.** Pulls structured damage and needs out of each report: houses partially or totally damaged, injured, displaced, food and water needs.
- **C3 Geotagging and deduplication.** Clusters reports of the same house or event.
- **C4 Fusion with remote sensing.** Merges reports with satellite imagery and Google Open Buildings footprints (SKAI-style).
- **C5 Auto-filled official forms.** Fills the OCD RDANA form and the DSWD DROMIC / NDRRMC situation-report templates that LGUs must submit under RA 10121.

---

## 1. Products and platforms

| # | Name | URL | What it does | Overlap | Components |
|---|------|-----|--------------|---------|-----------|
| 1 | **WFP PRISM** (Platform for Real-time Impact and Situation Monitoring) | https://innovation.wfp.org/project/prism ; https://github.com/WFP-VAM/prism-app | Open-source map dashboard that layers hazard, exposure and vulnerability data. Has threshold alerts, exposure analysis with PDF reports, and a **KoBo integration** that plots field-form submissions on the map. **Not deployed in the Philippines:** the repo has configs for Cambodia, Indonesia, Sri Lanka, Mongolia, Mozambique and ~30 more, but no `philippines` config, only a PHL translation file. No LLM, no photo or voice analysis, no RDANA or DROMIC output. Also not to be confused with **PhilRice PRISM** (the Philippine Rice Information System), which does satellite rice-damage assessment for DA. | Partial (low) | C4 (hazard exposure), weak C1 (structured KoBo forms only) |
| 2 | **Mobile RDANA App** | https://www.facebook.com/RDANAMobileApp | A digital RDANA form app. It replaced paper RDANA for e.g. 22 BDRRM teams in San Fernando, Camarines Sur (training by HumDev Management Consultancy). Trained assessors fill in the form fields by hand. No AI and no citizen intake. | Partial | C5 (digital RDANA output), C1 (assessor-only, manual) |
| 3 | **DSWD DROMIC IS v2 / Online Rapid Data Collector / DROMIC Virtual Ops Center** | https://dromic.dswd.gov.ph/online-rapid-data-collector/ ; https://car.dswd.gov.ph/2024/06/dswd-field-office-car-launches-dromic-is-v-2-sets-trend-in-disaster-response/ | The official DSWD system for affected families, displaced people, evacuation centers (ECs) and family food packs (FFPs). v2 (May 2024) adds automated forms and templates. LGU and field-office staff enter the data by hand. DROMIC guidelines were revised by MC No. 12 s. 2026, and an MOU with UP Resilience Institute (Feb 2026) covers AI for **forecasting**, not for reporting. | Partial (it is the target system, not a competitor) | C5 (official DROMIC output, manual) |
| 4 | **DepEd RADaR** (Rapid Assessment of Damages Report) | https://reliefweb.int/report/philippines/deped-partners-launch-radar-app-ensure-learning-continuity-after-disasters | Mobile and web app (2020, DepEd with Save the Children and Prudence Foundation) for school damage, casualties, ECs and learning-space needs. Uses manual structured forms. | Partial | C5 (sector-specific damage reporting, manual) |
| 5 | **LyfSaver x Quezon City** | https://tribune.net.ph/2026/08/27/qc-taps-ai-citizen-reports-for-faster-disaster-response ; https://mb.com.ph/2026/08/26/qc-lyfsaver-roadshow-launched-to-speed-up-disaster-reporting | "Crowdsource, verify, mobilize" citizen-report platform, launched in 2024 and partnered with QC in Aug 2026. Uses UP NOAH maps and Fyt Media crowdsourcing. **AI-assisted verification and aggregation is being tested**, and reports feed Helpline 122, iReport, QC DRRMO and barangays. No public evidence that it extracts structured damage counts or fills RDANA/DROMIC forms. | **Partial (closest live PH deployment)** | C1, C3 (verification), early C2 |
| 6 | **MapaKalamidad.ph** (PetaBencana / Yayasan Peta Bencana, PhilAWARE) | https://www.rappler.com/moveph/agos/mapakalamidad-ph-app-helps-citizens-map-flooded-areas-disasters/ | Since 2020, AI "humanitarian chatbots" on FB Messenger, Telegram and X collect geolocated citizen flood photos and descriptions and put them on real-time maps. Covers flood extent and depth, not damage or needs counts, and produces no forms. | Partial | C1, C3 (geotag/map) |
| 7 | **Rappler Project Agos / eBayanihan** | https://amp.rappler.com/move-ph/issues/disasters/95880-project-agos-push-zero-casualty-goal-northern-mindanao | Crowdsourced map of SMS (2929) and hashtag reports (#RescuePH, #ReliefPH) covering damage, rescue and relief needs. Classification is by volunteers or rules. Dates from 2013-2015. | Partial | C1, C3 (map) |
| 8 | **PhilAWARE** (OCD with Pacific Disaster Center) | https://www.pdc.org/ | NDRRMC Ops Center decision-support system: multi-hazard monitoring, exposure and impact estimates. Part of the 2024 National Disaster Response Plan (NDRP). Model-based, with no citizen-report extraction. | Partial (low) | C4 |
| 9 | **PDRF EOC mobile GIS rapid damage assessment** | https://www.esri.com/about/newsroom/blog/philippines-private-led-disaster-resilience | Private-sector EOC. Member companies file rapid damage assessments through a mobile GIS (Esri) app. Manual entry, no AI. | Partial (low) | C1 (structured), C3 (GIS) |
| 10 | **Alerto PH / Alerto GOV** | https://stii.dost.gov.ph/2103-how-alerto-ph-app-can-boost-lgus-emergency-disaster-response-capabilities-the-rise-of-filipino-inventors-in-drrm | LGU command-center app (DOST/DICT-supported) that combines IoT alarms, citizen alerts and "AI" aggregation. Built for incident response, not for RDANA. | Low | C1 |
| 11 | **Bagyo.app / Aeris AI agent** | https://bitpinas.com/ai/aeris-ai-report/ | Typhoon chatbot built with "vibe coding". Published an AI-written Typhoon Uwan impact report (Nov 2025) by aggregating **published** figures, framed as useful for DSWD and OCD. Does not take in citizen photos or voice and does not fill official forms. | Partial (low) | output-side "AI sitrep" only |
| 12 | **Google SKAI + Open Buildings** (with WFP Innovation Accelerator and UN Global Pulse) | https://github.com/google-research/skai ; https://www.unglobalpulse.org/ai-from-google-research-and-un-boosts-humanitarian-disaster-response-wider-coverage-faster-damage-assessments | Building-damage classification from satellite imagery (zero-shot and fine-tuned) on Open Buildings footprints. No confirmed Philippines operational use. No ground photos, no needs extraction, no forms. | Partial | C4 (exactly the satellite half) |
| 13 | **Microsoft AI for Good HASTE** | https://microsoft.github.io/haste/usage/overview.html | Building-damage mapping from satellite imagery after labelling a small sample. | Partial | C4 |
| 14 | **xView2 / xBD** | https://xview2.org | Benchmark and models for satellite building damage. | Partial | C4 |
| 15 | **HOT / OpenStreetMap Tasking Manager** | https://tasks.hotosm.org | Volunteer mapping of buildings and damage (e.g. Haiyan 2013, Kristine 2024). | Low | C4 |
| 16 | **Ushahidi** | https://www.ushahidi.com | Generic crowdsourced report mapping. Some recent versions add AI tagging. | Partial (low) | C1, C3 |
| 17 | **KoBoToolbox / ODK** | https://www.kobotoolbox.org | Standard humanitarian form collection (IFRC, PRC/510 and WFP use it). RDANA-like templates can be built in it. Manual entry. | Partial | C1 (structured), C5 (form) |
| 18 | **510 / Netherlands Red Cross typhoon impact model** | https://centre.humdata.org/peer-review-of-510s-typhoon-model-and-its-use-in-the-philippines/ | ML that predicts the **% of houses totally damaged per municipality** before landfall to trigger anticipatory action. A forecast, not an assessment, and uses no citizen data. | Low | C4 (prior-based estimate useful as a sanity check) |
| 19 | **UP NOAH / DOST HazardHunterPH / GeoRiskPH** | https://noah.up.edu.ph ; https://hazardhunter.georisk.gov.ph | Hazard maps and point hazard-assessment reports. NOAH received P1B in Aug 2026 for AI flood forecasting. Pre-disaster, with no damage-report intake. | Low | C4 (hazard layers) |
| 20 | **IFRC GO field reports / Flash updates** | https://go-wiki.ifrc.org/en/user_guide/Field_report_form | Structured digital sitrep forms for National Societies. Manual entry. | Low | C5 (analogous international form) |
| 21 | **DEEP** (Data Entry and Exploration Platform) | https://solve.mit.edu/solutions/40886 | NLP-assisted tagging of humanitarian **documents** for secondary data review. | Low | C2 (text only, secondary data) |
| 22 | **OCHA x Dataminr AI pilot / ReliefWeb** | https://reliefweb.int/blogpost/piloting-ai-humanitarian-information-reflections-our-collaboration-dataminr | AI pilot to speed up OCHA humanitarian information products from open-source signals. | Low | output-side AI sitrep |
| 23 | **AHA Centre DMRS / weekly updates** | https://ahacentre.org/what-we-do/ | ASEAN regional monitoring and situation updates built from national data. | Low | C4 / sitrep |
| 24 | **DICT x Google Cloud Gemini Enterprise (eGovPH)** | https://www.googlecloudpresscorner.com/2026-06-21-DICT-and-Google-Cloud-Partner-on-Multi-Year-AI-and-Cybersecurity-Initiatives-to-Deliver-Next-Generation-Citizen-Services | June 2026 deal: Gemini agents for government, including local-language Q&A on disaster-assistance guidelines. 50k+ public servants get Gemini Enterprise. **No damage-reporting or RDANA agent is announced.** | Low (but a strong adoption tailwind) | n/a |
| 25 | One Concern, Gramener, Planet / Maxar | various | Commercial resilience modelling and satellite damage analytics. | Low | C4 |

## 2. Hackathon projects and GitHub repos

| # | Name | URL | What it does | Overlap | Components |
|---|------|-----|--------------|---------|-----------|
| 26 | **Project Agap** | https://github.com/Polqt/project-agap | Barangay-first PH app with resident "I am safe / need help" pings, evacuation-center **needs reports** (food packs, water, medicine, evacuees) and an **LLM (Claude) bilingual English/Filipino incident sitrep**, plus an LGU export card. Inputs are structured forms, not photos or voice. | **Partial (closest hackathon-style project)** | C5-lite (LLM sitrep), C1 (structured) |
| 27 | **Project ARK** (AMD Developer Hackathon, May 2026, lablab) | https://lablab.ai/submissions/c578ldsl3fpmm0cht7qn47ce | Turns satellite imagery into PH typhoon damage reports in English and Tagalog. Satellite only, with no official forms. | Partial | C4 + generic report |
| 28 | **READYLINK** (Brgy. Alangilan, Batangas) | https://github.com/zner07/readylink_aberya | Frontend prototype for citizen risk reports with photos and AI classification (currently mocked). | Low | C1 |
| 29 | **HERMES-GeoAI** | https://github.com/Nomik21/HERMES-GeoAI | Multi-agent pipeline (OpenAI) that turns street-view and satellite imagery into evidence-grounded damage reports. Not tied to the Philippines and produces no forms. | Partial | C2 (photos), C4, report |
| 30 | **AFTERMAP AI Agent** | https://github.com/sultankennesaw-Civil/AFTERMAP_AI-AGENT_Demo | UAV damage segmentation plus Gemini reasoning summaries. | Partial (low) | C2/C4 |
| 31 | **HazardMind AI** (lablab Band of Agents) | https://lablab.ai/submissions/ybcm3g24bebz07x7ajcs2d1y | Multi-agent Sentinel-1/2 analysis that outputs an executive PDF. No citizen photos. | Low | C4 |
| 32 | **Pytho AI** (Gemini API Developer Competition) | https://ai.google.dev/competition/projects/pytho-ai | Gemini multimodal analysis of drone, satellite and social data producing rescue plans and damage assessments (US wildfire and hurricane focus). | Partial | C2, C4 |
| 33 | **RePair** (Devpost) | https://devpost.com/software/repair-5ebgtw | Gemini analysis of household-damage photos with voice guidance, aimed at homeowners. | Low | C2 (photo to damage severity) |
| 34 | **Aileen 4 Disaster Relief** (Gemma 4 Good, May 2026, Australia) | https://ndurner.substack.com/p/aileen-4-disaster-relief | Field notes and photos turned into reviewed public social updates, on edge devices. | Low | C1/C2 (field evidence to text) |
| 35 | Ad1e/RDANA, diazsamantha8/rdanaf, haidemabido01/project_rdana; several `dromic` repos (e.g. hello9titree/mdrrmo-evac-monitoring-system "based on DROMIC form") | GitHub | Student or LGU digital RDANA / DROMIC form apps (2025-2026) with empty or boilerplate READMEs. No AI. | Low | C5 (manual digital form) |
| 36 | DOST CALABARZON Hack4Progress (Lucena, Sept 8-10, 2026) | https://hack4aprogress.dostcalabarzon.ph/ | Hackathon theme: AI to help LGUs assess risk and **prioritize recovery from damage assessments**. Winners not found. **The same idea may be submitted here or at similar events.** | Unknown | watch-list |
| 37 | Dev-shop apps: altcoder/dromic-covid19-sitreps | https://github.com/altcoder/dromic-covid19-sitreps | Machine-readable scrape of DROMIC sitreps. Useful as a template and schema source. | None | data source |

## 3. Academic work

| # | Paper | URL | Relevance |
|---|-------|-----|-----------|
| 38 | Automated Wildfire Damage Assessment from Multi-view Ground-level Imagery via VLMs (2025) | https://arxiv.org/abs/2509.01895 | Zero-shot VLM damage classification from ground photos. Supports the feasibility of C2. |
| 39 | DisasTeller: multi-LVLM agents for post-disaster assessment, alerts, resource allocation (Nature Comms / arXiv 2024-25) | https://www.preventionweb.net/publication/documents-and-publications/integration-large-vision-language-models-efficient-post | **Closest academic analogue**: agentic VLM pipeline from images to damage grades and plans. Japan (Wajima), GPT-4o, no government forms. |
| 40 | RAPID / RAPIDMap: multi-agent pipelines fusing satellite and street-view imagery (arXiv 2606.21819, 2609.00046, 2026) | https://arxiv.org/abs/2609.00046 | Ground and satellite fusion (C2+C4) producing map-ready intelligence. Not citizen reports, not forms. |
| 41 | A Large-Language-Model Framework for Automated Humanitarian Situation Reporting (ISI/UNICEF, Dec 2025) | https://arxiv.org/abs/2512.19475 | LLM sitreps from **documents** (ReliefWeb) with citations. Covers the output side only. |
| 42 | SmartBook: AI-Assisted Situation Report Generation (2023) | https://arxiv.org/abs/2303.14337 | News to sitrep. Output side only. |
| 43 | From Imagery to Insight: Multimodal LLMs for Rapid Disaster Impact Assessment (GMU JSSR) | https://journals.gmu.edu/jssr/article/view/5205 | Gemini-API damage assessments from imagery. |
| 44 | CrisisMMD + MLLM severity scoring (2025) | https://crisisnlp.qcri.org/crisismmd | Benchmark for social-media image damage severity. Usable for evaluation. |
| 45 | Filipino disaster-tweet work: FILIET; clustering tweets for needs assessment (arXiv 2108.06853); UP text-mining prioritization | https://arxiv.org/abs/2108.06853 | Pre-LLM NLP for Filipino **text** needs extraction. Prior art for C2 in Tagalog, but text only. |
| 46 | DenseNet201 ground-level damage classification, Quezon Province (MSEUF 2022) | https://mseuf.edu.ph/research/read/1826 | PH ground-photo damage classification (partially or totally damaged, 90%) deployed as a mobile app. These are the **same classes RDANA uses**, but it is a CNN without extraction, dedup or forms. |
| 47 | UAV 3D building damage, Tacloban/Haiyan (UP Diliman, ISPRS 2026) | https://isprs-annals.copernicus.org/articles/X-5-W4-2025/331/2026/ | PH-specific damage markers. Covers C4 only. |

---

## Conclusion

### Has it been done?
**Not end to end.** Every component exists somewhere, but no product, hackathon entry or paper found does the full chain: **multilingual (Tagalog/Bisaya) photo and voice reports, then a VLM/LLM that extracts damage and needs counts, then geotag, dedup and satellite or Open Buildings fusion, then auto-filled OCD RDANA and DSWD DROMIC / NDRRMC sitrep forms.**

### Closest prior art
1. **Digital RDANA (Mobile RDANA App, DROMIC IS v2 / Online Rapid Data Collector, DepEd RADaR, student RDANA/DROMIC repos).** These already digitize the *official forms*, but trained staff fill them in by hand. The proposed idea's value is to **feed** these systems, not replace them.
2. **WFP PRISM.** It is a hazard-exposure dashboard with KoBo point layers and PDF exposure reports. It is **not deployed in the Philippines** (no PH config in the repo), has no AI extraction and does not output RDANA or DROMIC. Overlap is limited to the "merge with geospatial layers" piece. Do not confuse it with PhilRice PRISM (rice-crop damage).
3. **LyfSaver x Quezon City (Aug 2026).** Citizen reports with AI-assisted verification, connected to the LGU DRRMO. This is the closest *live* deployment on intake and verification, but there is no public evidence of structured damage or needs extraction or official-form output.
4. **Project Agap (GitHub).** Barangay needs forms plus an LLM bilingual sitrep. It has the closest *output* side but uses structured form inputs, with no photo or voice extraction, no fusion, and no exact RDANA or DROMIC template.
5. **Google SKAI / Open Buildings / HASTE / RAPIDMap / DisasTeller.** These already handle the satellite side and the VLM damage reasoning, but none has a ground-report intake that produces official PH forms.
6. **MapaKalamidad.ph / Agos.** Since 2013-2020 they have taken in geolocated citizen photos and texts by chatbot, but they map flood and incidents and do not produce damage or needs tallies or forms.

### What is genuinely novel
- **Turning unstructured multilingual ground evidence into official-form schemas.** Gemini extracts RDANA fields (houses partially or totally damaged, dead, injured, missing, displaced, lifelines status, critical needs) and DROMIC fields (affected and displaced families and persons, inside or outside ECs, damaged houses partial or total) from **voice notes in Tagalog and Bisaya** and from photos. No prior system was found that does this.
- **Report-level deduplication and consolidation into the barangay, city/municipality, province, region hierarchy** that DROMIC and NDRRMC sitreps require, with a per-field provenance trail back to the photos and notes behind each count.
- **Ground-truth and satellite reconciliation.** Citizen photo counts of damaged houses are cross-checked against Open Buildings footprints and SKAI or 510-model priors, and the system flags where the two disagree for RDANA team follow-up.
- **Compliance framing.** The output is the actual RA 10121 / NDRP deliverable (an RDANA form draft, a DROMIC report, an NDRRMC sitrep annex) for a human LDRRMO officer to approve. It is not "yet another dashboard."

### How to differentiate the pitch
- Lead with "**From 2,000 messy Messenger voice notes to a signed RDANA form in 15 minutes**." Show a side-by-side of the official OCD RDANA form and DROMIC template being filled, with each field citing its source evidence.
- Position the tool as a **feeder or co-pilot for existing official systems** (DROMIC IS v2, Mobile RDANA, PhilAWARE), not as a competitor to them. LyfSaver, MapaKalamidad and PRISM sit upstream (intake) or alongside (geospatial). The novel piece is the conversion from ground evidence into the official form.
- Emphasize **Bisaya and Tagalog voice-first intake** that works over low-bandwidth Messenger or SMS, plus offline queueing. Other tools offer text or English only, or are satellite-only.
- Make **confidence, dedup and human-in-the-loop sign-off** visible to address trust (LyfSaver's own framing is "trust is not something AI can automate").
- Ride the June 2026 DICT x Google Cloud Gemini Enterprise rollout to show a clear government adoption path.
- Risks to mention: the DROMIC guidelines were updated (MC 12 s. 2026), so use current templates; there is privacy exposure under the Data Privacy Act; and similar entries may surface at the DOST Hack4Progress (Sept 2026) or Gemma 4 Good events.

## Verdict: **PARTIALLY DONE**
The building blocks (digital RDANA and DROMIC forms, citizen photo crowdsourcing, satellite damage AI, LLM sitrep drafting) all exist separately. The **end-to-end multilingual photo and voice to official RDANA/DROMIC auto-fill with dedup and satellite fusion** was not found anywhere and is the defensible novel core.
