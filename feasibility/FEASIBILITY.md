# ClearSight feasibility test (2026-10-11)

**Verdict: GO, but change the hero demo.** Data, stack and signal all check out. The pitch as written ("Gemini extracts the validity condition and lease polygon from the Kalinga EC letter") does not survive contact with the real letter.

## What we tested

| # | Test | Result |
|---|---|---|
| 1 | `earthengine-api` 1.7.47, `google-genai`, `google-adk` 2.11.0 install on Python 3.14 | ✅ PASS |
| 2 | EE datasets live: S2 SR Harmonized, S1 GRD, Dynamic World | ✅ updated through today |
| 3 | AlphaEarth `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` | ⚠️ 2017–2024 confirmed; 2025 uncertain (check AOI) |
| 4 | JRC Global Surface Water | ⚠️ ends 2021, baseline only; use DW water / MNDWI after |
| 5 | EE noncommercial access | ✅ free, immediate, 150 EECU-h/month (Community tier) |
| 6 | CAG finding real | ✅ Construction World, 6 Oct 2026 |
| 7 | Kalinga EC letter public | ✅ but **scanned 1990 image, 2 pages, no expiry date, no coordinates** |
| 8 | Mine coordinates | ✅ bbox in 2025 EC + EAC minutes (no polygon) |
| 9 | Six-monthly compliance reports public | ✅ mahanadicoal.in (mcl.gov.in is dead) |
| 10 | Cloud-free S2 over mine, dry season | ✅ 28–50 scenes/season |
| 11 | Visible change at mine 2021 → 2023 → 2025 | ✅ visually clear (see `balram_triptych.png`) |
| 12 | Naive bbox NDVI as a metric | ❌ fails: farmland dominates; scene "0% cloud" was hazy |

## Corrected hero case facts
- **"Kalinga OCP" = Balram (Balaram) OCP**, Talcher coalfield, Angul. All post-2022 documents use Balram.
- Original EC: J-11015/4/87-IA-C, **24 Oct 1990**, 8 MTPA. 1,309 ha lease.
- EC expired **23 Oct 2021** (CAG); mining continued to **Mar 2023**, ~11.5 Mt, Rs 9.57 bn. (The other mine, Kulda OCP, is a capacity-excess case: 0.23 Mt.)
- New EC 15 MTPA / 2,574 ha issued **24 Feb 2025** (EC25A001OR198573). It contains the bbox: 20°55'53.6"–20°59'7.11" N, 85°2'36.37"–85°6'21.71" E.
- Company's own HYC report Oct 2021–Mar 2022 (filed 25 May 2022) reports against the 1990 EC, **never mentions expiry**, and states it "has not exceeded the approved capacity of 8 MTY". This is the claim-vs-reality beat.
- Statuses are narrative ("being done", "maintained"), not "Complied" checkboxes → Claim Reader must handle prose.
- Bonus: the 2025 Ananta OCP EC includes a ministry-written table of **excess production beyond EC capacity** by year (1993–2010). Good second validation case.

## Required changes to FINAL_IDEA.md
1. **Validity comes from a rule, not the letter.** Pre-2006 ECs carry no expiry. Compiler extracts issue date → rule engine applies validity (30 yrs + COVID extension → 23 Oct 2021). Show the rule on screen.
2. **Lease geometry:** use the bbox from the 2025 EC / EAC minutes + a reviewer-drawn mine footprint (label evidence "moderate", as planned). Polygons are not in the letters.
3. **Metric:** clip to the mine footprint, per-pixel Cloud Score+ mask, monthly composites; subtract the +1000 reflectance offset for S2 L2A after Jan 2022 (or use EE harmonized collection, which handles it).
4. **AlphaEarth:** plan on 2021→2022→2023→2024 annual change; 2025 is a bonus.
5. **Gemini must OCR scanned PDFs** (1990 letter). Newer ECs (2014+) have a text layer.
6. **Prior art to acknowledge:** CMPDI already does satellite land-reclamation monitoring per MCL mine (reports on mahanadicoal.in); Mining Surveillance System (boundary only); ISPRS 2026 sand-mining-vs-EC paper. Our new part stays: EC conditions + self-report comparison + evidence-gap rules.
7. **"Reproduces the CAG finding without anyone pointing it to the site"** is an overclaim. Satellite shows *continued activity after a computed expiry date*; that's the honest phrasing.

