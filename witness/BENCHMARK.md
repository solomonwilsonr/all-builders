# Witness benchmark v0 (built 2026-10-11)

Ground truth for testing Witness: viral disaster videos with a published fact-check. **25 test videos (26 claims) + 2 radar references.** Every fact-check page was opened and returns HTTP 200 (Euronews returns 406 to scripts only). All 12 earlier-source YouTube videos listed below were checked live, with upload dates matching the fact-checks.

**Verdicts Witness must produce:** consistent · possible inconsistency · inconclusive. Witness is not an AI-video detector: for AI-generated clips the correct physics/archive verdict is usually *inconclusive* unless the archive finds the AI-labelled original.

## Gate test: Cloud Vision Web Detection (5 cases)
**Pass = earlier source found for ≥3 of 5.** Use keyframes from the *viral* copy (archive links) where possible, not from the earlier source itself; otherwise the test is circular.

| # | Case | Why picked | Expected earliest source |
|---|---|---|---|
| 1 | CY-05 Fengal → Jeddah | Foreign origin, mainstream re-uploads | YT Short pdE-c4qJFas (2024-09-02) |
| 2 | W02 Wayanad → Meizhou, China | On-screen date, 3 live YT copies | YT -UBuGHH_pIo (2024-06-25) |
| 3 | LS-03 Dharali → Nalagarh | Hard: neighbouring state, similar terrain | YT gG8y--iMl04 (2022-07-29) |
| 4 | W06 Delhi → Bengaluru | Metro signage for OCR cross-check | YT RmGXuHqZt2c (2022-09-05) |
| 5 | W09 Guwahati → Sainj Valley | Two fact-checkers differ in confidence | YT BmLiocx3Q3o (2023-07-18) |

