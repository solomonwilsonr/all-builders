# web/: the judges' page

One static page (no build step, no keys) that calls the same public API as the extension.

- **Try a sample**: six listings with known right answers (`samples/presets.json`), including a clean control that must raise no warning. Each opens with a saved run of the live API (`samples/<id>.json`) replayed at real speed, then **Run it live** streams a new run from `POST /v1/agent/sessions/stream`. Live runs are capped at 10 a day per browser; the API also rate-limits every caller.
- **Check your own listing**: the same live Investigate run for any title, link and price.
- **SafeShelf vs Gemini alone**: the backtest (`data/bench.json`, copied from `bench/results.json`), plus the agent test set and Catalog Scan results.

```
make web           # serve on http://localhost:8095
make web-samples   # re-record every sample from the live API (after an API deploy)
make deploy-web    # copy the latest bench results, then Firebase Hosting
```

`record_samples.py` won't save a run the API answered from its 10-minute memory, so wait 10 minutes after the last check of the same listing.
