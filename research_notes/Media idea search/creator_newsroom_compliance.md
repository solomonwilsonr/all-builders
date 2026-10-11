# Media theme: Compliance / Rights / Ops pain in JAPAC (researched 2026-10-10)

Context: Google Cloud AI Builder Cup 2026, Media theme. Avoid: audio description (Gapline), ad localization (OmniLocate), cricket analytics (SEEN), curriculum, dubbing, clips, avatars, summarizers, thumbnails.

---

## 1. Creator / influencer ad-disclosure + claims compliance

### Regulation and evidence (verified numbers)
- **India ASCI**: FY24-25, 9,599 complaints, 7,199 ads scrutinised, 98% needed modification. Influencer violations were **14% of ads processed**. **1,015 influencer ads investigated, 98% needed modification.** 318 involved offshore betting. 121 were LinkedIn non-disclosures. Healthcare: 370 ads investigated, 56% misleading. 233 health ads referred to the AYUSH Ministry.
  - https://www.exchange4media.com/influence-zone-news/14-of-flagged-ads-in-fy25-linked-to-influencer-violations-asci-143887.html
  - https://thesouthfirst.com/news/from-cancer-cures-to-sexual-weakness-fixes-asci-flags-233-misleading-health-ads-to-ayush-ministry
- **ASCI dipstick study**: 76% of Forbes India Top-100 digital stars did not disclose paid collabs (2024), up from 69%. https://campaignindia.in/article/69-of-indias-top-influencers-violate-disclosure-guidelines-asci/500642
- **ASCI April 28 2025 update**: "technical" health/finance claims need qualified credentials, while generic promotion does not. Stock/investment influencers must be SEBI-registered and show their registration number, name and qualifications. Other finance claims need IRDAI/CA/CS. Health claims need a medical, nursing, nutrition, physio or psychology qualification. https://conventuslaw.com/report/india-asci-updates-influencer-guidelines-for-health-and-finance-sectors-strikes-balance-between-expertise-and-expression/
- **SEBI**: early-2025 rules bar SEBI-regulated entities (brokers, AMCs, advisers) from associating with unregistered finfluencers. SEBI says it removed **70,000+ misleading posts/accounts since Oct 2024** and acted on about 15,000 unregistered finfluencers. Avadhut Sathe order (Dec 2025): Rs 546 cr impounded. Baap of Chart: Rs 17.2 cr. https://www.business-standard.com/amp/finance/personal-finance/no-more-misleading-stock-tips-sebi-cracks-down-on-fraudulent-influencers-125082700154_1.html
- **CCPA endorsement guidelines (Jan 2023)**: fines up to Rs 10 lakh, or Rs 50 lakh for repeat violations. Endorsement bans of 1 to 3 years. Disclosure must be "clear, prominent and extremely hard to miss". https://www.exchange4media.com/digital-news/influencers-can-be-fined-upto-rs-50-lakh-for-misleading-consumers-as-per-new-guidelines-124905.html
- **India IT Rules amendment 2026** (G.S.R. 120(E), notified 10 Feb 2026, in force 20 Feb 2026): synthetically generated content must carry a prominent label plus provenance metadata. Flagged unlawful content must come down within 3 hours. This is a new pre-publish check for AI-edited creator videos. https://blog.ipleaders.in/it-rules-2026/
- **Vietnam**: amended Advertising Law No. 75/2025/QH15 (in force 1 Jan 2026) defines "advertising conveyors" (KOLs/KOCs). They must verify the advertiser and the product information, and disclose ads before and during promotion. The practical norm is "Quảng cáo"/"Ad" spoken and shown at the start. **Decree 87/2026/ND-CP (25 Mar 2026), Art. 51**: KOL fines of about US$1,500 to 3,800 plus takedown and public apology. Kera-candy case: Quang Linh Vlogs, Hang Du Muc and Miss Thuy Tien each got **2 years in prison** for false advertising ("one candy = a plate of vegetables"; less than 1% vegetable powder).
  - https://www.dfdl.com/insights/legal-and-tax-updates/vietnam-navigating-the-amended-advertising-law-insights-for-businesses/
  - https://tuoitrenews.vn/news/society/20250405/popular-vietnamese-influencers-arrested-over-controversial-candy-promotion/85778.html
- **Australia ACCC sweep**: 81% of 118 influencers made concerning posts; non-disclosure was the most common issue. https://www.accc.gov.au/media-release/scrutiny-of-influencers-and-businesses-for-misleading-advertising-and-online-reviews-continues
- **Indonesia**: no influencer-specific law. BPOM cosmetic-claims rule (Reg. 3/2022) applies, but the regulatory gap is weak. **Philippines**: PAGCOR and the Ad Standards Council agreement on gambling promos; the CICP stance (Sep 2025); NPC influencer accountability consultation.

