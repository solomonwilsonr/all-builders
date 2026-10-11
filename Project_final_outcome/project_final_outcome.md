# ClearSight: Final Outcome (Balram OCP case study)

Status as of 2026-10-11. This records what the work established, what it did not, and the data behind each statement.

## 1. Summary

**Case tested:** Balram OCP (formerly Kalinga OCP), a coal mine in the Talcher coalfield, Angul district, Odisha, run by Mahanadi Coalfields Ltd (MCL).

**Question:** did the mine keep operating after its environmental clearance (EC) expired, and can satellite images show it?

| | Result |
|---|---|
| Did mining continue after the EC expired? | **Yes, per public records.** MCL's own production table shows output rising after the computed expiry date of 23 Oct 2021. |
| Does the CAG's 11.5 Mt figure hold up? | **Yes, roughly.** The company's production table implies about 11.0 Mt in the same window. |
| Can the satellite show it? | **Only partly.** It shows the mine footprint and small outward growth. It cannot measure how much coal was produced. |
| Did mining stop in Mar 2023? | **No.** Production and consent continue after that date. "March 2023" appears to be the end of the audit period. |
| Was our before/after activity test conclusive? | **No.** The monthly activity test was run on the wrong mine and has not yet been run on Balram. |

**Claim we can support:** "Public records show Balram kept producing, at rising volume, after the clearance's computed expiry. Satellite imagery shows the mine active over the same period, with modest outward growth beyond its 2019 outline."

**Claim we cannot support:** that satellite imagery proves illegal mining or measures production.

## 2. The case

| Fact | Value | Source |
|---|---|---|
| Names | Kalinga OCP renamed Balaram/Balram OCP in 2006. Opened 1991. | Forest site inspection report, p. 3 |
| Original EC | 24 Oct 1990, 8 MTPA, prior to the 1994 EIA rules | EAC minutes, 44.1.3 |
| EC expiry | 23 Oct 2021 (30 years plus COVID extension). The 1990 letter itself states no expiry. | CAG via [Construction World](https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253) |
| CAG finding | Mining "continued until March 2023", about 11.5 Mt, Rs 9.57 bn, without a valid EC | same article; the CAG report itself was **not** obtained |
| Existing lease | 1,309 ha | EAC minutes |
| Proposed expansion | 15 MTPA, lease to 2,574 ha. The 44th EAC (9 May 2023) **deferred** it. | EAC minutes |
| New EC | 24 Feb 2025, EC25A001OR198573 | earlier research notes; not re-verified |
| Location | About 20.95 N, 85.075 E (west of the Padma/Ananta/Jagannath blocks) | CMPDI Talcher map and the 2025 EC bounding box |

The CMPDI map used to locate the mine:

![CMPDI vegetation cover map of the Talcher coalfield, 2016](screenshots/01_cmpdi_talcher_map.png)

## 3. Evidence from documents

### Company-reported production (EAC minutes, pp. 8-10)

| Year | Production (Mt) | | Year | Production (Mt) |
|---|---|---|---|---|
| 2014-15 | 3.70 | | 2019-20 | 5.23 |
| 2015-16 | 2.52 | | 2020-21 | 6.26 |
| 2016-17 | 2.81 | | **2021-22** | **6.52** |
| 2017-18 | 2.79 | | **2022-23** | **7.74** |
| 2018-19 | 3.63 | | | |

Capacity was 8.00 Mt a year. The "excess production" column is Nil in every year. The minutes also record consent to operate for 7.74 Mt in FY2023-24 (granted 22 Mar 2023, valid to 31 Mar 2024).

### Cross-check of the CAG tonnage (rough)

- Oct 2021 to Mar 2022 is about half of FY2021-22: 6.52 / 2 = 3.26 Mt (assuming even output through the year).
- Plus all of FY2022-23: 7.74 Mt.
- Total: **about 11.0 Mt**, against the CAG's **11.5 Mt**, a difference of about 4%.

### Physical figures stated in the documents

