# SafeShelf Global · Team Hashes · AI Builder Cup 2026

**Theme:** Retail & Commerce

SafeShelf checks any product listing and answers two questions: **Is it safe?** (hazards spotted in buyer reviews and photos before an official recall, plus recall and certification checks) and **Is it real?** (copied photos, an impossible price, a brand-new website). All of this runs on one product-identity engine that recognises the same product under different brand names. A SafeShelf agent (Google ADK) can also investigate for the shopper: it clicks through photos, reviews and seller details, checks official registries, answers questions in a chat, suggests a safer genuine alternative and watches products after purchase. It works with screen readers and the keyboard, and it can read the answer aloud in plain language in 26 JAPAC languages.

## Try it
| | Link |
|---|---|
| Judges' page (web app) | https://shelf2026-3656b.web.app |
| Android app and Chrome extension downloads | https://shelf2026-3656b.web.app/site/get.html |
| Test shops (the seven test products as real web pages) | https://safeshelf-shops.web.app |
| API (Cloud Run) | https://safeshelf-api-368488022657.asia-south1.run.app |

## Repository layout
| Folder | What it is |
|---|---|
| [`engine/`](engine/) | Identity engine, Safety Radar, recall and safety-mark checks, "Is it real?" checks, live official sources, evidence verification, ADK agents |
| [`api/`](api/) | FastAPI service on Cloud Run that serves the engine |
| [`agents/`](agents/) | Google ADK agent definitions |
| [`research/`](research/) | Research Agent service: a headless browser that checks official recall sites (Cloud Run) |
| [`browser/`](browser/) | A real Chrome with the SafeShelf extension, for "Try it" on the judges' page (Cloud Run) |
| [`web/`](web/) | Judges' page (Firebase Hosting) |
| [`extension/`](extension/) | Chrome extension |
| [`android/`](android/) | Android app |
| [`whatsapp/`](whatsapp/) | WhatsApp bot (text and voice notes) |
| [`shops/`](shops/) | Test storefronts for the demo |
| [`contracts/`](contracts/) | OpenAPI contract and JSON schemas shared by every component |
| [`data/`](data/) | Data loaders, database schema and migrations, source registry |
| [`bench/`](bench/) | Backtest, SafeShelfBench and the other evaluations, with results |
| [`docs/`](docs/) | Design document ([`SAFESHELF.md`](docs/SAFESHELF.md), [PDF](docs/SafeShelf_Global.pdf)), backtest method, tools, privacy and source access notes |

## Run it
```
cp .env.example .env     # extension settings
make db-up load-data     # local Postgres and data
make api                 # API on http://localhost:8080 (MOCK=0 for the real engine)
make web                 # judges' page on http://localhost:8095 (calls the live API)
make test-engine         # engine tests
make bench-all           # evaluations
```
See the [`Makefile`](Makefile) for deploy targets and the README in each folder for details.
