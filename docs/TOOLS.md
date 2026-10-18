# SafeShelf: tools, services and data sources

★ = what we plan to use. Everything here fits within the $300 Google Cloud trial credit. The open-source tools and datasets are free.

## Google tools

| Tool | What it does for SafeShelf |
|---|---|
| ★ **Gemini 3.x on Vertex AI** (Flash / Flash-Lite / Pro) | Core AI: reads reviews and photos, matches twins, reads safety marks, writes summaries and evidence packs. Flash-Lite handles bulk review reading cheaply; Pro handles hard cases |
| ★ **Gemma** | Free, small open model for cheap pre-filtering of large review volumes |
| ★ **Vertex AI multimodal embeddings** | Turns product photos and text into vectors for finding twins and copied photos |
| ★ **Cloud Vision API: Web Detection** | Finds where else an image appears online. Key to the **"copied photos"** check: did this shop's photo come from the brand's official page? |
| ★ **Agent Development Kit (ADK)** + **Vertex AI Agent Engine** | The SafeShelf agent: Concierge + Shelf Chat, the investigate pipeline (sequential + parallel agents), Shopper and Research agents, Investigation Copilot. Sessions hold the product identity |
| ★ **Gemini computer use** (`gemini-3.8-flash`, or `gemini-3.5-flash-lite` for speed) | Shopper Agent (clicks through the product page) and Research Agent (registries without an API). Vertex support to confirm on Oct 12 |
| **Agent Engine Memory Bank** | My Shelf: remembers what the shopper owns (Firestore also works) |
| **Firebase Cloud Messaging** | My Shelf recall push notifications |
| **A2A protocol** + **MCP** | Let other AI shopping agents call SafeShelf |
| ★ **Grounding with Google Search** | Gemini looks up recall notices or registry pages in other countries, with sources |
| ★ **Cloud Run** | Hosts our API and web app (required by the rules) |
| ★ **Cloud SQL (PostgreSQL + pgvector)** | Products, evidence and relationships, with vector search |
| ★ **BigQuery** | Fast analysis of millions of reviews for the backtest, plus trend charts |
| ★ **Cloud Storage** | Photos, documents and datasets |
| ★ **Gemini TTS / Cloud Text-to-Speech** | The "Read it to me" voice, including Hindi |
| ★ **Web Risk API** (Google Safe Browsing for businesses) | Is the shop's website already known to be harmful? An extra signal for "Is it real?" |
| **Gemini Live API** | "Ask by voice" (stretch goal) |
| **Cloud Translation API** | Translating summaries and non-English reviews |
| **Document AI** | Reading certificates and test-report PDFs (optional; Gemini can often do this itself) |
| **Vertex AI Vector Search** | Large-scale vector search later; pgvector is enough for the hackathon |
| ★ **Cloud Tasks / Pub/Sub / Cloud Scheduler** | Background jobs: ingestion, registry re-checks, daily My Shelf recall checks |
| **Firebase Hosting / Firestore** | Quick front-end hosting or simple data storage |
| **Secret Manager, Cloud Logging, Cloud Monitoring** | API keys, logs, health checks |
| **Looker Studio** | Quick trend dashboards (optional) |
| ★ **Google Antigravity / AI Studio** | The rules require one agentic platform (Agent Platform, Antigravity or AI Studio). Use it for prompt testing and building, but bill Gemini calls through Vertex: the $300 credit doesn't cover AI Studio API calls |
| ★ **Google Colab** | Notebook for running the backtest quickly |
| ★ **Lighthouse** (built into Chrome) | Accessibility, performance and quality scores |
| ★ **Chrome Extensions (Manifest V3)** | The browser extension platform. `chrome.sidePanel` for Shelf Chat, `chrome.tabs.captureVisibleTab` for screenshots, content script or `chrome.debugger` to carry out the agent's clicks |
| **Gemini Nano in Chrome** (built-in AI) | Optional on-device summaries in the extension, for privacy |
| **Google Slides** | The deck (the official template is a .pptx) |

## Data sources