| Item | Value |
|---|---|
| Excavated area as of 1 Apr 2023 | 519.21 ha of a planned 668 ha |
| Still to be excavated in the existing lease | 148.79 ha |
| Reclaimed as of 31 Mar 2023 | 175.17 ha technically; 89.02 ha internal dump and 26.52 ha external dump biologically |
| Internal dump height | RL +165 m reached, +205 m planned |
| Forest clearance for expansion | 193.845 ha, still pending in Dec 2023 |

Reclamation matters for the satellite results: bare ground can fall because land is being re-greened, not only because mining stopped.

## 4. Satellite analysis

### 4.1 Method in plain terms

1. **Locate the mine** using the CMPDI map and the bounding box in the 2025 EC (20.9316 to 20.9853 N, 85.0434 to 85.1060 E).
2. **Outline it** using the Maus et al. global mining polygons (v2, 2019 Sentinel-2). Polygon fid 44352 merges several Talcher mines into 46.9 km², so it was cut to the EC bounding box. The result is an **810.4 ha** outline of Balram's 2019 footprint.
3. **Measure growth beyond the 2019 outline**, inside the EC box. Count ground that became bare and stayed bare in each dry season (Feb-Apr, Dynamic World "bare" class, 10 m pixels).

Outline of the 2019 footprint (red) inside the clearance box (white); the merged neighbouring mines are orange:

![Balram outline from Maus polygon cut to the EC box](screenshots/04_balram_outline_maus_in_ec_box.png)

Dataset used for the outline:

![PANGAEA page for Maus et al. global mining polygons v2](screenshots/07_pangaea_maus_dataset_page.png)

Accuracy reported for the dataset: overall 88.3%, user's accuracy 97.2%, producer's accuracy 78.9% (it misses about a fifth of mine area). Licence CC BY-SA 4.0.

### 4.2 Result: new bare ground outside the 2019 outline (Balram, valid run)

Values are read off the chart and are approximate. The exact list was not expanded in the console.

| Onset year | New bare ground (ha) | Period covered |
|---|---|---|
| 2020 | about 0 | Apr 2019 to Apr 2020 |
| 2021 | about 22 | Apr 2020 to Apr 2021 (before expiry) |
| 2022 | about 9.5 | Apr 2021 to Apr 2022 (straddles the 23 Oct 2021 expiry) |
| 2023 | about 17 | Apr 2022 to Apr 2023 (after expiry) |
| 2024 | about 17.5 | Apr 2023 to Apr 2024 |
| 2025 | about 42 | Apr 2024 to Apr 2025 (single season, least reliable) |

![Growth chart, console output](screenshots/06_growth_chart_console.png)

Map of that new ground, coloured by the year it became bare (2020 yellow to 2025 cyan). It shows one small patch on the north-west edge of the outline:

![Onset-year map](screenshots/05_growth_onset_map.png)

**Reading:** about 10-17 ha a year of outward growth in 2022-2024, around 1-2% of the 810 ha footprint. It is real but small, and it does not separate "before" from "after" the expiry. The 2025 bar is the largest, but later years pass a weaker persistence filter (a 2025 pixel must stay bare for one season, a 2021 pixel for five), so they are more likely to include noise. Growth in 2025 may also be legitimate, because the new EC was granted in Feb 2025.

**Not yet checked:** whether the coloured patch is real mine growth rather than fallow field or village edge. A look at high-resolution imagery is still needed.

### 4.3 Earlier runs, kept for the record

**Run A: first hand-drawn polygon (about 200 ha, around the pit with the lake).** Probably Balram, not verified.

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Bare ground (ha, approx.) | 98 | 79 | 147 | 155 | 160 | 153 | 146 |
| Mean NDVI (approx.) | 0.17 | 0.21 | 0.06 | 0.05 | 0.02 | 0.05 | 0.05 |

The pit was already almost entirely bare by 2021, so "how much is bare" cannot show whether it was still being worked.

![Run A charts](screenshots/02_first_polygon_charts_200ha.png)