## A. Misattributed flood / rain videos (10)
| id | Viral claim | Actual origin | Debunked by | Fact-check | Earlier source | Expected Witness verdict |
|---|---|---|---|---|---|---|
| W01 | House collapses into river, Chennai, Dec 2023 | Mundakayam, Kerala, 17 Oct 2021 | Earlier upload | [Newschecker](https://newschecker.in/fact-check/old-video-of-house-collapsing-into-a-river-in-kerala-falsely-linked-to-2023-chennai-floods/) | [TNM](https://www.thenewsminute.com/kerala/video-captures-two-storey-house-kerala-completely-collapsing-gushing-river-156607), [NDTV](https://www.ndtv.com/kerala-news/video-house-swept-away-as-kerala-witnesses-heavy-rain-2578676) | Possible inconsistency (earlier upload) |
| W02 | House swallowed by flood, Wayanad, 30 Jul 2024 | Meizhou, Guangdong, China, 16 Jun 2024 | Earlier upload + on-screen date | [Quint](https://thequint.com/news/webqoof/china-video-of-flooding-shared-as-wayanad-landslide-kerala-fact-check) | [YT](https://www.youtube.com/watch?v=-UBuGHH_pIo) ✅ 2024-06-25 | Possible inconsistency (earlier upload + OCR date) |
| W03 | Crocodile on flooded road, Delhi, Jul 2023 | Vadodara, Aug 2019 | Earlier upload | [Newschecker](https://www.newschecker.in/fact-check/old-video-of-crocodile-on-flooded-road-from-vadodara-shared-as-delhi) | [YT](https://www.youtube.com/watch?v=ZOX-7NbFx8Y) ✅ 2019-08-03 | Possible inconsistency |
| W04 | SUV in waterlogging, Delhi, Jul 2023 | Rohtak, Haryana, 30 Jun 2022 | Earlier upload + shop sign on Street View | [BOOM](https://www.boomlive.in/fact-check/viral-video-delhi-waterlogging-old-video-haryana-social-media-22478) | [X](https://twitter.com/mohit_upsc/status/1542509951838408707) | Possible inconsistency |
| W05 | Cars swept away, Punjab, Jul 2023 | Parwanoo, Himachal, 10 Jul 2023 | Earlier upload (same week) | [Newschecker](https://newschecker.in/fact-check/video-of-water-sweeping-away-vehicles-is-from-himachal-pradesh) | [YT](https://www.youtube.com/watch?v=KHiEquR_Yf0) ✅ 2023-07-10 | **Hard:** date consistent, place contradicted |
| W06 | Flooded street, Delhi, Jul 2024 | Bengaluru, Sep 2022 | Earlier upload + metro signage | [Quint](https://thequint.com/news/webqoof/old-bengaluru-video-showing-floods-shared-as-one-from-delhi-fact-check) | [YT](https://www.youtube.com/watch?v=RmGXuHqZt2c) ✅ 2022-09-05 | Possible inconsistency |
| W07 | Crocodiles in floodwater, Vadodara, Aug 2024 | Kimberley, W. Australia, 7 Aug 2024 | Earlier upload (FB) | [Quint](https://www.thequint.com/news/webqoof/crocodiles-spotted-swimming-flooded-areas-vadodara-gujarat-viral-video-fact-check) | FB/IG, no direct URL | Possible inconsistency (not really flood footage) |
| W08 | Flooded runway, Mumbai airport, Aug 2025 | Chennai airport, Dec 2023 (Michaung) | Earlier upload + on-screen GPS | [BOOM](https://www.boomlive.in/fact-check/viral-video-mumbai-airport-flooded-maharashtra-waterlogging-claim-fact-check-29288) | PTI via TOI, no direct URL | Possible inconsistency (OCR GPS ≠ Mumbai) |
| W09 | Shops swept away, Guwahati, Jun 2025 | Sainj Valley, Kullu, 9 Jul 2023 | Earlier upload | [Quint](https://www.thequint.com/news/webqoof/clip-of-floods-in-hp-falsely-viral-as-one-from-assam-fact-check), [Newschecker](https://newschecker.in/fact-check/old-unrelated-videos-falsely-linked-to-assam-floods) | [YT](https://www.youtube.com/watch?v=BmLiocx3Q3o) ✅ 2023-07-18 | Date contradicted; place *likely* (Newschecker couldn't confirm it; Quint says Sainj) |
| W10 | Building collapses into flood, Assam, Jul 2026 | Beerwah, Budgam, Kashmir, 21 Jul 2026 | News match (same week) | [Quint](https://thequint.com/news/webqoof/video-from-beerwah-budgam-kashmir-falsely-shared-as-assam-floods-fact-check) | [TOI](https://timesofindia.indiatimes.com/city/srinagar/j-k-floods-terrifying-video-shows-shopping-complex-swallowed-by-raging-floodwaters-near-kashmir/articleshow/132540535.cms) | **Hard:** date consistent, place contradicted |

## B. Misattributed cyclone / landslide / cloudburst videos (8)
| id | Viral claim | Actual origin | Debunked by | Fact-check | Earlier source | Expected Witness verdict |
|---|---|---|---|---|---|---|
| CY-01 | Slab crashes onto cars, Nariman Point, Mumbai, Tauktae, May 2021 | Medina, Saudi Arabia, 30 Jul 2020 | Earlier upload + CCTV timestamp | [BOOM](https://www.boomlive.in/fact-check/saudi-arabia-clip-shared-as-cyclone-tauktae-destruction-at-mumbais-trident-hotel-13166) | Al Jazeera Arabic / Albawaba (named, no URL) | Possible inconsistency (OCR date) |
| CY-02 | Tornado in West Bengal before Yaas, May 2021 | 2016 YouTube upload, place unconfirmed | Earlier upload | [Quint](https://www.thequint.com/amp/story/news/webqoof/no-video-does-not-show-tornado-that-hit-bengal-ahead-of-cyclone-yaas) | [YT](https://www.youtube.com/watch?v=y9ZVJ4eP_Co) ✅ 2016-08-06 | Date contradicted; **place inconclusive** |
| CY-03 | Waves hit jetty, Gujarat, Biparjoy, Jun 2023 | Minicoy, Lakshadweep, Aug 2017 | Earlier upload + Maps landmark | [Quint](https://www.thequint.com/amp/story/news/webqoof/tides-hitting-bridge-cyclone-biparjoy-guarat-fact-check) | [perma.cc](https://perma.cc/5XT4-UAYE) | Possible inconsistency; **same clip reused for Tauktae 2021** (tests "seen before" memory) |
| CY-04 | Waves hit houses, Odisha, Dana, Oct 2024 | Yaas footage, May 2021 | Earlier upload | [Quint](https://www.thequint.com/amp/story/news/webqoof/cyclone-dana-impact-odisha-west-bengal-viral-video-fact-check) | [FB](https://perma.cc/LM3S-UUS8), [OTV](https://ghostarchive.org/varchive/TR79k9CyWhw) | Possible inconsistency (same region, older cyclone) |
| CY-05 | Flooded Marina Beach road, Chennai, Fengal, Nov 2024 | Jeddah, Saudi Arabia, 2 Sep 2024 | Earlier upload + Saudi Press Agency rain report | [Quint](https://www.thequint.com/amp/story/news/webqoof/video-of-flooded-roads-saudi-arabia-viral-as-one-from-chennai-cyclone-fengal) | [YT Short](https://www.youtube.com/shorts/pdE-c4qJFas) ✅ 2024-09-02, [Newsflare](https://www.newsflare.com/video/675991/saudi-arabia-heavy-rain-has-flooded-the-streets-of-jeddah) | Possible inconsistency; **radar can check Marina that week** |
| LS-01 | Cloudburst, McLeodganj, 12 Jul 2021 | Atami mudslide, Japan, 3 Jul 2021 | Earlier upload | [Quint](https://www.thequint.com/amp/story/news/webqoof/video-of-mudslide-japan-shared-as-cloudburst-in-dharamshala-himachal-pradesh-fact-check) | ABC / HT (named, no URL) | Possible inconsistency; **reused as Sikkim 2023** ([Newschecker Nepal](https://nepal.newschecker.co/en/english/fact-check-old-clip-showing-massive-landslide-hitting-japan-falsely-shared-as-recent-video-from-sikkim)) |
| LS-02 | Building collapse, Kullu, Jul 2023 | Sangihe, Indonesia, Jun 2016 | Earlier upload | [Quint](https://www.thequint.com/amp/story/news/webqoof/cloud-burst-building-collapsing-in-himachal-pradesh-floods-shared-as-recent-fact-check) | [perma.cc](https://perma.cc/XFR5-EJ34) | Possible inconsistency |
| LS-03 | River rescue, Dharali, Uttarkashi, 5 Aug 2025 | Nalagarh, Himachal, Jul 2022 | Earlier upload | [Newschecker](https://newschecker.in/fact-check/uttarkashi-cloudburst-old-video-of-men-being-rescued-from-flooded-river-in-himachal-falsely-shared-as-dharali) | [YT](https://www.youtube.com/watch?v=gG8y--iMl04) ✅ 2022-07-29 (+2 more) | Possible inconsistency (hard: similar terrain) |

## C. Hard cases: genuine, AI-generated, unresolved (7 videos, 8 claims)
| id | Type | Claim | Finding | Source | Expected Witness verdict |
|---|---|---|---|---|---|
| A1 | Genuine (liar's dividend) | Etna eruption videos are "AI" (Italy, Jun 2025) | Real; AP filmed the same scene | [Euronews](https://www.euronews.com/my-europe/2025/06/16/fact-check-tourist-videos-of-mount-etna-eruption-are-real-not-ai-generated) | Consistent (not India; only true liar's-dividend case found) |
| A2a | Genuine | Flash flood, Possa, Arunachal, 24 Jun 2026 | Real; PTI video same day | [CyberPeace](https://cyberpeace.org/resources/blogs/factcheck-video-from-arunachal-pradesh-floods-falsely-shared-as-nepals-rasuwa-floods) | **Consistent** (positive control) |
| A2b | Misattributed | Same clip as "Nepal Rasuwa flood" | Wrong country | same | Possible inconsistency |
| A3 | Genuine, wrong label | "Nepal/Tibet flood, 26 Aug 2026" | Niti Valley, Chamoli, 10 Aug 2026 (Chamoli Police via ANI) | [BOOM](https://www.boomlive.in/fact-check/viral-nepal-flash-flood-videos-claim-fact-check-old-unrelated-videos-32124) | Possible inconsistency for Nepal; consistent for Chamoli |
| B1 | AI-generated | Drone shot of flooded Surat skyscrapers, Jul 2026 | AI (Hive 99.9%); **real flooding did occur in Surat** | [CyberPeace](https://cyberpeace.org/resources/blogs/factcheck-ai-generated-video-falsely-shared-as-drone-footage-of-flooded-surat-gujarat) | **Inconclusive.** Radar confirming a flood must NOT turn into "consistent" |
| B2 | AI-generated | Hill-road flood, Assam *and* Uttarakhand, Jun 2025 | AI; Brazilian channel uploaded 28 May 2025, labelled AI | [Fact Crescendo](https://english.factcrescendo.com/2025/06/12/ai-generated-video-goes-viral-as-visuals-of-flood-in-assam-and-uttarakhand/) | Possible inconsistency (archive finds AI-labelled original) |
| B3 | AI-generated | Rooftops submerged, Assam, Jul 2026 | AI (detectors 77–99%) | [CyberPeace](https://cyberpeace.org/resources/blogs/factcheck-ai-generated-video-falsely-shared-as-real-footage-of-assam-floods), [Quint](https://www.thequint.com/news/webqoof/ai-generated-video-of-assam-flood-shared-as-real-false-claim-fact-check) | Inconclusive |
| C2 | Unresolved origin | Elephant rescue, Nepal floods, 26 Aug 2026 | Posted 9 Aug 2026 as "Assam"; origin unverified | [Lead Stories via Yahoo](https://www.yahoo.com/news/world/articles/fact-check-video-elephant-rescuing-023914859.html) | Nepal date contradicted; true origin **inconclusive** |

## D. Radar ground truth (for Sentinel-1 checks)
| id | Event | Data | Source |
|---|---|---|---|
| D1 | Assam floods, Jun 2023 | NRSC Sentinel-1A SAR map, 23 Jun 2023; 279,926 ha across 20 districts | [ASDMA report](https://asdma.assam.gov.in/sites/default/files/swf_utility_folder/departments/asdma_revenue_uneecopscloud_com_oid_70/this_comm/as_2023_23_06_1800_report.pdf) |
| D2 | Cyclone Montha, Andhra, Oct–Nov 2025 | NRSC Sentinel-1A SAR, 2 Nov 2025; 2,691 ha across 6 districts | [APSAC report](https://apsac.ap.gov.in/wp-content/uploads/2025/11/02-11-2025/NRSC/AP_2025_02_11_0600_Report.pdf) |

## What this benchmark already tells us
- **18 of 18 misattributed cases were solved by finding an earlier upload or matching news coverage** (sometimes plus a landmark or on-screen text). None was solved by shadows or weather alone. Physics should be supporting evidence, not the core.
- **On-screen text matters:** W02 (date), W08 (GPS), CY-01 (CCTV timestamp), W06 (metro sign). Gemini OCR is a cheap, high-value check.
- **3 hard cases where date checks fail** (W05, W10, A2b): same-week footage from a different place. Only place evidence catches them.
- **Reused clips** (CY-03, LS-01): the "seen this before" memory has real cases to demonstrate.
- **AI-generated clips are a growing share in 2025–26** (B1–B3). Witness should say "inconclusive", not pretend to detect AI.
- **Gap:** no Indian fact-check found that confirms *real* flood footage after it was dismissed as fake. The "protect real footage" pitch beat has to rely on A2a/A3 (real footage, wrong label).

## Caveats
- Some earlier sources are named in the fact-check but have no direct URL (CY-01, LS-01, W07, W08). X/Instagram links may be dead.
- 2026 cases could only be checked against the fact-check page itself.
- Video length not recorded; viral copies need to be pulled from archive links before testing.
