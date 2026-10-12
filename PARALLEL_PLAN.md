# Parallel work plan: Person A + Person B

How two people build SafeShelf at the same time and join the pieces later. Each module is described in [`MODULES.md`](MODULES.md).

Deadline: **18 Oct 2026, 11:59 PM IST** (we aim for 17 Oct). Live version in Notion: *SafeShelf Plan → Parallel work plan*.

## How to use this plan

1. **Decide who is who.** Write the names in the table below.
2. **Each person follows their own column** and ticks the boxes as they go. Both columns run at the same time.
3. **Meet at the 🔗 join points** to put the pieces together.

| Role | Name | Works on | Owns folders |
|---|---|---|---|
| **Person A (Brain)** | _(fill in)_ | M1 Data, M2 Big test + Bench, M3 Find copies, M4 Safety Radar, M5 Recall + safety marks, M6 Is it real?, M7 API, M12 WhatsApp bot, M14a Business backend, M16 Real-world finding | `engine/` `api/` `bench/` `data/` `whatsapp/` |
| **Person B (Face)** | _(fill in)_ | M8 Extension + accessibility, M9 AI agents, M10 My Shelf + scan + report, M11 Website + login, M13 Voice, M14b Business screens, M15 Judges' Lab | `extension/` `agents/` `web/` `lab/` |
| **Both together** | | M0 Foundation (Day 1), video storyboard (Day 2), M17 Submission (Day 6) | `contracts/` (change only after telling the other person) |

**About the time estimates (⏱):** rough hours for one person **using Claude Code**. Without AI help, expect about double. Each person has about 10–12 working hours a day. Total: Person A ≈ 49 h, Person B ≈ 49 h, together ≈ 14 h.

**The trick that lets us work separately:** in M0 we write down the exact shape of every API answer (`contracts/openapi.yaml` + example JSON in `contracts/mock/`). Person A makes the engine return exactly that. Person B builds against the mock data until the real engine is ready, then swaps it in. Nothing else changes.

---

## Day 1: 12 Oct · ⏱ A ≈ 6 h · B ≈ 5 h · together 3 h