**Run B: polygon drawn at the Google coordinates (20.962 N, 85.178 E), 698.4 ha. This is NOT Balram.** By our reading of the CMPDI map, those coordinates fall about 10 km east, in the Bhubaneswari/Lingaraj block. These numbers must not be quoted as Balram results:

- Bare ground (approx. ha): 245, 245, 548, 388, 382, 313, 402 for 2019-2025.
- Monthly activity (mean absolute change in the bare-soil index): 0.0592 before expiry, 0.0674 from Oct 2021 to Mar 2023, 0.0527 after Mar 2023.

![Run B charts, wrong mine](screenshots/03_other_mine_charts_698ha_NOT_BALRAM.png)

## Conclusion 1: first growth test (version 1 script)

![Conclusion 1: console output of the first growth test](screenshots/08_conclusion1_v1_growth_chart.png)

### What the numbers say
- **Balram's 2019 footprint:** about 810 ha. The 1990 lease was 1,309 ha, so that's plausible.
- **New bare ground outside that footprint, by year (read off the bars):**

| Year | New ha (approx.) | Period it covers |
|---|---|---|
| 2020 | ~0 | Apr 2019 – Apr 2020 |
| 2021 | ~22 | Apr 2020 – Apr 2021 (before expiry) |
| 2022 | ~10 | Apr 2021 – Apr 2022 (straddles the 23 Oct 2021 expiry) |
| **2023** | **~17** | **Apr 2022 – Apr 2023 (after expiry, while the CAG says mining continued)** |
| 2024 | ~17 | after the CAG end date |
| 2025 | ~42 | Apr 2024 – Apr 2025 |

### What I'd conclude
1. **There is outward growth after expiry, but it's small.** About 10–17 ha a year in 2022–2023, which is 1–2% of the 810 ha footprint. It's real enough to see, but not dramatic.
2. **The pattern doesn't match the expected story cleanly.** Growth doesn't stop after Mar 2023. 2024 is about the same as 2023, and 2025 is the largest bar.
3. **So I can't claim this proves anything yet.** It's consistent with continued activity, but it doesn't clearly separate "mining continued until Mar 2023, then stopped".

### Why the later bars may be inflated
- **Weaker persistence filter.** A 2021 pixel has to stay bare for five dry seasons to count. A 2024 pixel only has to stay bare for two, and a 2025 pixel for one. Later years therefore let in more noise, such as fallow fields.
- **2025 may be real.** The new clearance (15 MTPA, 2,574 ha) was issued on 24 Feb 2025, so expansion in 2024–25 may be legitimate site preparation. The 2025 bar is also a one-season estimate.
- **The CAG end date may be the audit's cutoff.** "Until Mar 2023" may not mean the mine physically stopped.

### Before drawing conclusions
1. **Look at the map.** Do the coloured patches (2021 yellow ... 2025 cyan) sit on real new pits and dumps, or on farm plots and village edges? This is the most important check.
2. **Expand the printed list** and send me the exact six numbers.

### Fixing the bias
I'd make the filter equal for every year: a pixel counts as new ground only if it's bare in year Y and Y+1, with 2025 shown separately and flagged as unconfirmed. That makes the bars comparable. I'd also add a control mine to see whether random "growth" of 10–20 ha a year appears there too, which would tell us whether this is signal or noise.

Send the map screenshot first. If the patches look like real mine growth, we do the fix. If they look like farmland, we tighten the method.

## 5. Problems found along the way

| Problem | Effect | Resolution |
|---|---|---|
| Google's coordinates for "Balram OCP" pointed to a different mine | One full analysis run used the wrong place | Located the mine from the CMPDI map and the EC box instead |
| Hand-drawn polygons included farmland and village | Crop cycles drowned the mine signal | Switched to a published mine outline cut to the EC box |
| The Maus polygon merges neighbouring mines | Could not isolate Balram directly | Intersected with the EC bounding box |
| Assumed mining stopped in Mar 2023 | Our test expected a drop that never happens | The EAC minutes show production and consent continuing, so the end date is the audit's cutoff |
| "How much is bare" is saturated once the pit is bare | Cannot distinguish a busy pit from an idle one | Needs activity signals (radar, change detection) |

