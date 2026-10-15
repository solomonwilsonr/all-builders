# data/ (Person A)

M1 data collection. Raw downloads go to `data/raw/` (git-ignored). Tables: [`schema.sql`](schema.sql).

| Script | What it does |
|---|---|
| `load_cpsc.py` | CPSC recalls 2019–2026 → `raw/cpsc_recalls.jsonl`, `raw/cpsc_backtest_candidates.jsonl` (Amazon + fire/shock + electrical + before Aug 2023), and the `recalls` table |
| `load_au_registry.py` | Australian energy-rating registry (TVs, fridges, …) → `raw/au_*.csv` and `registry_energy_rating` |
| `stream_reviews.py` | Streams Amazon Reviews 2023 and keeps only matching metadata or reviews. Run on Colab or a VM |
| `load_globalrecalls.py` | JAPAC recalls (Australia, Japan, Korea, Taiwan, Singapore, ASEAN) from OECD GlobalRecalls → `raw/globalrecalls.jsonl` and the `recalls` table |
| `load_india_notices.py` | India (not in GlobalRecalls): CCPA recall orders and safety notices and BIS raids, from the PIB press releases listed in [`india_sources.json`](india_sources.json) → `raw/india_notices.jsonl` and the `recalls` table (`Kind` says which are not recalls) |
| `india_incidents.json` | Real Indian power-bank fires from the news (sources checked), for the pitch and video; not loaded anywhere |
| `firecrawl_collect.py` | Plans and runs Firecrawl jobs inside a hard credit cap; saves every result and a credit ledger |

```bash
make db-up && make load-data          # local Postgres on :5442 + recalls + registry
uv run data/firecrawl_collect.py plan-recall-twins
uv run data/firecrawl_collect.py run --jobs data/raw/firecrawl_jobs.jsonl --max-credits 10 --dry-run
```

Firecrawl key goes in `.env` (git-ignored) as `FIRECRAWL_API_KEY`, never in code.
