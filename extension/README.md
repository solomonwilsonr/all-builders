# extension/ (Person B)

Chrome extension: an in-page SafeShelf button that opens an "Is it safe? / Is it real?" card. Talks only to the live SafeShelf API (Cloud Run), for the check, the chat, evidence and the shelf. No local service and no mock data. See [MODULES.md](../MODULES.md) M8.

## Try it
1. Nothing to start for the extension itself. For the demo shop pages: `make demo-pages` (:8090).
2. Chrome → `chrome://extensions` → Developer mode → **Load unpacked** → select this `extension/` folder.
3. Open http://localhost:8090/fake-shop.html (or an Amazon.in / Flipkart product page) and click the **SafeShelf** button at the bottom right. Nothing is sent to the API until you click. Click the toolbar icon for the menu: **My Shelf** and **SafeShelf on/off**.

Switch to Cloud Run by editing `API_BASE` in `config.js` (and add the URL to `host_permissions`). Read-aloud uses the browser voice for now; Gemini TTS + Hindi come next.

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