| Source | Used for |
|---|---|
| ★ **CPSC Recalls API** (saferproducts.gov) | Past US recalls with product, model, sellers, hazard and date. These are the backtest's answers |
| ★ **SaferProducts.gov incident reports** | Consumer injury reports filed with CPSC: extra evidence and validation |
| ★ **Amazon Reviews 2023** (McAuley Lab, Hugging Face) | Millions of dated reviews with photos, plus product metadata. This is the backtest's input |
| ★ **Australian Energy Rating registry** (data.gov.au, open CSV/API) | Certification check with exact ground truth |
| **ACCC recalls** (productsafety.gov.au), **OECD GlobalRecalls**, **EU Safety Gate**, **Health Canada recalls** | Recalls from other countries, for JAPAC and global coverage |
| **BIS CRS and BEE star-label registries** (India) | Shown as a connector; partly manual or behind a captcha |
| ★ **RDAP lookup** (e.g. rdap.org) | Domain registration date, for the "brand-new website" check |
| **Wayback Machine API** | Whether a shop's website existed in the past |
| **Watchlist Internet fake-shop list** (Austria) | Possible fake-shop test data (to be verified) |

### Firecrawl: data collection only
We have **21,119 Firecrawl credits**, which expire on 21 Oct 2026. Firecrawl is used **only to collect data this week**. It is **not** part of the live product: no live scanning in the Lab, extension or agents. Everything collected is saved to Cloud Storage (raw snapshots) and Cloud SQL (extracted fields), so nothing depends on Firecrawl after the credits expire.

| Collect | For | Credits (est.) |
|---|---|---|
| Current listings matching about 60 recalled products (search + scrape) | Real-world finding | ~3,600 |
| ACCC + OECD recalls, 2019–2026, electrical | Recalls beyond the US (JAPAC) | ~1,500 |
| About 400 charger / power-bank listings and their rebrands | Identity pairs for SafeShelfBench | ~400 |
| Official product photos, genuine prices, authorised-seller lists, 50 genuine listings | "Is it real?" reference data and tests | ~400 |
| 500 listings for a seeded catalog | Catalog Scan test | ~500 |
| BEE star-label registry (India), only if there's no captcha | Certification check (India) | ~500 |
| Frozen snapshots (HTML, markdown, screenshot) of the demo and test pages | Repeatable tests, offline Shopper Agent tests | ~300 |
| News stories (charger fires in India) | Deck and video | ~50 |
| **Total** | | **~7,250**; the rest is spare for re-runs |

**Rules:**
- Test extraction on 10 pages first, because structured JSON may cost more than 1 credit per page.
- Scrape once, save, then always work from the saved copy.
- No bulk Amazon or Flipkart review scraping, no getting around captchas (BIS).
- Don't republish full marketplace pages in the public repo; commit only extracted fields.
- **Finish the main collection by 14 Oct**, before the build days. Top-ups (re-runs, missing pages) are possible until 20 Oct; after 21 Oct the credits are gone.

## Open-source tools

| Tool | Used for |
|---|---|
| ★ **DuckDB** or **Polars** | Querying very large review files quickly on a laptop |
| ★ **Hugging Face `datasets`** | Streaming Amazon Reviews 2023 without downloading everything |
| ★ **RapidFuzz** | Fuzzy matching of brand and model names between recalls and listings |
| ★ **imagehash** | Perceptual hashes to catch copied or reposted photos |
| **scikit-learn** | Confidence calibration, precision/recall metrics |
| **ruptures** | Detecting a sudden rise in complaint rates |
| ★ **FastAPI** | Backend API |
| ★ **React / Next.js + Tailwind** | Web app screens |
| ★ **Recharts or D3** | Timeline replay chart |
| ★ **Cytoscape.js** | Twin graph |
| **WXT or Plasmo** | Faster Chrome extension development |
| **ReportLab / WeasyPrint** | Evidence pack PDF |
| ★ **axe-core**, **NVDA** (Windows), **TalkBack** (Android) | Accessibility testing |
| ★ **Playwright** | Headless browser for the Research Agent on Cloud Run; also end-to-end tests of the app and extension |
| **GitHub Actions** | Running tests on every push |
| **Docker** | Packaging services for Cloud Run |
| **OBS Studio or QuickTime** | Recording the 3-minute demo video |

## Best tools for each job
- **Backtest:** CPSC API + Amazon Reviews 2023 + DuckDB/BigQuery + RapidFuzz + Gemini Flash-Lite, in Colab.
- **Twin finding:** Vertex multimodal embeddings + pgvector + imagehash + Gemini.
- **"Is it real?":** Cloud Vision Web Detection + RDAP + price-floor rules + Web Risk API.
- **Accessibility:** Gemini TTS + Lighthouse + axe + NVDA.
- **Data collection (this week only):** Firecrawl → Cloud Storage + Cloud SQL.
- **Agent:** ADK + Agent Engine + Gemini computer use + Playwright on Cloud Run + `chrome.sidePanel`.
