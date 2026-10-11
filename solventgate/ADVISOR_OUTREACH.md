# Finding a pharmacist or QA advisor: outreach kit

**Goal by Oct 12–13:** one person with pharma QA/QC, regulatory or pharmacy experience who will (1) spend 15 minutes sanity-checking SolventGate's logic and (2) record a 20-second quote for the demo video. Ideally also willing to be named as an advisor in the deck.

## Where to look (fastest first)
1. **Your own network:** friends, family or ex-colleagues who studied B.Pharm/M.Pharm or work at any pharma, chemical or food company. Ask in WhatsApp groups: *"Does anyone know someone in pharma QA/QC?"*
2. **LinkedIn search:** filter by location India / Indonesia and search titles **"QA Officer" / "QC Executive" / "Quality Assurance" pharma**, **"Regulatory Affairs"**, **"Drug Inspector" (retired)**, **"Excipient"**. Target Baddi, Ahmedabad, Hyderabad and Mumbai clusters. Send connection notes (message A below).
3. **Pharmacy / pharma-science communities:** IPA (Indian Pharmaceutical Association) state branches, B.Pharm alumni groups, r/pharmacy and r/pharmaindia, pharma QA Telegram/LinkedIn groups.
4. **Academics:** pharmaceutics or pharmaceutical analysis faculty at a nearby pharmacy college. They often reply to well-framed public-health projects.
5. **The hackathon Discord:** ask whether any participant or mentor has pharma QA background.

Send 10–15 messages to get 1–2 replies. Lead with the children's-deaths cases; they make people respond.

## Message A: LinkedIn connection note (under 300 characters)
> Hi [Name], I'm building a Google Cloud AI Builder Cup project to stop DEG/EG-contaminated solvent at a syrup maker's receiving gate (the Coldrif and Indonesia cases). Could I get 15 minutes of your QA view this week? Happy to credit you as advisor.

## Message B: WhatsApp / email (longer)
> Hi [Name],
>
> I'm [Your name], part of team Hashes in the Google Cloud AI Builder Cup 2026 (finale in Singapore).
>
> We're building **SolventGate**, a tool for small syrup manufacturers. At the receiving gate, a QA officer photographs the drum label, the supplier's CoA and the invoice. AI cross-checks them (grade, batch numbers, manufacturer, whether a DEG/EG result is reported, whether the supplier is really a pharma-grade producer). It then puts the batch on **HOLD until the GC test is done**, and generates the quarantine and receiving records. It never says "safe"; it makes sure the test and paperwork actually happen.
>
> We're replaying the Indonesia 2022 forged-label case and the 2025 Coldrif case to show both would have been stopped.
>
> Could you give us **15 minutes this week** to check whether our logic matches how receiving and QC really work? If you're comfortable, a **20-second video quote** would help a lot. We'd credit you as an advisor (or keep you anonymous, your choice).
>
> Thank you!

## The 15-minute call: questions to ask
1. When a drum of PG/glycerin/sorbitol arrives, what happens step by step until it's released? Who signs?
2. What do you check on the label, the CoA and the invoice today? What's most often wrong or missing?
3. Since the 2025 CDSCO order, is every batch DEG/EG-tested in-house, or sent out? How long does it take?
4. Which red flags would make you reject or hold a drum immediately? (Trader vs manufacturer, missing DEG/EG line, mismatched batch numbers, non-pharma grade?)
5. Are we missing any document? (Manufacturer's CoA vs trader's CoA, TSE/BSE declarations, ONDLS entry, GRN?)
6. Does "HOLD + mandatory GC test + audit trail" sound useful, or would a QA officer ignore it? What would make you trust it?
7. What would a Schedule M inspector want to see in the receiving record?

Write down every correction; it goes straight into the rules engine and the deck.

## The 20-second quote: script options (they should use their own words)
- *"I've worked in pharma QA for [N] years. The documents for those poisoned drums existed. Nobody cross-checked them. A tool that forces that check at the gate, and refuses to release without the test, is exactly what small manufacturers need."*
- *"Small units don't have enterprise QMS software. If a QA officer can photograph three documents and get a hold-or-test decision with an audit trail, that closes the gap that killed those children."*

**How to record:** phone, landscape, quiet room, face and shoulders, 15–25 seconds. On-screen caption: name, role and years of experience (or "Pharma QA professional, India" if anonymous).

## Consent (keep it simple and in writing)
Before using their name, face or quote, get a short written OK (a WhatsApp message is fine):
> "I agree that team Hashes may use my video quote and name/title [or: anonymously] in their AI Builder Cup 2026 submission video and deck."

Don't attribute anything to their employer, and don't use the company name unless they explicitly agree.

## If nobody replies by Oct 13
- Use **public expert statements** instead: WHO alerts, CDSCO orders and published QA articles, quoted and cited in the deck.
- Frame the team as: *"We validated our rules against USP/IP monographs, the FDA's 2023 DEG/EG testing guidance and CDSCO's 2025 orders."*
- Or **switch to BatchWatch**, as planned.
