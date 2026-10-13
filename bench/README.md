# bench/ (Person A)

M2 big test + SafeShelfBench. `make bench` will write `bench/results.json` (shape: `contracts/mock/bench_results.json`). See [BACKTEST.md](../BACKTEST.md).

<!-- bench:start -->
Generated 2026-10-13T12:07:32+00:00.

| Method | Recalls flagged early | Median lead (weeks) | False alarms |
|---|---|---|---|
| keyword_rules | 11/25 | 169.9 | 11/40 |
| gemini_alone | 6/25 | 104.1 | 6/40 |
| safeshelf | 6/25 | 92.6 | 2/40 |
| safeshelf_no_pooling | 1/25 | 67.3 | 2/40 |
<!-- bench:end -->