### Existing tools and the gap
| Tool | What it does | Gap vs our idea |
|---|---|---|
| Reech (used by ASCI) | Regulator-side AI that monitors posts for missing disclosure (captions/regex/ML) | Post-publication, regulator side; disclosure only, not claims or credentials |
| Valen Sentinel (Indie Hackers) | Paste a YouTube URL or upload video, get an FTC compliance score in 2 min; $99/mo | US FTC only |
| PostEverywhere FTC Disclosure Checker | Free caption checker | US, text only |
| Influencer.com "Advert Audit" | UK ASA disclosure checker | UK only |
| BanProof AI | Checks TikTok Shop/Amazon affiliate scripts, MP4/MP3 for medical/guarantee claims; writes appeal letters; MCP; from $14.99 | Platform-policy (TikTok Shop) focus, not ASCI/SEBI/Vietnam law. Generic phrase risk with no credential check. **Overlaps strongly on "video claims checker", so we must differentiate on jurisdiction + credential + regulated-brand workflow.** |
| Fabulate SparQ 2.0 (Sydney, 12 APAC markets) | Has a "Compliance Check" against regulatory and brand standards | Details unspecified; looks generic, not per-market |
| Kofluence (India) + ASCI partnership | Influencer platform with ASCI tie-up | Marketplace, not a video-native claims auditor |
| Red Oak Compliance | US finance marketing-review workflow (FINRA) | US only |
| Academic: arXiv 2603.04383 | YouTube affiliate disclosure classifiers (FTC) | Research, US |

- Hackathon prior art: no Devpost/lablab project found for an ASCI/SEBI/Vietnam-specific video checker. Generic "FTC checker" side-projects exist.

### Novelty verdict: PARTIALLY DONE
Generic disclosure and claims checkers exist (US/UK, plus BanProof for TikTok Shop). We found no tool combining all of the following:
- (a) India ASCI technical-claim plus credential rules
- (b) SEBI registration verification against SEBI's public registered-intermediary list
- (c) the 2026 AI-label rule
- (d) Hinglish / Vietnamese video+audio reasoning
- (e) a regulated-brand reviewer workflow

---

## 2. Copyright / Content ID false claims; music licensing reports
- Evidence: Ziiki Media (South African aggregator with a Warner India partnership) put retroactive claims on old videos of about a dozen Indian journalists (Ravish Kumar, Abhisar Sharma), mostly for public-domain press-conference clips. Roha Entertainment (Telangana) filed false claims through Content ID partner access. T-Series and Zee Music send mass takedowns on remixes. https://enewsroom.in/youtube-bug-controversy-journalists-videos-ziiki-media
- Existing: YouTube Studio's own tools (Assisted Trim, Erase Song, streamlined dispute flow) and freelance counter-notice services. No dedicated AI "evidence-pack + dispute drafter" product was found, but YouTube keeps absorbing this.
- Hard limit: we cannot access Content ID reference audio. Gemini can only check whether the claimed timestamp contains music or speech, whether it is public-domain footage (press conference / Parliament feed), and the license history. Demo data is fine (public press-conference clips).
- **JASRAC/IPRS usage reports**: Soundmouse (Orfium), BMAT and the JASRAC/NexTone streamer report flow already automate cue sheets. **ALREADY EXISTS.**
- Novelty verdict, Content ID dispute assistant: **PARTIALLY DONE** (manual services plus platform tools). The pain is real but episodic, there is no clean before/after metric, and it is legally sensitive (counter-notices are sworn statements).

## 3. Broadcast/OTT classification and compliance
- India: OTT self-classification under IT Rules 2021 (U, U/A 7+, 13+, 16+, A) plus content descriptors. MIB blocked 25 OTT apps (Ullu, ALTT…) on 23 Jul 2025 after 6 months of warnings. CBFC averages 18 working days for features; tatkal was scrapped, so standard is 30 to 40 days (assured 20 to 25).
- Korea: OTT self-rating since Apr 2023, and ratings drifted lenient: G rose from 21.2% to 40.8% and R fell from 24.5% to 14.2%. KMRB named TVING and Disney+ outstanding self-raters (Mar 2026).
- Singapore IMDA co-classification: trained in-house "content assessors" can rate up to PG13 (about 2,300 titles co-classified).
- Indonesia KPI: P3SPS warnings, e.g. "Ipar Adalah Maut The Series" (MDTV, Nov 2025). KPID Central Java logged 1,859 potential violations in 2025.
- **Existing tools are heavy here**:
  - Spherex: 1,000+ attributes, age ratings and compliance for 200 territories incl. India; clients include YouTube, Lionsgate, Paramount
  - **Prime Focus Technologies CLEAR AI**: India-based; S&P/compliance edits with "an in-built framework of parameters for all regulatory bodies"; claims 80% less manual review time; shown at Broadcast Asia 2025
  - BBFC CLEARD (with AWS)
  - Vionlabs
  - Qwerty AI (script-based age rating, 80% accuracy)
- **Verdict: ALREADY EXISTS.** Avoid. Demo footage (sex/violence) is also awkward for judges.

