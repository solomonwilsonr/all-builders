# SafeShelf: social impact and awareness plan

Status: **planned, not started.** Pick this up once the core setup is complete (after submission on 17–18 Oct, or earlier if a step is cheap). Every number we publish must come from our own data and must follow the identity rule: **only an exact model inherits a recall; a possible rebrand goes to a human; a look-alike never does.**

Why it matters for the cup: "Problem alignment & impact" is 25% of the score, and there are $2k prizes for **Most Impactful** and **Social Choice**. The Top 50 shortlist is 7 Nov and the finale is 4 Dec, so Steps 1–3 can still strengthen the story after submission.

Recommended order: **1 and 3 first. Both are now scheduled for Day 5 (16 Oct) in `plan.md` §17, before submission.** Step 1 gives one measured headline number; Step 3 gives one memorable person and moment. Both use only what is already built.

---

## 1. "Still on sale" public report

**Idea.** The OECD found 87% of banned or recalled products still on sale online. We measure the same thing on our own catalog: how many recalled products still have exact-model or rebranded copies listed under other brand names.

**Uses.** `recalls`, `recall_products.match_class`, `product_relationships` (`exact_model`, `rebranded_equivalent`), `listings`.

**Steps**
- [ ] Script `bench/still_on_sale.py`: for each recall, count linked products by class: exact model (counts), rebranded equivalent (counts as "needs review", never as recalled), visually similar (excluded)
- [ ] Only count `product_relationships.status = 'verified'` as confirmed; report unverified links separately
- [ ] Hand-check a sample (at least 20 rows) before publishing; record the precision
- [ ] Output: one table + one headline sentence, e.g. "X of 2,537 recalls have Y exact copies still listed; Z more possible rebrands await review"
- [ ] One-page summary (method, limits, numbers) for the deck and for journalists and consumer groups

**Done when** the headline number is reproducible with one command and every counted row has evidence IDs.

## 2. Child-safety focus

**Idea.** Button batteries, magnets, infant sleepers, crib bumpers and baby walkers are where a missed recall harms children. One filtered view turns the general tool into a clear campaign.

**Steps**
- [ ] Tag recalls and hazard signals by child-product category (keywords + Gemini classification, checked by hand)
- [ ] Lab / web view: "Children's products: recalls and early hazard signals"
- [ ] WhatsApp prompt: "Is this safe for my baby?" routes to the same check with a child-safety summary
- [ ] One real case (parent, product, what SafeShelf found) for the video or deck

## 3. Recall alerts for people who never see recall notices

**Idea.** Recall notices are English web pages. Our WhatsApp bot already answers in Hindi with a voice note. Present it as recall alerts for low-literacy, older and rural shoppers on low-cost phones.

**Steps**
- [ ] Connect the WhatsApp bot to a Meta test number (already built and tested; see `whatsapp/`)
- [ ] Hero moment for the deck/video: a family member sends a product photo, gets a Hindi voice note that it matches a recall, with what to do next
- [ ] Add more languages after Hindi (Tamil, Bengali, Marathi) via Gemini TTS
- [ ] Opt-in "watch this product" alerts after purchase (ties to My Shelf)

## 4. Fake ISI mark awareness (India)

**Idea.** BIS seized 3,500+ items with fake or missing ISI marks from Amazon and Flipkart warehouses. "Check the ISI number before you buy" is a simple, India-specific message backed by our safety-mark check.

**Steps**
- [ ] Short explainer card in the extension and WhatsApp: what an ISI / R-number is, how SafeShelf checks it
- [ ] Count mark mismatches in our Amazon.in / Flipkart products (`certifications.validation_status = 'mismatch'`) for a measured number

## 5. Partnerships (deck: future plans, not claims)

Do not name any partner as a partner until they agree. Until then, list them as "who we plan to approach".

| Who | Region | What we offer them |
|---|---|---|
| Consumer VOICE, CUTS International | India | Free analyst dashboard, evidence packs, ISI mismatch findings |
| CHOICE | Australia | Recall + energy-registry mismatch findings |
| Kids In Danger | US | Child-product recall copies still on sale |
| CPSC, ACCC, BIS | Regulators | Early-signal reports, always after human review, never automatic |

**Steps**
- [ ] One-page outreach note per group with the Step 1 numbers
- [ ] Send the confirmed real-world finding to the regulator form (already planned for 17 Oct in `plan.md` §17)

## 6. Open data and a free public tier

