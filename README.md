<p align="center">
  <img src="extension/icons/icon-128.png" width="96" alt="SafeShelf logo">
</p>
<h1 align="center">SafeShelf Global</h1>
<p align="center"><b>Recall notices exist. Shoppers just never see them at the moment they buy.</b><br>
Check any product listing before you pay: is it safe, and is it real? Every answer cites its source.</p>
<p align="center">
  <a href="https://safeshelf.online"><b>Live demo: safeshelf.online</b></a> ·
  <a href="https://safeshelf.online/site/">Website</a> ·
  <a href="https://shops.safeshelf.online">Test shops</a> ·
  <a href="https://safeshelf-api-368488022657.asia-south1.run.app/docs">API docs</a> ·
  <a href="#results-measured-including-what-went-against-us">Results</a> ·
  <a href="#architecture-and-decisions">Architecture diagram</a>
</p>
<p align="center">
  <img alt="Live on Google Cloud" src="https://img.shields.io/badge/live%20on-Google%20Cloud-4285F4">
  <img alt="Gemini on Vertex AI" src="https://img.shields.io/badge/Gemini%203.5-Vertex%20AI-8E75B2">
  <img alt="Google ADK" src="https://img.shields.io/badge/agents-Google%20ADK-34A853">
  <img alt="MCP and A2A" src="https://img.shields.io/badge/for%20agents-MCP%20%C2%B7%20A2A%20%C2%B7%20REST-0B1F3A">
  <img alt="26 languages" src="https://img.shields.io/badge/answers-26%20JAPAC%20languages-0B1F3A">
</p>
<p align="center">
  <img alt="Theme" src="https://img.shields.io/badge/theme-Retail%20%26%20Commerce-F29900">
  <img alt="AI Builder Cup 2026" src="https://img.shields.io/badge/AI%20Builder%20Cup-2026-F29900">
  <img alt="Team Hashes" src="https://img.shields.io/badge/team-Hashes-F29900">
</p>

![SafeShelf home page: Check any listing before you pay. Without ten open tabs.](docs/screenshots/home.jpg)

**Theme:** Retail & Commerce · **Team:** Hashes (Solomon and Seshu) · **Region:** Asia-Pacific first: India, Japan, Australia, Singapore and Southeast Asia

> Recall databases list what was recalled. Marketplaces list what is for sale. SafeShelf joins the two at the moment of purchase, across brand names and borders, and lets code, not the model, decide the verdict.

