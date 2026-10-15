# SafeShelf checklist

**Last updated:** 16 Oct 2026 (Day 5 of 6)
**Deadline:** 18 Oct 2026, 11:59 PM IST · **Our target:** 17 Oct · **Feature freeze:** evening of 16 Oct

Updated with every change. For the details behind each line, see [plan.md](plan.md).

## In one line
The engine, agents and data are built and working. What's missing is mostly what judges see: a web page they can open, the video, the deck and the submission.

## What SafeShelf does
Give it a product listing and it answers two questions:
1. **Is it safe?** Official recalls, danger warnings in buyer reviews and photos, and whether the safety marks are real.
2. **Is it real?** Copied photos, a price that's too low, a brand-new website, specs that don't match the genuine product, and hidden text meant to trick an AI.

---

## ✅ Done

**Live on Google Cloud**
- [x] API live on Cloud Run: 18 endpoints return real data
- [x] Cloud SQL + pgvector, Gemini 3.x on Vertex, Cloud Storage, Secret Manager; public API is rate-limited
- [x] Research Agent on its own Cloud Run service (headless browser for recall sites with no API)
- [x] Off Gemini 2.5 before its 16 Oct retirement

**Engine**
- [x] Find copies: the same product under different brand names
- [x] Safety Radar: reads reviews and review photos for danger (20/20 on hand-labelled reviews)
- [x] Recall and safety-mark checks: only an exact model counts as "recalled"
- [x] Is it real? checks: photos, price, website age, specs, hidden text
- [x] Catalog Scan for businesses: precision 1.00, recall 0.98 on a 500-row test
- [x] "Already bought it?" owner guidance and case file

**Agents (Google ADK)**
- [x] Investigate, Shelf Chat (English + Hindi), Safer Alternative, Report Draft, Shopper Agent, Research Agent
- [x] Live agent steps; colours arrive in about 3 seconds
- [x] MCP server and A2A agent card so other AI agents can use SafeShelf

**Data**
- [x] ~27,800 products and 29,379 real reviews
- [x] 2,537 US recalls + 6,116 JAPAC recalls (Japan, Australia, Korea, Taiwan, Singapore, ASEAN)
- [x] 8,470 Australian energy-registry records

**Measured results**
- [x] Backtest: SafeShelf catches as many recalls early as Gemini alone (6/25) with a third of the false alarms (5% vs 15%)
- [x] Agent test set: 18/18 cases pass on the live API

**Apps**
- [x] Chrome extension: Amazon India, Japan, Australia, Singapore and Flipkart
- [x] New look for the extension (16 Oct): one chat instead of two, with sources, Listen, Copy and Try again; the verdict comes first on the card; loading shows what is being checked; Investigate matches the card; "Check this page" in the toolbar menu
- [x] Model numbers read right (16 Oct): "Convertible 5-in-1" was taken as model "IN1" on a Samsung fridge on Amazon.in, and long codes like RS76CG8003S9HL were missed; the shop's own "Model number" now comes first. **Needs `make deploy-api`** to reach the live API
- [x] Chat page (`extension/demo/chat.html`) rebuilt for shoppers: example questions to start, live agent steps, paste or drop a screenshot, English/हिन्दी switch, works on a phone; developer controls moved to a Tools drawer
- [x] WhatsApp bot built and tested: link or photo in, Hindi or English text + voice note out
- [x] Other JAPAC shops (16 Oct): the website-age check now looks up the shop itself on Japanese and South-East Asian addresses. Before, `item.rakuten.co.jp` was looked up as `co.jp`, and `.com.sg`, `.com.my`, `.co.id`, `.co.th` and `.com.ph` were wrong the same way. Shopee, Lazada, Rakuten, Tokopedia, Mercari, Qoo10, Kogan, Trade Me and others now count as big marketplaces, so the seller is judged rather than the website. On shops the extension can't read, the extension now tells people to send the link or a screenshot to chat or WhatsApp. **Needs `make deploy-api`** to reach the live API

---

