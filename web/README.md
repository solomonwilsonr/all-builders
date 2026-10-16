# web/: the judges' page

One static page (no build step, no keys) that calls the same API as the extension.

**Sign-in is required.** Every page starts hidden behind a "Sign in with Google" card (`auth.js`, Firebase Auth,
project `shelf2026-3656b`; settings in `firebase-config.js`), and every API call carries the person's ID token, which
the extension stores for later API requests. Other pages:

- `signin.html?ext=<id>`: the extension's sign-in; hands the session to the extension after Google sign-in.

The saved samples and `data/*.json` are plain files on Hosting, readable without a sign-in; everything live goes
through the API and needs one. Sign-in only works on addresses listed in Firebase → Authentication → Settings →
Authorized domains (localhost and `shelf2026-3656b.web.app` are there by default).

- **Try a sample**: six listings with known right answers (`samples/presets.json`), including a clean control that must raise no warning. Each opens with a saved run of the live API (`samples/<id>.json`) replayed at real speed, then **Run it live** streams a new run from `POST /v1/agent/sessions/stream`. Live runs are capped at 10 a day per browser; the API also rate-limits every caller.
- **Check your own listing**: the same live Investigate run for any title, link and price.
- **SafeShelf vs Gemini alone**: the backtest (`data/bench.json`, copied from `bench/results.json`), plus the agent test set and Catalog Scan results.

```
make web           # serve on http://localhost:8095
make web-samples   # re-record every sample from the live API (after an API deploy)
make deploy-web    # copy the latest bench results, then Firebase Hosting
```

`record_samples.py` won't save a run the API answered from its 10-minute memory, so wait 10 minutes after the last check of the same listing.

Website pages use sign-in without role-based menus or access checks.
Extension RBAC uses Firebase identity and Firestore `user_roles/{UID}`; see `../extension/README.md`.