## 4. Regional newsroom ops (court/legislature to vernacular briefs)
- SC India uses TERES for live transcription; the CJI has pledged regional-language transcripts. SC livestreams on YouTube. Sarvam/Bhashini provide the language infrastructure.
- No dedicated "court hearing to vernacular news brief" product was found, but it is a summarizer/translator shape (saturated category) with no compliance hook and weak before/after evidence. **Verdict: PARTIALLY DONE / weak fit.**

---

## Ranked idea framings

### #1 FinClear / "Collab Clearance Desk": SEBI + ASCI pre-publish clearance for regulated brands' creator videos (India first, Vietnam second)
- **Named user**: Priya, marketing-compliance officer at a mid-size Indian mutual fund AMC or stockbroker (also insurer, nutraceutical or D2C health brand). Since SEBI's 2025 rule, *her firm* is liable if it associates with an unregistered finfluencer or a creator making investment-advice claims. She must vet every creator draft video before it goes live.
- **Workflow**:
  1. Upload the draft reel/YouTube cut (Hinglish).
  2. Gemini 2.5/3 reads video, audio and on-screen text. It flags: missing or late disclosure (ASCI: in the first few seconds, not buried in hashtags); technical investment or health claims; guaranteed-returns language; missing disclaimers (the "Mutual fund investments are subject to market risks…" line); unlabeled AI-synthetic segments (IT Rules 2026).
  3. Credential check: the creator's claimed SEBI RIA/RA number is verified against SEBI's public registered-intermediary list (function calling / grounding).
  4. Output: a timestamped violation list with clause citations (ASCI guideline / SEBI circular / CCPA), suggested rewrite lines, and an approve / return-to-creator decision.
  5. The human approves, and an audit-trail PDF is stored (Firestore).
- **Sponsor-tech depth**:
  - Gemini native video understanding with timestamps
  - Structured output per clause
  - RAG over the actual ASCI/SEBI/CCPA PDFs (Vertex AI Search or File Search)
  - Function calling to a SEBI-registry lookup
  - Optional Gemma on-device pre-check for creators
  - Cloud Run + Firebase
- **Before/after metric**: manual legal review of one creator video is assumed at 30 to 60 min and 1 to 3 days of back-and-forth (assumption; validate with 1 to 2 agency or AMC interviews). Target: under 3 minutes for a first-pass report, at 90%+ recall on a seeded test set of ~30 clips. Hook stats: 98% of 1,015 influencer ads ASCI examined needed modification; SEBI removed 70,000+ posts; fines up to Rs 50 lakh.
- **Demo data**: record or script 10 to 20 synthetic Hinglish reels (compliant vs. violating pairs). Public SEBI/ASCI documents. SEBI registry is publicly searchable.
- **8-day buildability**: high. Single upload, then a report UI. The rules corpus is small.
- **Novelty**: **PARTIALLY DONE**. Generic checkers (Valen Sentinel/FTC, BanProof/TikTok Shop, Influencer.com/ASA, SparQ) exist. The specific *regulated-brand + SEBI credential verification + ASCI technical-claim + AI-label + Indian-language video* combination was not found in products or hackathons. Pitch the differentiation explicitly against BanProof.
- **Vietnam extension (slide or stretch)**: Law 75/2025 plus Decree 87/2026 check whether "Quảng cáo" is spoken and shown at the start, and whether claims are verified. The Kera candy case (2-year jail terms) is a strong story.

### #2 Claim-Shield: evidence pack + dispute drafter for wrongly claimed news/creator videos
- Named user: an independent Hindi news YouTuber (Ziiki-style retroactive claims on press-conference clips).
- Gemini segments the claimed timestamp: speech vs. music, source (press conference, Lok Sabha TV feed, own footage). It assembles evidence (upload date, original source link, public-domain or fair-dealing basis under Indian Copyright Act s.52) and drafts the dispute. A human signs.
- Metric: time to file a dispute; share of claims that are clearly misidentifications.
- **Novelty: PARTIALLY DONE** (YouTube tools plus manual services). Weaker: episodic pain, legal-liability risk, no access to the reference audio.

### #3 (not recommended) OTT/regional-film self-classification drafter
- Gemini watches an episode, then drafts the U/A 7+/13+/16+ rating, content descriptors and timestamps for a human classifier, with Korea lenient-drift and MIB-ban evidence.
- **ALREADY EXISTS** (Spherex covers India; PFT CLEAR is India-native with an 80% review-time cut; BBFC CLEARD). Avoid unless the angle is very niche, e.g. small regional OTT or YouTube web-series makers.

### Also ruled out
- JASRAC/IPRS usage-report automation: ALREADY EXISTS (Soundmouse/Orfium, BMAT).
- Court/legislature vernacular briefs: summarizer shape, no compliance hook.

## Open validation items
- Get a real number for manual creator-content legal review time (agency or AMC interview, or industry survey).
- Check whether SEBI's intermediary search has a scrapeable endpoint (else use a cached CSV for the demo).
- Re-check BanProof's 2026 feature list for India/ASCI support before the pitch.