## Problem stat
"13 years" = MoEFCC 2019 affidavit to NGT (likely *Sandeep Mittal v. MoEFCC*), cited via LiveLaw, 21 Aug 2026. Also: NGT 2019 found no monitoring for ~92% of Cat-B and 33% of Cat-A projects. No newer figure found.

## Extra validation cases (NGT)
- Olasingh laterite quarry, Khordha, Odisha (OA 179/2026/EZ): ~15× permitted extraction, no green belt, no compliance reports.
- Bheluguri stone mahal, Hojai, Assam (OA 66/2025/EZ): mining without EC since Jan 2024.
- Rushikulya sand mining, Ganjam, Odisha (ORSAC imagery shows out-of-lease mining).
- Tolarpasi quarry, Talcher (OA 185/2025/EZ, EC revoked 18 Jan 2025): unconfirmed.

## Cost estimate (whole hackathon)
**~$15–70 total, covered by the $300 GCP trial credit.** Gemini is the only real spend. These are estimates from public price lists, not measured; check the billing console after day 1.

| Item | Basis | Cost |
|---|---|---|
| Earth Engine | Noncommercial Community tier, 150 EECU-h/month | $0 |
| Gemini 3.6/3.7 Flash (Vertex) | $0.75 in / $3.75 out per 1M tokens (intro price to 31 Dec 2026) | ~$10–50 |
| Cloud Run | Free tier: 2M requests, 180K vCPU-s/month | $0 (~$5–15 if min-instances=1 during judging) |
| Firestore | Free tier: 50K reads, 20K writes/day, 1 GiB | $0 |
| Cloud Storage | PDFs + cached tiles, < 5 GB | < $1 |
| Data | All public | $0 |

Gemini maths: EC letter ~25–40K tokens + compliance report ~100K tokens + ~10K output ≈ **$0.15 per project run**. ~20 projects × many dev re-runs ≈ 300 runs ≈ $45. Using Pro instead of Flash multiplies this several times; keep Pro for the few explanation calls if at all.

Guardrails:
- Budget alert at $50 on day 1.
- Cache EE results and Gemini outputs for demo cases, so judge clicks cost nothing.
- Pin a 3.x model ID in an env var (Gemini 2.5 retires on Vertex Oct 16).
- Call Gemini via Vertex; the trial credit does not cover AI Studio API calls.
- EE over-quota throttles (restricted mode until the 1st), it doesn't bill.

## Still to do (needs a human)
- Register an EE Cloud project and authenticate (`earthengine authenticate`), then rerun the metric on EE with Dynamic World inside a drawn footprint.
- Pull the full CAG report from cag.gov.in for exact wording.
- Check whether the AOI has a 2025 AlphaEarth image.

## Key URLs
- CAG news: https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253
- MCL statutory docs: https://www.mahanadicoal.in/Environment/hestatuatorycp.php
- Balram HYC Oct21–Mar22: https://www.mahanadicoal.in/Environment/pdf/EC%20Half%20Yearly/HYC_Oct21-Mar22/Balram%20OCP.pdf
- 40th EAC minutes: https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/0403202379611075MoM40thEACMeetingheldon16&17February2023.pdf
- EE access: https://developers.google.com/earth-engine/guides/access
- 13-year quote: https://www.livelaw.in/articles/post-facto-environmental-clearance-546751
- Vertex AI pricing: https://cloud.google.com/vertex-ai/generative-ai/pricing
- Cloud Run pricing: https://cloud.google.com/run/pricing
- Firestore pricing: https://cloud.google.com/firestore/pricing
- EE noncommercial tiers: https://developers.google.com/earth-engine/guides/noncommercial_tiers