## 6. Limits

- **The satellite cannot measure production.** Output rose about 20-40% across the expiry date, which is probably below what 10 m optical imagery can resolve.
- **Surface change only.** Digging deeper and dumping inside the old outline are not captured by the growth measure.
- **The CAG report was not read.** The expiry, tonnage and period come from a news article. Whether the EC was revalidated is unknown.
- **Chart values are approximate**, read from screenshots.
- **The monthly activity test has not been run on Balram.** The only monthly result is from the wrong mine.
- **Dynamic World misclassifies some land**, notably fallow fields and dry scrub as "bare".
- **Single mine.** Nothing here shows the method separates violators from compliant mines. That needs control mines.

## 7. Next steps

1. Get the CAG report (cag.gov.in) and the Feb 2025 EC to fix the violation window.
2. Run the monthly activity analysis on the Balram outline, expecting activity to continue through 2024.
3. Compare yearly satellite activity with the production table (2017-18 to 2022-23, six points) to see whether activity rises with output.
4. Check the coloured growth patch and a few dates around Oct 2021 against high-resolution imagery (Google Earth historical view).
5. Add Sentinel-1 radar, which sees through cloud and responds to earth moving.
6. Repeat the identical steps on 2 more mines with documented violations and 2 control mines.
7. Test the second claim: excavation into the expansion area and Gopalprasad Reserve Forest before forest clearance.

## 8. Files and how to reproduce

| File | Purpose |
|---|---|
| [code/00_clip_maus_gpkg.py](code/00_clip_maus_gpkg.py) | Cuts the Maus mining polygons to the Talcher area (pure Python, no GDAL needed) |
| [code/01_balram_outline_and_growth.js](code/01_balram_outline_and_growth.js) | Earth Engine script: Balram outline plus growth beyond the 2019 footprint (section 4.2) |
| [code/02_yearly_and_monthly_activity.js](code/02_yearly_and_monthly_activity.js) | Earth Engine script: yearly bare ground, NDVI and monthly activity for a drawn polygon (section 4.3) |
| [data/talcher_mines_maus_v2.geojson](data/talcher_mines_maus_v2.geojson) | The 14 Maus polygons near Talcher (CC BY-SA 4.0) |
| [screenshots/](screenshots/) | Images used above |

To rerun: register for Earth Engine (free, noncommercial, Community tier), paste `01_balram_outline_and_growth.js` into the Code Editor, and click Run. The script is self-contained.

## 9. Sources

- CAG finding: [Construction World](https://www.constructionworld.in/energy-infrastructure/coal-and-mining/cag-flags-rs.-9.76-bn-coal-mining-irregularities-in-odisha/98253) (opened and checked); also reported by [Business Standard](https://www.business-standard.com/industry/news/cag-detects-1-210-crore-mining-irregularities-in-odisha-amid-mmdr-debate-126100400520_1.html) and [OdishaTV](https://odishatv.in/odisha/cag-flags-rs-975-crore-coal-mining-irregularities-in-odisha-12593636) (search summaries only).
- [Minutes of the 44th EAC (Coal), 9 May 2023](https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/1905202365746813FinalMoM44EACmeeting.pdf): production table, area figures, expansion proposal.
- [Forest site inspection report, Dec 2023](https://forestsclearance.nic.in/writereaddata/AdditionalInformation/AddInfoSought/0_0_1211612712131SIR_BalaramOCP_MCL_193845Ha.pdf): rename history, reclamation, forest clearance status.
- Maus, V. et al. (2022), Global-scale mining polygons (Version 2), PANGAEA, [doi:10.1594/PANGAEA.942325](https://doi.org/10.1594/PANGAEA.942325).
- CMPDI, Vegetation Cover Mapping of Talcher Coalfield (2016), supplied by the project owner.
- Earlier feasibility notes: [../feasibility/FEASIBILITY.md](../feasibility/FEASIBILITY.md).