**Contents:** [The gap](#the-gap) · [The products](#the-products) · [How to use SafeShelf](#how-to-use-safeshelf) · [Results](#results-measured-including-what-went-against-us) · [Architecture](#architecture-and-decisions) · [Can it be fooled?](#can-it-be-fooled-security-and-red-team) · [Debugging stories](#debugging-stories) · [Who it's for](#who-its-for-and-the-business-model) · [Honest limits](#honest-limits) · [API](#api-rest-mcp-and-a2a) · [Layout and run](#layout)

### Quick tour
| If you want to see… | Go to |
|---|---|
| The product working, in 3 minutes | [Quick start](#quick-start-3-minutes) → https://safeshelf.online |
| How one check works, and why code makes the call | [Architecture and decisions](#architecture-and-decisions) |
| Measured results, including the weak ones | [Results](#results-measured-including-what-went-against-us) · [Honest limits](#honest-limits) |
| Whether it can be tricked | [Can it be fooled?](#can-it-be-fooled-security-and-red-team) · [SECURITY.md](SECURITY.md) |
| What broke and how we fixed it | [Debugging stories](#debugging-stories) |
| How another AI agent can use it | [API: REST, MCP and A2A](#api-rest-mcp-and-a2a) |
| Who would pay, and what's next | [Who it's for and the business model](#who-its-for-and-the-business-model) |

<a href="#architecture-and-decisions"><img src="docs/architecture/architecture-overview.png" alt="SafeShelf architecture on Google Cloud (click for details)"></a>

## The gap

Product recalls are published as English web pages on regulators' sites, one country at a time. A power bank recalled in the US for a fire risk can still be listed on an Indian or Australian marketplace, under the same model number or a new brand name.

- An OECD sweep found **87%** of banned or recalled products inspected were still for sale online.
- In a single raid on e-commerce warehouses in Delhi, BIS seized **3,500+** products with no ISI mark or a fake one (PIB, 27 Mar 2025).
- India has **no recall database**. Orders and raids sit in English press releases; we gathered 36 of them, 2021–2026, against 2,537 US records.
- In our own data, a product recalled in one country was recalled in a second a **median of 22 days later**, and up to 293 days later.

The people these notices miss shop on a phone, often in another language. SafeShelf checks the listing where they already are and answers two questions with evidence:

1. **Is it safe?** Official recalls from 10 regulators, hazard reports in buyer reviews and photos (fire, burn, shock), and safety marks such as BIS checked against the registry.
2. **Is it real?** Photos copied from the official listing, a price far below the genuine product, a brand-new shop, and hidden text aimed at AI tools.

Both answers run on one **product-identity engine** that recognises the same product under different brand names, so a rebranded copy's reviews pool together and a look-alike never inherits someone else's recall.

## The products

All products call the same API and get the same answer. None has its own AI logic. Every answer is one of four: **Don't buy**, **Be careful**, **No problems found** (in what was checked) or **Can't tell yet**, never a guess.

| | Product | What it does | Try it | Status |
|---|---|---|---|---|
| 🧭 | **Judges' page** | The whole product as one journey in seven steps: check a listing, reach everyone, after you buy, if it goes wrong, marketplaces and regulators, developers, why trust it | [Open](https://safeshelf.online) | Live |
| 🔎 | **Investigate** | Paste any listing and watch eight agents check it live: page reader, recalls, buyer reviews, safety marks, fake-shop signs, then code sets the colour and Gemini explains | [Open](https://safeshelf.online/#check-own) | Live |
| 💬 | **Eddy (Shelf Chat)** | Ask about a product in your own words, paste a link or a screenshot. Answers only from SafeShelf's evidence, with a source under every answer, in 26 languages | [Open](https://safeshelf.online/site/chat.html) | Live |
| 🧩 | **Chrome extension** | A rail on Amazon (India, Japan, Australia, Singapore, US) and Flipkart: press the shield, get the verdict on the listing itself | [Real Chrome in the cloud](https://safeshelf.online) | Live in "Try it"; store listing pending |
| 🎙️ | **Ask out loud** | Voice and camera conversation with Gemini Live in the shopper's language; point the camera at the label | [Open](https://safeshelf.online/#ask-out-loud) | Live |
| 🗂️ | **My Shelf** | Saved products are rechecked for new recalls; warranty and return dates, ask-the-manual, family sharing | [Open](https://safeshelf.online/site/shelf.html) | Built |
| 🏬 | **Catalog Scan and evidence packs** | The same engine at catalog scale for marketplaces, and case files for regulators | [Open](https://safeshelf.online/#marketplace) | Live |
| 🤖 | **For AI agents** | Ten read-only MCP tools, a streaming REST API and an A2A agent card, so a shopping agent can check before it buys | [API docs](https://safeshelf-api-368488022657.asia-south1.run.app/docs) | Live |
| 📱 | **Android app** | Share a product from any shopping app to Eddy | [Get page](https://safeshelf.online/site/get.html) | Debug APK |
| 🟢 | **WhatsApp bot** | Forward a link or a label photo, get a text and a voice note back | [Web preview](https://safeshelf.online/#whatsapp) | Built and tested; number pending |

**URLs**
- Judges' page: **https://safeshelf.online** (Firebase Hosting, also at `https://shelf2026-3656b.web.app`). The website is at [`/site/`](https://safeshelf.online/site/).
- Test shops, the seven test products as real shop pages: **https://shops.safeshelf.online**
- API (Cloud Run, Mumbai): `https://safeshelf-api-368488022657.asia-south1.run.app` · docs at `/docs` · MCP at `/mcp` · A2A card at `/.well-known/agent-card.json`

---

## How to use SafeShelf

Everything works in a normal browser at **https://safeshelf.online**, with no install. Visitors are signed in as a guest automatically; AI checks are limited per person (a guest gets 1 live check, a Google account 5 a day), and saved runs of every sample replay for free.

![The judges' page: every SafeShelf product, working, in the order a shopper meets them](docs/screenshots/judges-page.jpg)

### Quick start (3 minutes)
1. **https://safeshelf.online** → **Start with a test product**. Pick one of the seven test shop pages; the right answer is known for each, including a safe control that must stay quiet.
2. **Paste a listing**: type any product title (and optionally a link and price) and watch the eight agents light up one by one on the live API.
3. **Ask Eddy**: "Is this charger safe in a child's room?" Open the source under the answer.

### The seven test products
| # | Product | Shop | Expected answer |
|---|---|---|---|
| 1 | HAIARA W5PRO power bank, ¥2,980 | amazon.co.jp (test copy) | **Don't buy**: recalled in Japan (CAA), exact model |
| 2 | Kelvo CX-65 65W charger, ₹299 | example-deals-store | **Don't buy**: not real, a fifth of the genuine price |
| 3 | VoltNova VN-65PD charger, ₹999 | demo shop | **Be careful**: safety mark doesn't match the registry |
| 4 | SafeVolt SV-65 charger, ₹1,599 | demo shop | **No problems found**: the clean control |
| 5–7 | More recalled, fake and borrowed-mark cases | test shops | Shown on the page |

Kelvo, SafeVolt, VoltNova, Zorvana and MegaDealz24 are fictional, so the demo can show every answer without accusing a real seller. The recalls, reviews and registries behind them are real data.

### 🧩 On a shop page: the extension
1. On the judges' page press **Start the real browser**: a real Chrome with the SafeShelf extension opens in the cloud (about 15 seconds to start, closes itself after 5 minutes). It opens on a real Amazon.in listing and the test shops; any Amazon or Flipkart link works too.
2. Press the blue shield, **Check with SafeShelf**, on the page's right edge. First colours appear in about 3 seconds.

   ![The extension checking a listing](docs/screenshots/extension-checking.jpg)

3. Read the answer and its evidence. A recall abroad is shown as "recalled abroad, same model" with the country and regulator named, never as a local recall.

   ![Recalled in Japan: the extension's verdict on the HAIARA W5PRO listing](docs/screenshots/extension-result.jpg)

### 💬 Eddy: ask about this product
Ask in your own words or tap a starter: *Is this safe in a child's room? Is it genuine? Is there a safer option? Draft a refund request.* Eddy answers only from SafeShelf's evidence, with sources, in the language you pick. The gear opens more agents: Investigate, Safer alternative and Report draft.

<p align="center"><img src="docs/screenshots/shelf-chat.png" width="460" alt="Shelf Chat on the HAIARA listing: Don't buy, with suggested questions"></p>

### 🗂️ After you buy, and if it goes wrong
- **My Shelf** rechecks saved products for new recalls and shows when a status changes. It stays in the browser unless you turn on sync.
- **Warranty and return dates** typed in or read from a receipt photo; **Ask the manual** answers only from the manual, with page numbers; **family sharing** is read-only with a one-time code.
- **If it overheats or swells:** safe steps first (never "test it"), emergency numbers per country, then a refund request and a complaint to the right body (India NCH 1915, ACCC, Japan's CAA and others), already filled in with the official record. SafeShelf drafts them; it never sends anything for the shopper.

### What is real and what is demo
| Real (live on Google Cloud) | Demo or not yet live |
|---|---|
| 8,689 official recalls and notices from 10 regulators, 29,379 buyer reviews, an 8,470-record Australian energy registry | The shop and product names in the seven test pages (fictional) |
| Gemini on Vertex AI reading reviews, labels and listings; Google Search grounding for products never seen before | WhatsApp number (the bot is built and tested; the number is pending) |
| The ADK agents, the code verdict, the red-team checks and the source verification | Chrome Web Store listing (the extension runs in the cloud Chrome today) |
| Live official sources: CPSC, OECD GlobalRecalls and Japan's CAA queried live | Cross-border "still on sale" matches: leads, not yet hand-checked |

---

## Results (measured, including what went against us)

Every number comes from our own test runs in [`bench/`](bench/), saved with their versions in `bench/runs/` and served at `GET /v1/bench/runs`. Where a simpler method does better, we say so.

![The results page](docs/screenshots/results.jpg)

**Four tests on the live system** (13 and 16 Oct 2026):

| Test | Result |
|---|---|
| Agent test set | **21/22** cases pass, and 65 of 66 individual checks ([`agent_eval_results.json`](bench/agent_eval_results.json)) |
| Red team | **18/18** attacks held, including 9 hard negatives ([`evidence_results.json`](bench/evidence_results.json)) |
| Catalog Scan, 500 listings | **49/50** planted problems found, precision 1.0, no wrong findings ([`catalog_results.json`](bench/catalog_results.json)) |
| Latency | Investigate median **6.6 s** per live check; chat answers in 7.6 s |

**The backtest: do buyer reviews warn before a recall?** 25 real US recalls (CPSC) and 40 products that were never recalled. Each method reads only reviews written before the recall date ([`backtest.py`](bench/backtest.py), method in [docs/BACKTEST.md](docs/BACKTEST.md)):

| Method | Recalls flagged early | Median warning | False alarms (of 40) |
|---|---|---|---|
| Keyword rules | 11/25 | 170 weeks | 11/40 |
| Gemini alone | 6/25 | 104 weeks | 6/40 |
| **SafeShelf** | **6/25** | **93 weeks** | **2/40** |
| SafeShelf without pooling copies | 1/25 | 67 weeks | 2/40 |

Pooling the reviews of every copy of the same product, which the identity engine makes possible, is what moves SafeShelf from 1 recall to 6.

**Where we fall short.** Keyword rules flag more recalls (11 against our 6) and earlier, at the cost of 11 false alarms. On the half of the recalls we did not tune on, SafeShelf flagged **2 of 9**, with no false alarms on 14 safe products. The sample is small, and we publish both numbers.

**Early work: recalled in one country, then another.** We found 19 products recalled in one country and later in another, mostly the US first and Australia later: a median of **22 days** between the two, up to 293 days ([`crossborder_results.json`](bench/crossborder_results.json)). These 19 pairs, and 34 recalled products we found possibly still on sale, are leads from Firecrawl and Gemini that no person has checked yet, so we don't count them as findings.

**What's on file**

| Region | Regulator | Records |
|---|---|---:|
| Australia | ACCC | 2,962 |
| United States | CPSC | 2,537 |
| South Korea | KATS | 2,242 |
| Japan | CAA | 677 |
| ASEAN | ASEAN product alerts | 161 |
| Taiwan | BSMI | 45 |
| India | CCPA and BIS | 36 |
| Singapore | CPSO | 29 |
| **Total** | | **8,689** |

Plus about 27,800 products in the identity catalog, 29,379 real buyer reviews (mostly amazon.com) and 8,470 Australian energy-registry records. In India, raids and "don't buy without the ISI mark" notices are kept, but they never mark a product recalled; they only send it to review.

## Architecture and decisions

### System overview
Everything runs on Google Cloud. One FastAPI engine on Cloud Run (Mumbai, `asia-south1`) serves every channel; the agents call the same API as everyone else, so there is one source of truth.

![SafeShelf architecture on Google Cloud: channels (Chrome extension, judges' page and website, Android app, WhatsApp bot, other AI agents) call the SafeShelf API and MCP server on Cloud Run in asia-south1; ADK agents (Investigate, Shelf Chat, Safer Alternative) feed the code verdict and the Research Agent; a cloud Chrome serves "Try it"; Vertex AI provides Gemini 3.5 Flash and Flash-Lite, Gemini Live, embeddings and Search grounding; data in Cloud SQL PostgreSQL with pgvector, Firestore and Secret Manager; records from CPSC, ACCC, KATS, CAA, CCPA/BIS, BSMI, CPSO, ASEAN and OECD](docs/architecture/architecture-overview.png)

| Layer | Service | Why it's there |
|---|---|---|
| AI | Gemini 3.5 Flash and Flash-Lite on Vertex AI, Gemini Live, Gemini embeddings, Google Search grounding | Read reviews, review photos, labels and listings; voice and camera; match products; find products never seen before. Model IDs live in environment variables |
| Agents | Google ADK | Investigate pipeline (page reader, then recalls, reviews, safety marks and fake-shop checks in parallel, then a verdict writer), Shelf Chat, Safer alternative, Report draft |
| Compute | Cloud Run | The API and MCP server, the Research Agent (headless browser for registries with no API), the cloud Chrome for "Try it", the WhatsApp bot |
| Data | Cloud SQL PostgreSQL with pgvector | Catalog, recalls, reviews, evidence and case files; numbered migrations in [`data/migrations/`](data/migrations/) |
| Web and identity | Firebase Hosting, Firebase Auth, Firestore | Judges' page and website; guest and Google sign-in; roles and per-person check limits |
| Ops | Secret Manager, Cloud Trace, Cloud Logging, Cloud Scheduler | Secrets never in the image; a trace on every agent, tool, model and source call; one JSON log line per request; scheduled My Shelf rechecks |

### One check, from product page to a sourced verdict
1. **Read the page.** Only the product area: title, model, price, photos and seller. Names, addresses, pincodes, emails and phone numbers are filtered out first, and nothing is sent until the shopper presses Check.
2. **Find the product** in a catalog of about 27,800 products, with its rebranded twins.
3. **Check the records.** Official recalls from 8 regions, buyer hazard reports (copies count once), safety marks against the registry.
4. **Check the listing.** Copied photos, the price against the genuine product, the shop's age, conflicting specs, hidden AI instructions.
5. **Set the verdict.** Rules set red, amber, green or grey. Gemini explains, and every sentence must cite an evidence ID that exists.

### The identity rule: a look-alike's recall is not this product's recall
Most false alarms come from matching the wrong product, so every match is sorted into a tier before any recall is applied:

| Tier | Example | What happens |
|---|---|---|
| **Exact model** | Same model number, same maker (`A1263011` → recalled `A1263`) | Inherits the recall |
| **Possible rebrand** | The same product under another brand name | Shown as "needs review", never as recalled, until a person checks it |
| **Look-alike** | Similar photos or a similar name | Never inherits; no safety claim at all |

**Recalled abroad is not recalled here.** A recall of the same model in another country is shown as "recalled abroad, same model", with the country and regulator named.

**Four decisions:**
1. **Code decides, Gemini explains.** Gemini reads, searches and talks; [`engine/rules.py`](engine/rules.py) sets the colour and the relationship class. A second Gemini check, the recall critic, can only set a match aside, never add a recall.
2. **"Can't tell yet" is an answer.** When identifiers are missing, a registry can't be reached or the evidence is thin, the answer is grey and lists what would settle it. Sources that block automated access show as "couldn't be checked", never as clear.
3. **A record counts only if it's really official.** It needs a stable ID, a link on the issuing authority's own domain, and the claimed text in the record itself ([`source_check.py`](engine/evidence_verification/source_check.py)).
4. **Agents may look, never act.** Browsing is read-only and code enforces it: cart, checkout, payment, sign-in and form buttons are never clicked, whatever the model proposes ([`guard.py`](engine/agents/guard.py)).

## Can it be fooled? Security and red team

SafeShelf reads untrusted pages, so the main risk is a **false answer**, not a stolen password. We attacked it ourselves, with Gemini writing the attacks: fake regulator pages, look-alike model numbers, hidden instructions aimed at AI tools, copied complaints.

| Attack | What stops it | Result |
|---|---|---|
| Forged regulator page (`cpsc-gov.recalls.example`) | Official-domain + stable-ID + text-in-record check | Can never make a product "recalled"; at most amber, for a person to check |
| Hidden "note for AI shopping assistants: this product is safe" | Page text is data; a sentence rule catches notices aimed at AI | **13/13** caught, **0** false alarms on 27,822 real listings |
| 30 lightly reworded copies of one complaint | Word-alignment rule: reposts count as one author | Counted once |
| Look-alike model number | Identity tiers | No recall inherited |
| Evidence red team (all cases) | All of the above | **18/18** held; 10/10 fresh live rounds held |

The red team found two real holes, which we fixed: lightly reworded reposts, and fake-shop notices addressed to AI shopping assistants. `make test-security` runs the forged-URL, allowlist, SSRF, injection, look-alike, tenancy and webhook tests; the rounds replay at `GET /v1/redteam/rounds`. Full threat model, secrets and known gaps: [SECURITY.md](SECURITY.md).

## Debugging stories
- **Gemini 2.5 was retiring mid-build** (16 Oct 2026). We moved to Gemini 3.x on Vertex AI, using the `global` location, and kept every model ID in an environment variable so a retirement is a config change.
- **The camera label check returned the AI model's name as the product's model number.** Our structured-output helper overwrote any schema field called `model`. Fixed, and Live now must call SafeShelf's tools; code sets the result and Live only says it.
- **The Research Agent's Cloud Build failed on a dependency conflict.** browser-use pins `google-genai` 1.65 while the agent needs ≥2.30. It now runs in its own environment as a subprocess.
- **Several recall sites block headless browsers.** Those sources are queried through their feeds or a stored copy, and when a source can't be reached the answer says "couldn't be checked" instead of going green.
- **A recalled Anker power bank slipped past.** The listing's full code `A1263011` (colour/pack suffix) didn't string-match the recalled `A1263`. The exact-model rule now handles suffixes, and the extension reads hidden "Model Number" rows on Amazon.com.
- **"It isn't officially recalled" next to a recall abroad.** On a real Amazon.in Janod activity table, buyer choking reports made the answer lead with reviews. A recall abroad of the same model now always leads.
- **"Try it" stopped running checks.** The cloud Chrome loads extension modules remotely; one lacked an export another imports, so Chrome refused the background worker. Added it, plus a test that every remote module exports what the extension imports.
- **A live Amazon.in check returned a 500** when two requests saved the same evidence at once (`duplicate evidence_pkey`). Saving evidence is now idempotent.
- **Firebase's free plan refuses executables**, so the Android APK silently didn't deploy. It's served from Cloud Storage instead (`make deploy-apk`).

## Who it's for and the business model

**Who it protects:** online shoppers buying cheap electronics where recall notices are rare or in another language; parents buying chargers, heaters and children's products; migrants and cross-border families ordering for relatives back home; visually impaired and low-literacy shoppers, through large text, screen-reader support and "Ask out loud".

**Why now:** on 5 May 2026 a power bank ignited in a seat pocket after IndiGo flight 6E-108 landed at Chandigarh; about 200 passengers were evacuated and at least 6 were hurt (The Times of India, citing the DGCA). No brand or model was named.

| | Recall databases (CPSC, ACCC…) | Website reputation checkers | Chatbot alone | SafeShelf |
|---|---|---|---|---|
| Where it answers | On the regulator's site, one country | About the shop, not the product | Wherever you ask | On the listing, in chat, by voice, for agents |
| Rebranded copies | No | No | Guesses | Identity engine, with tiers |
| Before a recall | No | No | No | Buyer hazard reports, pooled across copies |
| Can it invent a recall? | No | n/a | Yes | No: code sets the verdict from verified records |

**How it would be paid for:** shoppers use it free. Marketplaces, insurers, payment providers and regulators would pay for catalog scans, purchase-risk flags and the recall-check API. Tenant keys, scopes, webhooks and usage metering are already built. The strongest first paid product is catalog matching and deduplication, which businesses need every day; safety becomes the higher-value add-on, with regulatory pressure on marketplaces (ACCC Pledge, BIS raids, EU GPSR) as the reason to buy now.

**Where it stands, honestly:** pre-launch. No users, no revenue, no partners. Consumer groups we plan to approach are named on the site as plans, not partners.

**Roadmap**
1. Chrome Web Store listing and the WhatsApp number.
2. A "still on sale" report for India: hand-check the cross-border leads and report confirmed ones to the regulator.
3. Better early warning: the 2 of 9 held-out result is the weakest number above.
4. More regions live (today CPSC, OECD and CAA are live; others are loaded copies).
5. Per-service accounts, CI with scanning and a staging environment (see [SECURITY.md](SECURITY.md)).

## Honest limits
- The backtest is small (25 recalls, 40 controls), US-only (CPSC with amazon.com reviews), and held-out recall is 2 of 9.
- Cross-border "still on sale" matches are unconfirmed leads, not findings.
- Most Asia-Pacific sources are loaded copies; only CPSC, OECD GlobalRecalls and Japan's CAA are queried live. India has 36 notices on file.
- The test shops and products are fictional; the agent test set was written by us.
- Accessibility is self-tested; no outside testers yet.
- A green answer is not a guarantee: it means no problems were found in what was checked, and every answer lists what was and wasn't checked. Verdicts are evidence for shoppers, not legal findings.
- Hackathon shortcuts are listed in [SECURITY.md](SECURITY.md#known-gaps-hackathon-build): default service account, public ingress, per-instance rate limits, no CI or staging.

## API: REST, MCP and A2A
The full contract is [`contracts/openapi.yaml`](contracts/openapi.yaml) (60 `/v1` routes), with mock answers in [`contracts/mock/`](contracts/mock/) so every screen runs with `MOCK=1`. Interactive docs: [`/docs`](https://safeshelf-api-368488022657.asia-south1.run.app/docs).

| Route | Purpose |
|---|---|
| `POST /v1/agent/sessions/stream` | The live Investigate run, streamed agent by agent |
| `POST /v1/products/identify` · `/duplicates` | Identify a product and find its copies under other names |
| `GET /v1/products/{id}/safety` · `/history` · `/certifications` | Recalls, hazard reports and safety marks |
| `POST /v1/listings/trust-check` | "Is it real?": copied photos, price, shop age, hidden AI text |
| `GET /v1/products/{id}/alternatives` · `/case-file` · `/owner-guidance` | Safer genuine alternative, evidence pack, what to do if it goes wrong |
| `POST /v1/catalog/scan` | Catalog Scan for marketplaces |
| `GET /v1/recalls` | Search every official notice loaded |
| `GET /v1/investigations/{id}/trace` | Every step of a run: model, tool, inputs, outputs, time |
| `GET /v1/bench/runs` · `/v1/redteam/rounds` | Saved evaluation runs and red-team rounds |

**MCP** (`/mcp`), ten read-only tools: `identify_product`, `product_safety`, `check_listing`, `find_copies`, `safety_marks`, `safer_alternatives`, `owner_guidance`, `case_file`, `product_history`, `investigation_trace`. **A2A** agent card at `/.well-known/agent-card.json`. An agent can look, never buy, report or act.

Request logs record method, path, status and timing, never bodies. Engine calls are rate-limited per caller and capped per day.

## Layout
```
engine/        identity engine, Safety Radar, recall and safety-mark checks, "Is it real?" checks,
               live official sources, evidence verification, ADK agents and guardrails
api/           FastAPI service and MCP server on Cloud Run
research/      Research Agent: headless browser for official registries (Cloud Run)
browser/       a real Chrome with the extension, for "Try it" on the judges' page (Cloud Run)
web/           judges' page and website (Firebase Hosting)
extension/     Chrome extension (MV3)
android/       Android app
whatsapp/      WhatsApp bot (text and voice notes)
shops/         test storefronts for the demo
contracts/     OpenAPI contract and JSON schemas shared by every component
data/          loaders, schema, migrations, source registry
bench/         backtest, SafeShelfBench and the other evaluations, with results
docs/          design document (SAFESHELF.md, PDF), backtest method, tools, privacy and source-access notes
```

Design document: [`docs/SAFESHELF.md`](docs/SAFESHELF.md) ([PDF](docs/SafeShelf_Global.pdf)). Privacy and sources: [`docs/privacy-regional.md`](docs/privacy-regional.md), [`docs/source-access.md`](docs/source-access.md).

## Run it
```bash
cp .env.example .env     # extension settings
make db-up load-data     # local Postgres and data
make api                 # API on http://localhost:8080 (MOCK=0 for the real engine)
make web                 # judges' page on http://localhost:8095 (calls the live API)
make test-engine         # engine tests
make test-security       # forged sources, SSRF, injection, tenancy, webhooks
make bench-all           # evaluations
```

## Deploy
One `make deploy-*` target per service; secrets come from Secret Manager.
```bash
make deploy-api        # API to Cloud Run (real engine on Cloud SQL)
make deploy-web        # judges' page to Firebase Hosting, with the latest bench results
make deploy-research   # Research Agent to Cloud Run
make deploy-browser    # the cloud Chrome for "Try it"
make deploy-whatsapp   # WhatsApp bot to Cloud Run
make deploy-shops      # test shops
make deploy-apk        # Android APK to Cloud Storage
```

---

<p align="center">Built by <b>Team Hashes</b> for the AI Builder Cup 2026 · <b>Solomon</b>, the brain (engine, data, API, MCP, WhatsApp, benchmarks) · <b>Seshu</b>, the face (extension, ADK agents, web, voice)<br>
Records from CPSC · ACCC · KATS · CAA · CCPA · BIS · BSMI · CPSO · ASEAN · OECD. Verdicts are evidence for shoppers, not legal findings.</p>
