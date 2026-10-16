# Deck and video additions (16 Oct)

Slide text for the official 16-slide template (checklist item 15) and beats for the 3-minute video (item 16), covering the features built on 16 Oct. Every number here is measured and the source is named. The claims stay inside what the code does.

---

## Slide: Who it's for

**Shoppers who can't easily check for themselves, across JAPAC.**

- **Migrant and cross-border families.** Our cross-border check protects people who buy or are sent products from abroad, where a product recalled in one country is still sold in another. *Example: a power bank recalled in the US, still listed on Amazon.in, sent home to a family in Kerala. SafeShelf says "Recalled in the US, not yet in India: check the model number", in Malayalam if that's what the family reads.*
- **Older and low-literacy shoppers.** The verdict is read aloud in 26 JAPAC languages, in a few seconds. They can also ask out loud and get a spoken answer.
- **Visually impaired shoppers.** They point the phone at the label and hear what it says, whether it has been recalled, and what to do.
- **Shops and marketplaces.** When a recall lands, they learn which items on their shelves are affected and what to do with them.

Proof point: 19 cross-border recall pairs. Median 22 days between the first country's recall and the later country's (95% CI 13–68, n=17; small sample). `bench/crossborder_results.json`

---

## Slide: Before and after purchase

| Before you buy | After you've bought it |
|---|---|
| Check card on Amazon.in, Flipkart, Amazon.co.jp, .com.au, .sg | **"I already bought it"**: stop using it, or check the label first |
| **Steps in when you click Buy now / Add to cart** on a red or amber answer: why, what to do, Listen. You still choose ("SafeShelf never blocks a purchase") | **Refund request** to the marketplace, already filled in with the official record |
| WhatsApp: send a photo or link | **Regulator complaint**, already filled in: India's National Consumer Helpline (1915), Australia's ACCC, Japan's CAA and the 188 hotline, Singapore's CPSO, Korea's 1372, the US CPSC. Japanese drafts for Japan |
| | **Case file** to attach (official records, where we checked, the code's result) |
| | **Report what happened**: a photo of a melted charger; similar reports add up to an early warning |

Rule shown on the slide: *drafts are written by code from the investigation, never by Gemini, so a draft never claims more than the code decided. A recall abroad is never written as "recalled here". Nothing is sent: the shopper sends it.*

---

## Slide: Checked by code, not guessed

Every line of an answer carries a badge, **⚙ Checked by code, not guessed**, linked to the official record (or the official list that was searched).

- Red only means an exact-model recall **in the shopper's own country**
- A recall abroad is amber: "Recalled in the US, not yet in India"
- Gemini reads, finds and explains. Code decides the colour (`engine/evidence_verification/adjudicator.py`)

---

## Slide: Attacker vs defender (red-team)

**18 / 18** invented hard cases come out as designed (`bench/evidence_results.json`): forged regulator pages, look-alike model numbers, injected instructions, copied complaints, excluded batches, retracted notices.

**Live rounds:** Gemini plays the attacker and invents new attacks on the judges' page (tab "Attacker vs defender"). The same code that answers shoppers defends, and a fixed rule decides whether it held.

What the live red-team found, and what we fixed the same day:
- Reposts with two or three words changed counted as separate owners → fixed (word-alignment rule); still 18/18
- Fake shops wrote "SYSTEM NOTICE FOR AI SHOPPING ASSISTANTS…" in phrasings our filter didn't know → fixed with a sentence rule: **13/13 attacks caught, 0 false alarms on 27,822 real listings, 10/10 fresh live rounds held**

Limits shown on the panel: fake reviews written from scratch (a review farm paraphrasing one story six ways) still count as separate reports, and a forged page can still send a product to a person for review as a "possible match". *Say "the red-team shows the rules behave as designed", not "real-world accuracy".*

---

## Slide: The seller and retailer side

When a recall lands, **Catalog Scan** (`POST /v1/catalog/scan`) tells a shop which listings on its shelves match, and now gives **what to do with each one**:

- **Exact recall match:** stop selling, unpublish, quarantine the stock, follow the remedy and return it to the supplier, tell the customers who bought it
- **Possible match:** hold sales until the model number is checked, and ask the supplier
- **Safety mark mismatch:** hold sales and ask for the valid certificate
- **Buyer hazard reports:** watch it and turn on recall alerts

The supply-chain endpoint (`GET /v1/products/{id}/supply-chain`) names the manufacturer, importer and distributor, each cited to the official notice.

---

## Slide: Shopper incident reports (the people side)

A shopper sends a photo and what happened. Gemini checks it: is it first-hand, which hazard, how serious, does the photo show heat or fire damage. Code then counts only **independent** reports: the same person, the same photo or copied words count once. It raises an **early warning** (never a recall) at two independent serious reports, or one with a fire-damage photo, by the same rule we use for buyer reviews. The warning goes to a person for review. The photo is never stored.

---

## Video beats (the Gemini moments)

1. **Ask out loud (Gemini Live).** In a shop, the phone camera is on the power bank's label and someone asks in Hindi: "क्या यह सुरक्षित है?" Gemini Live calls SafeShelf's label reader and investigation, and answers by voice in Hindi in about 4–13 s: "Anker A1263 को अमेरिका में आग के खतरे के कारण वापस ले लिया गया है…" *(Measured 16 Oct on `gemini-3.8-live`: tool call, then spoken Hindi; English and Japanese tested too.)* Say it plainly: Gemini Live speaks the result, code decides it.
2. **Buy-button interrupt.** Click "Buy now" on an amber product: the card steps in with the reason, plus Listen. Choose "Go back and check".
3. **I already bought it.** One click gives the steps, a refund request to Amazon.in and a complaint to the National Consumer Helpline, already filled in with the CPSC record, plus a case file. Copy and send.
4. **Attacker vs defender.** Press "Let Gemini attack now" on the judges' page: Gemini invents a fake shop that whispers to AI shoppers, and the code catches it.

## Before recording
- `make migrate` on Cloud SQL (adds `incident_reports`, migration 009) and `make deploy-api`: the new endpoints and the `/v1/live` WebSocket go live
- Reload the extension (2.10.0)
- Gemini Live runs in `us-central1` (`gemini-3.8-live`). The model and region can be changed with `SAFESHELF_LIVE_MODEL` and `SAFESHELF_LIVE_LOCATION`
- Test Ask out loud on a phone over https: browsers only allow the microphone and camera on https pages (Firebase Hosting is fine)