**Idea.** Free for good, paid for business: shoppers, NGOs, researchers and regulators use SafeShelf free; marketplaces and brands pay for Catalog Scan. This makes the impact story believable.

**Steps**
- [ ] Release the verified twin/rebrand links and early-warning signals as an open dataset (licence check on each source first: CPSC and the AU registry are public; review text is not ours to republish, so release IDs and derived labels only)
- [ ] Free rate-limited MCP tier so other AI shopping agents can check safety
- [ ] Pricing slide: free tier vs Catalog Scan

## 7. Community early-warning network

**Idea.** The extension's "Report a hazard" form feeds the same evidence pool across rebranded twins. Each report helps every copy of the product.

**Steps**
- [ ] Show on the product card: "N shopper reports across all versions of this product"
- [ ] Reports enter `hazard_signals` as `under_review`; a human confirms before anything is shown as a warning
- [ ] Keep `reports.reporter_ref` hashed; never store raw identity

## 8. "Check before you gift" campaign

**Idea.** Diwali (late Oct to mid Nov) brings a spike in cheap electronics, lights and toys bought online, and it overlaps the 7 Nov shortlist.

**Steps**
- [ ] Short social post + WhatsApp share card: "Send us the link before you buy"
- [ ] Track checks run during the campaign as a usage number for the finale

## 9. SafeSwap: goodies and T-shirts that fund safe replacements

**Idea.** A small shop of T-shirts and goodies. All profit (after making and shipping costs, which we publish) funds **SafeSwap**: we replace a fake or uncertified charger, extension board or heater in a low-income household with a certified one, and teach the family to check before buying. The money goes to the same problem SafeShelf solves, so the shop matches the product.

**What makes it ours**
- **Every item has its own SafeShelf passport.** A QR tag on each item opens its record: who made it, fabric and print certifications, the safety-mark check, what it cost to make, and which swap it paid for. The shop is a live demo of SafeShelf.
- **A public impact ledger.** One page shows money in, costs, swaps funded, and households and districts reached. Measured numbers only, like everything else we publish.
- **The goodies spread the message too.** Each sticker and tote carries the WhatsApp bot QR: "Send a link or photo before you buy."
- **Buy one, give one.** Every second T-shirt goes to a community health worker (for example an ASHA worker) or NGO volunteer who runs check-before-you-buy sessions with the WhatsApp bot.

**What to sell**
| Item | Design / message |
|---|---|
| T-shirt | "Is it safe? Is it real?" · "Exact model only" · Hindi: "पहले जांचो, फिर खरीदो" (check first, then buy) |
| Stickers / laptop decals | WhatsApp bot QR + "Check before you buy" |
| Tote bag | "I check before I buy" |
| Phone grip / card holder | Bot QR, for shoppers who need it at the moment they buy |
| Diwali gift card | Pairs with Step 8: "This gift was checked by SafeShelf" |

**Practice what we preach (hard rules)**
- No small magnets, button batteries or loose small parts in any goodie. Those are the child hazards SafeShelf warns about.
- Only certified suppliers. Every item gets its own passport before it goes on sale.
- Say "all profit after costs", never "every rupee", and publish the cost breakdown.

**How to run it without handling money ourselves**
- Print-on-demand (e.g. Qikink in India, Printful/Printify internationally), so there is no stock to buy up front.
- Profits go straight to a registered partner NGO (Section 5), which issues donation receipts (80G in India). We do not collect donations as a team.
- The NGO buys the replacement products and runs the swap visits. We supply the check (which items are fake or uncertified) and the passports.

**Steps**
- [ ] Agree a partner NGO and the swap process (what gets replaced, who visits, how a swap is recorded)
- [ ] 3–4 designs, plus a mock-up for the deck's impact slide ("future: SafeSwap")
- [ ] Set up a print-on-demand store; check supplier certifications through SafeShelf
- [ ] Shop page on the web Lab: items, passport QR demo, impact ledger
- [ ] Track swaps in a `swaps` table (household region only, no personal data) to feed the ledger
- [ ] Launch alongside the Diwali campaign (Step 8)

**Other ways to fund SafeSwap** (if merch is too slow to start): a "sponsor a swap" button (fixed price per household), corporate CSR sponsorship of safety-check camps, or listing SafeSwap as a cause on Give India / Milaap through the partner NGO.

---

## Rules for anything we publish

- Measured numbers only, with the method and limits stated next to them.
- Exact-model matches only are called "recalled". Rebrands are "possible, under review".
- No seller or brand is named as unsafe without a human check of the evidence.
- No raw reviewer or reporter identity anywhere.
