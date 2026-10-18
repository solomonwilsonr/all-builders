# extension/ (Person B)

Chrome extension: an in-page SafeShelf button that opens an "Is it safe? / Is it real?" card. Talks to the local SafeShelf API at `http://localhost:8080` for checks, chat and evidence. See [MODULES.md](../docs/MODULES.md) M8.

## Configuration
Edit `EXTENSION_API_BASE`, `EXTENSION_SHELF_SYNC`, `EXTENSION_SIGNIN_URL`, and `EXTENSION_FIREBASE_API_KEY` in the root `.env` (see `.env.example`). Run `npm --prefix extension run build:config` from the repo root before loading the extension and after each config change, then reload it in Chrome. Node 22+ is required. Only these public values are bundled; `GOOGLE_API_KEY` is never copied. For new API/sign-in domains, update the manifest host permissions and externally connectable matches.

## Try it
1. Run `make web` (:8095) for the local Firebase sign-in page. In another terminal run `make api` (:8080; mock responses by default). For demo shop pages run `make demo-pages` (:8090).
2. Chrome → `chrome://extensions` → Developer mode → **Load unpacked** → select this `extension/` folder.
3. Open http://localhost:8090/fake-shop.html (or an Amazon.in / Flipkart product page) and click the **SafeShelf** button at the bottom right. Nothing is sent to the API until you click. Click the toolbar icon for the menu: **My Shelf** and **SafeShelf on/off**.

## Sign-in
Sign in with Google to unlock the extension. Toolbar icon → **Sign in with Google** opens the website's `signin.html` (`SIGNIN_URL` in `config.js`), which signs in with Firebase and hands the session back to the extension (`externally_connectable` in `manifest.json`; only those sites can). `session.js` keeps it in this browser, renews the one-hour ID token and sends it with every API call; My Shelf, the Lab and Settings are covered by a sign-in card (`gate.js`) until then. The popup shows who is signed in and their role: **shopper** (everything here), **business** (also Catalog Scan in the Lab) or **admin**.

Sign-in is local: `make web` serves `http://localhost:8095/signin.html`. Enable the Google provider and authorize `localhost` in Firebase Authentication settings. After Google login, the page hands the session straight to the extension; the API does not need to be running for this handoff. The local API verifies the token when you actually make a request. Reload the extension at `chrome://extensions` after changing its files, close old sign-in tabs, and open sign-in again. No Firebase Hosting deployment or gcloud is required for this setup. Google sign-in and token renewal still need an internet connection.

Switch to Cloud Run by editing `EXTENSION_API_BASE` in the root `.env` and regenerating the config (and add the URL to `host_permissions`). Read-aloud uses the browser voice for now; Gemini TTS + Hindi come next.


## Components, one per API
Each one asks `/health` which endpoints are really live and shows "Not live on the SafeShelf API yet" for the rest. It never shows example data, and lights up by itself when the API goes live. (`ops.js` is the single door; `panels.js` turns answers into rows.)

| Component | API | Cost |
|---|---|---|
| 🛡 Check card | `trust-check`, `safety` | AI (estimate shown first) |
| Card → Marks | `certifications` | database read |
| Card → Copies | `relationships`; button "Find copies with AI" → `duplicates` | read; AI (estimate shown) |
| Card → History | `history` | read |
| Card → Safer options | `alternatives` | read |
| Card → Details | `products/{id}`; button "How was it identified?" → `identify` | read; AI (estimate shown) |
| Card → Report | `reports` | write |
| Ask (side chat on product pages; folded under the result on results-page cards) | `agent/sessions`, `evidence` | AI |
| 📚 Save | `shelf/items` | write |
| Lab (toolbar menu → Judges' Lab) | all endpoints' status, `bench/results`, `investigations/{id}/trace`, `catalog/scan`, product explorer | catalog scan warns about cost |


Extension RBAC reads Firestore directly using Firebase sign-in. No API role endpoint or Cloud Run
role deployment is required. Normal checks still use the existing product API.
Regular users have checks, chat, My Shelf, themes, and personal settings.
Admins additionally have Judges’ Lab, Administration diagnostics, and “Ask before paid requests”.
Background actions check Firestore each time; locally stored roles never authorize access.

In Firebase Console → Authentication → Users, copy the account UID.
In Firestore’s default database, create `user_roles/{UID}` with string `role` = `admin`.
Delete the document or set the role to `user` to revoke access.
Publish the rules from `web/firestore.rules` in Firebase Console → Firestore → Rules.
Users may get only their own role document; all client writes and collection listing are denied.
If you have existing rules for other collections, preserve those and ensure no broad rule allows role writes.
Reload the extension at `chrome://extensions`, then reopen Settings to refresh permissions.
Personal defaults do not overwrite the admin-only paid-request setting.
