# SafeShelf backtest plan

**Goal.** Test SafeShelf's main claim on past data where the answers are already known: *"SafeShelf warns about a dangerous product weeks before the official recall."*

**How it works, simply:** we take products that were already recalled and replay their Amazon reviews in date order, as if live. We note when SafeShelf would have raised the alarm and compare that with the recall date. Never-recalled products are run the same way, so we can measure false alarms.

## Steps

1. **Pick recalls** from the **CPSC Recalls API**. Each recall lists the product, model, sellers, hazard and recall date. Keep recalls that are:
   - **sold on Amazon** (many notices say "sold exclusively on Amazon.com"; these are often white-label brands with rebranded twins);
   - **fire/burn hazards in electronics**: chargers, power banks, space heaters, hoverboards, e-bike batteries;
   - **dated 2019 to mid-2023**, because Amazon Reviews 2023 ends around September 2023.
2. **Find each recalled product in Amazon Reviews 2023.**
   - Match on brand, model and title using RapidFuzz.
   - Gemini checks unclear matches by comparing recall photos with listing photos.
   - This step is a small version of SafeShelf's twin engine.
3. **Pick controls.** For each recalled product, take 3–5 similar never-recalled products from the same category, with a similar number of reviews.
4. **Read reviews.**
   - First, a keyword filter (hot, melt, smoke, fire, burn, spark, explode, swollen, shock).
   - Then Gemini Flash-Lite decides: is this a real hazard? Which type? Is it the reviewer's own experience? Does the photo show damage?
5. **Replay and set the alarm rule.**
   - Example rule: flag when there are 3 or more independent hazard reports within 90 days, above the category's normal level.
   - **Pick the threshold on half of the products and test it on the other half.**
6. **Measure:**
   - lead time (recall date minus flag date), per product and the median;
   - false-alarm rate on the controls;
   - **the same again with rebranded twins pooled into families** (does pooling flag earlier?).

## Rules for an honest result
- Never use reviews dated on or after the recall date.
- Remove reviews that mention "recall".
- Count duplicate or copied reviews once.
- Report every outcome, including recalls we missed.

## What counts as success
| Result | Decision |
|---|---|
| 20+ recalls matched, **median lead of 2+ weeks**, **10% or fewer false alarms** | Strong: build SafeShelf as planned |
| Early flags on only some recalls, or a short lead | Present it honestly ("flagged 9 of 20, median 3 weeks earlier"); lean more on "Is it real?" and certification checks |
| Almost no early signal | Rethink before building for the week |

## Ways to improve the chance of a signal (legitimately)
- Use noisy categories: fire hazards with many reviews.
- Use photos: a melted-port photo is strong evidence on its own.
- Pool twins: this helps exactly when each listing has only a few complaints.
- Use a baseline: a rise in complaints is a stronger signal than a fixed count.

## Tools and cost
- **Tools:** CPSC API, Amazon Reviews 2023 (Hugging Face), DuckDB or BigQuery, RapidFuzz, Gemini Flash-Lite on Vertex, in Colab. See [TOOLS.md](TOOLS.md).
- **Time:** about 3–4 hours for the first version. Downloading the review data is the slow part.
- **Gemini cost:** probably a few dollars after the keyword filter.
- **Output:** a results table, a lead-time chart, a pooling chart and the false-alarm rate. These feed the performance slide and the demo timeline.

## Status
Not run yet (as of 2026-10-12).