## 🔨 In progress
- [ ] **Judges' web page** (`web/`): built and tested locally (desktop, phone, dark mode), not deployed yet. Six samples with known right answers: recall, fake shop, borrowed safety mark, buyer hazard reports, unknown product, and a clean control that must stay quiet. Each opens with a saved real run replayed at real speed, then **Run it live with Gemini** (10 a day per browser). Also "Check your own listing" and a **SafeShelf vs Gemini alone** tab with the backtest. To go live: `make deploy-api` (two engine fixes below), then `make web-samples`, then `make deploy-web` (Firebase Hosting; Firebase may need enabling on the project first).
- [ ] **Two engine fixes, waiting for `make deploy-api`:** a safety mark the registry gives to another brand now makes "Is it real?" amber (before, it was found but ignored); Gemini's answer no longer mentions "green" when nothing is green.
- [ ] **Recall Catalog**: browse and search every loaded recall by country, regulator or hazard (`GET /v1/recalls`, `GET /v1/recalls/{id}`); also fixes dead image links and old ACCC links. Tests pass (7 new, 28 API). Next: commit, then deploy (`make deploy-api`).

---

## ❌ To do

**Must have for submission**
- [ ] 🚨 **Web page for judges:** built (see In progress); needs the deploys and a final look on a phone.
  - The new chat page needs no extension and calls the live API, so it could be added as another tab.
  - Ideas to copy from other teams (quick path with 3 examples, `?product=&lang=hi` deep links, verdict words, measured results, Verified vs AI reading): [MODULES.md P2-2](MODULES.md#p2-2-ideas-from-other-teams-entries)
- [ ] Connect the WhatsApp bot to a Meta test number and record the Hindi voice-note moment
- [ ] 3-minute demo video
- [ ] Deck from the official 16-slide template, exported to PDF
- [ ] Merge `person-1` into `main`, update the README, make the GitHub repo public
- [ ] Final `make bench` and `make eval-agents`; `make warm` before recording
- [ ] Submit: deployed link, public repo, video, deck

**Other JAPAC shops (after submission unless time allows)**
Today: Amazon (India, Japan, Australia, Singapore, US) and Flipkart work fully. Any other shop works by screenshot, and by pasted link with less detail.
- [ ] Extension on Shopee, Lazada, Rakuten, Myntra, Meesho, Tokopedia: add them to `manifest.json` and read title, price and brand from the shop's schema.org product data. Test on real pages first, because some shops may hide that data or block requests
- [ ] Pasted links from those shops: Shopee, Lazada and Tokopedia build the page with JavaScript, so the server reads little. Read their schema.org data, or open the page in the Research Agent's headless browser
- [ ] Reference prices and photos use only Amazon.in, Amazon.com and Flipkart (`REFERENCE_MARKETPLACES`). Add Amazon.co.jp, .com.au and .sg so non-Indian listings have a same-currency price to compare
- [ ] Change the popup and README wording once more shops are supported

**Nice to have**
- [ ] My Shelf backend (still a mock)
- [ ] "Still on sale" count of recalled products
- [ ] Hand-check the Sunbeam heated-blanket finding before claiming it
- [ ] Accessibility pass (Lighthouse ≥ 95)

---

## Are we on track?
**Mostly yes, with one big risk.**

| Judging area | Weight | Where we stand |
|---|---|---|
| Technical merit and GenAI | 40% | 🟢 Strong: real agents, Gemini 3.x, measured results |
| Problem fit and impact | 25% | 🟢 Good: JAPAC focus, Hindi, real recall data |
| Innovation | 25% | 🟢 Good: copy-finding engine and backtest |
| UX | 10% | 🟡 Extension and chat page redesigned (16 Oct); still at risk until judges have a hosted link |

**The risk:** judges probably won't install a Chrome extension. The web page fixes that once it's deployed. The hackathon notes also warn that overbuilding loses.

**Heads-up:** a check of a real Amazon India link ran for minutes and then dropped. Flipkart and title-only checks answer in under 20 s. Use those in the video until it's looked at.

## Next steps
1. **15 Oct:** commit the Recall Catalog and deploy it
2. **16 Oct (before freeze):** `make deploy-api`, `make web-samples`, `make deploy-web`; connect the WhatsApp number
3. **17 Oct:** no new features. Merge to `main`, record the video, make the deck, submit