**Together first: [M0 Foundation](MODULES.md#m0-foundation) · ⏱ 3 h**
- [ ] Create the repo folders: `engine/` `api/` `bench/` `data/` `whatsapp/` `extension/` `agents/` `web/` `lab/` `contracts/` · ⏱ 0.25 h
- [ ] Google Cloud: billing on, Vertex AI on, Gemini 3.x + computer-use model names confirmed · ⏱ 0.5 h
- [ ] Create Cloud SQL (Postgres + pgvector) and a Cloud Storage bucket · ⏱ 0.5 h
- [ ] Write `contracts/openapi.yaml` (every API endpoint) · ⏱ 0.75 h
- [ ] Write `contracts/mock/*.json` (one example answer per endpoint) · ⏱ 0.5 h
- [ ] Write the database tables (one SQL file) · ⏱ 0.25 h
- [ ] Pick 3–5 demo products with fixed IDs · ⏱ 0.25 h

| 🔵 Person A (Brain) | 🟣 Person B (Face) |
|---|---|
| ☐ Put the **mock API** online on Cloud Run (`MOCK=1`): [M7](MODULES.md#m7-api-server) · ⏱ 1.5 h | ☐ Apply for the **WhatsApp Business test number**: [M12](MODULES.md#m12-whatsapp-bot) · ⏱ 0.5 h |
| ☐ Load CPSC recalls + Australian registry: [M1](MODULES.md#m1-data-collection) · ⏱ 2 h | ☐ Create the **Firebase** project: [M10](MODULES.md#m10-my-shelf-camera-scan-report-form) · ⏱ 0.5 h |
| ☐ Start Firecrawl collection: [M1](MODULES.md#m1-data-collection) · ⏱ 1.5 h | ☐ Build the **demo product page**: [M8](MODULES.md#m8-browser-extension--accessibility) · ⏱ 2 h |
| ☐ Set up Colab / cloud VM for the big review files: [M1](MODULES.md#m1-data-collection) · ⏱ 1 h | ☐ Build the **fake shop page** (with hidden trick text): [M8](MODULES.md#m8-browser-extension--accessibility) · ⏱ 2 h |

🔗 **Join point (evening, ⏱ 0.5 h):** Person B calls the mock API and gets the demo product back.

---

## Day 2: 13 Oct · ⏱ A ≈ 11 h · B ≈ 10 h · together 1 h

| 🔵 Person A (Brain) | 🟣 Person B (Face) |
|---|---|
| ☐ [M3](MODULES.md#m3-identity-engine-find-copies) Find copies: fingerprints, look-alike search, Gemini compare, 5 labels · ⏱ 5 h | ☐ [M8](MODULES.md#m8-browser-extension--accessibility) Chrome extension panel "Is it safe? / Is it real?" (mock data) · ⏱ 4 h |
| ☐ [M4](MODULES.md#m4-safety-radar) Safety Radar: Gemini reads reviews + photos · ⏱ 3 h | ☐ [M8](MODULES.md#m8-browser-extension--accessibility) Side panel · ⏱ 2 h |
| ☐ [M2](MODULES.md#m2-big-test--safeshelfbench) Keyword and Gemini-alone scores · ⏱ 2 h | ☐ [M9](MODULES.md#m9-ai-agents) Shelf Chat with ADK (mock data) · ⏱ 4 h |
| ☐ [M1](MODULES.md#m1-data-collection) Finish loading Amazon reviews (background) · ⏱ 1 h | |

🔗 **Together (⏱ 1 h):** plan the demo video (storyboard), [M17](MODULES.md#m17-submission).

---

## Day 3: 14 Oct · ⏱ A ≈ 12 h · B ≈ 11.5 h · join 1 h

| 🔵 Person A (Brain) | 🟣 Person B (Face) |
|---|---|
| ☐ [M5](MODULES.md#m5-recall-check--safety-mark-check) Recall check (exact matches only) · ⏱ 2 h | ☐ [M9](MODULES.md#m9-ai-agents) Investigate (Shopper Agent): clicks, overlay, Esc to stop · ⏱ 5 h |
| ☐ [M5](MODULES.md#m5-recall-check--safety-mark-check) Safety mark check (Australian registry + BIS mock) · ⏱ 2 h | ☐ [M9](MODULES.md#m9-ai-agents) Research Agent (Australian registry) · ⏱ 2 h |
| ☐ [M6](MODULES.md#m6-is-it-real--spec-and-price-check) "Is it real?": copied photos, low price, new website · ⏱ 3 h | ☐ [M9](MODULES.md#m9-ai-agents) Safer Alternative · ⏱ 1.5 h |
| ☐ [M6](MODULES.md#m6-is-it-real--spec-and-price-check) Spec and price check · ⏱ 1 h | ☐ [M8](MODULES.md#m8-browser-extension--accessibility) Accessibility: screen reader, keyboard, Read it to me, plain language, Hindi · ⏱ 3 h |
| ☐ [M2](MODULES.md#m2-big-test--safeshelfbench) Full big test on 25+ recalls · ⏱ 3 h | |
| ☐ [M1](MODULES.md#m1-data-collection) Finish Firecrawl collection · ⏱ 1 h | |

🔗 **Join point (evening, ⏱ 1 h):** swap mock data for the real `identify`, `safety`, `certifications` and `trust-check` answers. The extension shows real results.

---

## Day 4: 15 Oct · ⏱ A ≈ 11.5 h · B ≈ 10.5 h · join 1 h

| 🔵 Person A (Brain) | 🟣 Person B (Face) |
|---|---|
| ☐ [M7](MODULES.md#m7-api-server) Finish real API + MCP for other AI agents · ⏱ 3 h | ☐ [M10](MODULES.md#m10-my-shelf-camera-scan-report-form) My Shelf + daily recall check + phone alert · ⏱ 3 h |
| ☐ [M12](MODULES.md#m12-whatsapp-bot) WhatsApp bot (link or photo → answer + voice note) · ⏱ 4 h | ☐ [M10](MODULES.md#m10-my-shelf-camera-scan-report-form) Scan with phone camera · ⏱ 2 h |
| ☐ [M16](MODULES.md#m16-real-world-finding) Search current listings for copies of recalled products · ⏱ 3 h | ☐ [M10](MODULES.md#m10-my-shelf-camera-scan-report-form) Report a problem form · ⏱ 1.5 h |
| ☐ [M3](MODULES.md#m3-identity-engine-find-copies) Product history page data · ⏱ 1.5 h | ☐ [M11](MODULES.md#m11-website--one-account--share-button) Website + one login + share button · ⏱ 4 h |

🔗 **Join point (evening, ⏱ 1 h):** agents run on real data. Investigate and Shelf Chat work on the fake shop page.
**Decision:** if everything is on track, add the small food demo (Phase 2 preview, ⏱ about 4 h).

---

## Day 5: 16 Oct · ⏱ A ≈ 9 h · B ≈ 11.5 h · join 2 h

| 🔵 Person A (Brain) | 🟣 Person B (Face) |
|---|---|
| ☐ [M14a](MODULES.md#m14a-business-backend) Catalog Scan backend · ⏱ 3 h | ☐ [M13](MODULES.md#m13-ask-by-voice) Ask by voice · ⏱ 2 h |
| ☐ [M14a](MODULES.md#m14a-business-backend) Evidence pack + supply chain data · ⏱ 2.5 h | ☐ [M14b](MODULES.md#m14b-business-screens) Business dashboard + Catalog Scan screen + supply chain map · ⏱ 3.5 h |
| ☐ [M2](MODULES.md#m2-big-test--safeshelfbench) Final scores (`make bench`) · ⏱ 1.5 h | ☐ [M14b](MODULES.md#m14b-business-screens) Regulator form helper (stops before Submit) · ⏱ 2 h |
| ☐ [M16](MODULES.md#m16-real-world-finding) Check real-world matches by hand · ⏱ 2 h | ☐ [M15](MODULES.md#m15-judges-lab) Judges' Lab: 5 steps, 7 Challenge cases, trace, audit report · ⏱ 4 h |
| ☐ Spare: help Person B with joining · ⏱ 2 h | |

🔗 **Midday (⏱ 2 h):** join everything. The full Lab path works start to finish.
🔒 **Evening: feature freeze.** Only bug fixes after this.

---

## Day 6: 17 Oct · ⏱ together ≈ 9.5 h

**Together: [M17 Submission](MODULES.md#m17-submission)**
- [ ] Report the real-world finding to the regulator ([M16](MODULES.md#m16-real-world-finding)) · ⏱ 1 h
- [ ] Record the demo video (with the blind tester) · ⏱ 4 h
- [ ] Make the slides · ⏱ 2 h
- [ ] Update the PDF · ⏱ 1 h
- [ ] Make the repo public with a clear README · ⏱ 1 h
- [ ] **Submit** · ⏱ 0.5 h

18 Oct is a spare day, only for fixing problems.

---

## Rules so we don't block each other

- **Own folders.** Person A: `engine/` `api/` `bench/` `data/` `whatsapp/`. Person B: `extension/` `agents/` `web/` `lab/`. Shared: `contracts/`. **Tell the other person before changing it.**
- **One Git branch per module** (e.g. `m3-identity`). Merge to `main` at each join point.
- **Never wait.** Person B always builds on the mock API. Need something new? Add an example to `contracts/` first, tell the other person, keep going.
- **Mocks stay working.** `MOCK=1` must always run, so the screens can be demoed even if a real part breaks.
- **Two 15-minute check-ins a day.** Morning: what I'm building, what I need. Evening: what's merged.
- **Claude Code in parallel:** one Git worktree per module, so agents don't edit the same files.
- **Stuck for more than an hour?** Say so straight away.
- **Running 50% over the estimate?** Tell the other person and cut to the module's minimum version.
