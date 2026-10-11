# Prior-Art Check: "Golden Hour" Scam-Recovery Copilot (BFSI, JAPAC)

Checked on 2026-10-08. Sources: web search (EN, HI, ID, JA), GitHub, Devpost, lablab.ai, Google AI competition, arXiv, vendor and government sites.

## Verdict: PARTIALLY DONE (the India-only victim-side core is crowded and recent)

The victim-side core already exists several times over for India, sometimes under the same name. That core is evidence ingestion, timeline reconstruction, a 1930/NCRP complaint draft, a bank dispute letter and a deadline countdown. A hackathon repo called **"Golden Hour"** (30 Sep to 3 Oct 2026, one week ago) does nearly the whole India flow. **ShieldTrace AI** covers timeline reconstruction, bank dispute letters and 24h/72h countdowns. **Satark-agent** drafts the "golden-hour complaint pack" in more than 11 Indian languages.

I found nothing that combines all of the following in one product:
- **multi-jurisdiction JAPAC routing** across IN, PH, SG and AU at once (the PH AFASA hold, SG SRF eligibility and AU SPF/IDCARE/AFCX routes have no victim-side copilot)
- **the voice note in the victim's language** used as evidence
- **a bank-side console that clusters victim reports by shared beneficiary**
- **the Japan elder pause-and-verify mode**

Each of these exists separately in institutional form (I4C Suspect Registry, AFCX FRX, CICC's Tagalog AI agent, NTT's AI call monitor, GASA's Scam.org country routing). Nobody has put them together, and nobody joins victim intake to the bank's mule intelligence.

**Do not use the name "Golden Hour".** It is already taken by a near-identical repo, and "golden-hour complaint pack" is Satark's tagline.

---

## A. Very close prior art (FULL or near-full overlap with the victim-side core)

| # | Name / URL | What it does | Overlap | Components that overlap |
|---|---|---|---|---|
| 1 | **Golden Hour** (Letusfightcorona) - https://github.com/Letusfightcorona/golden-hour (live: golden-hour-inky.vercel.app) | Hackathon build, 30 Sep to 3 Oct 2026. Gives "calm, multilingual help for people in India right after an online scam". Parses bank/UPI SMS for amount, UTR, UPI ID, bank and time. Claude reads screenshots and free text. Generates a pre-filled 1930 call script in Hindi and English with read-aloud. Includes a cybercrime.gov.in filing pack, a bank dispute letter PDF, a case tracker with deadline math, and RBI Ombudsman and SEBI SCORES escalation. Also runs over a WhatsApp (Twilio) channel. 6 commits. | **FULL for India victim side** | Same name, evidence extraction, 1930/NCRP routing, bank letter, deadline countdown, Hindi/Hinglish |
| 2 | **ShieldTrace AI**: AI-Powered Financial Scam Recovery Evidence Assistant - https://github.com/Limitha1/AI-Powered-Financial-Scam-Recovery-Evidence-Assistant (mirror: github.com/sharathbk910/LimitProject) | Ingests screenshots, PDFs, SMS and WhatsApp/Telegram chats. Gemini 2.5 extracts UTR/RRN and beneficiary VPA. Reconstructs the timeline in stages (FIRST_CONTACT, MANIPULATION, DEBIT, DISCOVERY and so on). Generates a bank dispute letter citing the RBI zero-liability circular plus a cybercrime police brief. Has **countdown timers for the 24h/72h windows**, client-side PII redaction and PDF export. | **FULL for India victim side** | Evidence upload, timeline, scam classification, police and bank letters, countdown |
| 3 | **Satark-agent** - https://github.com/BhuvanT1/satark-agent | A "cyber-fraud first-responder agent" that drafts the "golden-hour complaint pack in Indian languages" (11+). Its recovery planner computes golden-hour status, the RBI liability class, deadlines in working days and e-Zero FIR applicability. It places the victim on a 7-stage scam lifecycle. Outputs a JSON case file meant for banks, telcos and helplines. | **Near-full (India)** | Golden-hour framing, classification, complaint drafting, deadlines, multilingual |
| 4 | **Unscammed AI** - https://unscammed.com | Commercial startup live in the **US, UK and Australia**. AI prepares structured reports and files them for the victim with banks, police, FBI IC3 and FTC "in under 8 minutes". Users say it auto-fills the bank dispute and the IC3 filing. Reporting is free. Claims more than 1,000 customers and more than $3M in scams reported. | **Partial-to-full (commercial, includes AU)** | Report drafting, bank dispute, multi-authority submission. No JAPAC-Asia coverage, mule console, voice or countdown documented |

## B. Partial overlap: government and institutional

| Name / URL | What it does | Overlap | Components |
|---|---|---|---|
| **CICCAI "Sikay"** (Philippines CICC + Proto, Gates Foundation funding) - https://proto.cx/case-study/cicc-scales-national-scam-reporting-with-proto-ai-agent/ | AI agent in Filipino, Tagalog and English on the website, Facebook and the 1326 hotline. Takes structured intake (incident, channel, identifiers, evidence), auto-categorises reports, routes them, and hands off across agencies to BSP and SEC. Interactions rose 838% in one quarter. | Partial | Tagalog intake, classification, routing. No AFASA hold request drafting, timeline or countdown |
| **GASA Scam.org** (with OpenAI, ScamAdviser), launched 2026-03-12 - https://gasa.org/knowledge-base/blog/global-anti-scam-alliance-launches-scam.org-with-openai-and-key-partners | Global AI hub in 50+ languages that checks scams, provides victim support and **directs victims to the right reporting channel in their country and language**. Streamlined reporting is "rolling out". | Partial | Multi-country routing and multilingual. No evidence ingestion, drafting, countdown or bank console |
| **India 1930 / NCRP AI modernisation** - https://easemyprep.in/news/2219-amit-shah-reviews-national-cyber-crime-helpline-1930-orders-ai-based-modernizati ; Bihar's AI 1930 call centre (Drishti, 29 May 2026) | MHA has ordered AI for faster complaint registration, routing and classification. Bihar's AI call centre aims to cut registration from 16-18 minutes to 5-6 minutes. | Partial (in progress, government side) | Intake and classification |
| **I4C Suspect Registry / Samanvaya** (India) | Shares mule accounts from complaints with banks: 26.48 lakh Layer-1 mules by Dec 2025, with ₹9,055 crore declined. | Partial | **The bank-side mule clustering idea already exists institutionally in India** |
| **AFCX Fraud Reporting Exchange (FRX)** and **Intel Loop** (Australia) - https://ausbanking.org.au/australian-banks-join-new-fraud-reporting-exchange-digital-platform-to-help-halt-payments-to-scammers | Near-real-time interbank scam-payment reporting for freezing and recovery. Intel Loop shares scam intelligence with platforms. | Partial | Bank-side shared-beneficiary intel and recovery window |
| **Malaysia NSRC 997 + Semak Mule (PDRM CCID)** | Real-time scam response hotline and a public mule-account lookup. | Partial | Mule lookup, rapid freeze |
| **Thailand AOC 1441** - https://www.mdes.go.th/AOC1441/En | Hotline for account suspension requests, linked to Thaipoliceonline to generate a police case ID. | Partial | Routing, freeze. No AI copilot |
| **Indonesia IASC (OJK)** and its forthcoming "Indonesia Anti-Scam" app | Receives victim reports through banks (579k reports to May 2026) and blocks accounts. | Partial | Reporting, mule blocking |
| **Singapore ScamShield Suite** (app, 1799 helpline, WhatsApp bot) - https://guide.scamshield.gov.sg/introduction/help-ive-been-scammed | Reports scam messages and calls to SPF and directs victims to their bank. States explicitly that **ScamShield reports are not police reports**; victims must file separately through SPF e-services. No SRF claim helper found. | Partial (prevention-heavy) | Reporting, bank direction |
| **IDCARE** (AU/NZ) - https://idcare.org | Human case managers with more than 1,000 response plans. No AI copilot found. | Partial | Post-incident response plans |
| **OCBC Kill Switch**, Revolut in-app scam intervention and In-App calls | Victim self-freezes accounts. Chat with a fraud specialist. | Low | Containment only |
| **NTT East/West special-fraud AI call adapter** (Japan) | Records landline calls, flags special fraud with AI and alerts family. **Truecaller Family Protection** (Mar 2026) lets family hang up scam calls for a relative. | Partial (for the Japan elder mode) | Elder pause/verify, family alerting |
| **The Cyber Helpline** (UK) - https://thecyberhelpline.com | Chatbot that diagnoses cyber-attacks from the victim's description, plus volunteer experts. | Partial (UK) | Victim triage chatbot |

## C. Partial overlap: vendors and consumer apps

| Name | What it does | Overlap |
|---|---|---|
| Whoscall / Gogolook (TW, PH, TH, JP, MY, KR) | Caller ID, community scam reports, Web Checker, image "Check", missions and badges | Low. Prevention and reporting only, no recovery copilot |
| Trend Micro ScamCheck / Scam Radar | Verifies messages and links, detects scam journeys early. Recovery advice is generic blog content | Low |
| Truecaller Scamfeed | Community scam feed (India) | Low |
| Scamnetic, InfoHawk, Apate.AI, Savi (funded 2025-26) | Detection, prevention, scam-baiting | None for post-scam recovery |
| BioCatch, Feedzai (e.g. BigPay mule network), Bureau.id, FaceID link analysis | Bank-side mule-network detection with graph clustering on device, identity and beneficiary signals | Partial for the bank console. Mature commercial market, but driven by transaction and device data rather than victim-report clustering |
| Chainalysis, TRM Chainabuse, "Cryptera Chain Signals" (Product Hunt) | Crypto tracing and victim reports for pig-butchering cases. Recovery is mostly done by law enforcement or exchanges | Partial for the crypto branch. Note that the "recovery service" space is full of recovery scams |
| Hacked.com "Scammed" | Creates "Scam Incident Records" and organised evidence summaries for police and fraud reports | Partial (Western) |

## D. Hackathon projects

| Name / URL | What it does | Overlap |
|---|---|---|
| Golden Hour (see A1). Hackathon build, 30 Sep to 3 Oct 2026 | | FULL (India) |
| **ScamTrap** (ForgeHacks 2026) - https://github.com/arunthathiB15/ScamTrap | Scam detector plus a **complaint draft for cybercrime.gov.in/1930**, and a decoy agent that extracts UPI IDs, IFSC and accounts from the scammer | Partial |
| **Scammune** (Google Gemini API Developer Competition) - https://ai.google.dev/competition/projects/scammune | Detects scams, then gives post-loss remediation steps (helpline, what data to prepare). India | Partial |
| **SOS-AI** (lablab.ai Langflow hackathon) - https://lablab.ai/event/langflow-hackathon/avjo | Automates 1930 helpline support and simplifies complaint filing. India | Partial |
| **Scamoorai** (DBS / Singapore Courts / NCPC Hackathon for a Better World 2022) - judiciary.gov.sg | Builds on ScamShield with easy victim reporting and a chatbot | Partial (SG) |
| **IndiaAI CyberGuard AI Hackathon** - https://indiaai.gov.in/article/indiaai-launches-cyberguard-ai-cybercrime-prevention-hackathon | Government challenge: NLP to classify citizen-reported NCRP complaints | Partial (classification) |
| SIH 2025 SIH1516 / SIH1700 | Multilingual grievance and justice chatbots that support victims | Low |
| Devpost: ScamShield AI, IsThisAScam, Scam Map, AI Scam & Fraud Risk Analyzer, ElderSafe (has a "what to do if scammed / recover" guide) | Mostly detection | Low |
| **CyberSahayak / CyberShield-AI** (B.Tech course project) - https://github.com/spsneh07/CyberSahayak | Complaint drafting with placeholders, SHA-256 evidence integrity kit, English and Hindi, 21 categories | Partial |
| **Satark** (Dhwanitisshah) - https://github.com/Dhwanitisshah/satark | Scam checker in EN, HI and MR. Routes money-lost cases to 1930 and NCRP | Low-partial |
| UpayShield (Bangladesh) - https://github.com/Pro-seka/Upay_Cloak | Graph mule-network detection and a pre-transaction nudge in Bangla. No recovery | Partial (bank console) |
| Kolaxus AI Anti-Scam Hackathon 2026 (MY) | Ideas-only student challenge with no recovery track | None |

## E. Academic

| Paper | Relevance |
|---|---|
| Wen et al., "Forensic Schema for Psychological Manipulation in Cyber Fraud: LLM-Driven Victim Reports Analysis", arXiv:2607.07751 | LLM annotation of 10,994 victim reports. **Recommends AI-assisted victim intake with schema-informed follow-up questions** and finds that victim narratives lack actionable detail. Supports the problem, not a competing product |
| SeniorSafeAI (USF 2026) | LLM chatbot giving fraud guidance to older adults, evaluated on 589 QA pairs. Partial for the elder angle |
| ScamPilot (CHI 2026) | LLM conversation simulation for prevention training |
| "Distinguishing Scams and Fraud with Ensemble Learning", arXiv:2412.08680 | LLM classification of complaints |
| "Love, Lies, and Language Models", USENIX Sec '26 (arXiv:2512.16280) | Shows LLMs are used inside pig-butchering operations. Useful context |

Japanese search (詐欺 被害 AI 相談 返金) found no AI post-victim recovery copilot. Sources only advise asking an AI for a question list and then calling 188 or #9110, or seeing a lawyer. The 振り込め詐欺救済法 account-freeze and refund-distribution process has no AI copilot that I found.

---

## What remains genuinely novel

1. **One case object routed across several JAPAC countries.** Every prior build is single-country, mostly India. Nobody drafts a **PH AFASA disputed-funds hold request** (5 days plus 25), an **SG SRF eligibility check** (phishing-only scope, duties waterfall), an **AU SPF / IDCARE / ReportCyber** pack, or a **TH AOC 1441 / ID IASC / MY NSRC 997** pack. Cross-border cases fit this well: a Filipino worker in Singapore, or an Indian victim paying into a Thai mule.
2. **Voice notes in Tagalog, Thai or Bahasa as evidence.** Prior builds take SMS and screenshots, and Golden Hour reads its script aloud. None turns a native-language voice narrative into a structured timeline plus a complaint in the authority's language.
3. **A closed loop from victim intake to the bank's mule console.** Banks cluster mules from transaction and device data (BioCatch, Feedzai), and I4C/AFCX share registries. No consumer copilot sends structured, consented victim reports into a bank-side shared-beneficiary cluster view with SLA timers on hold requests. This is the strongest BFSI angle.
4. **Per-jurisdiction recovery-window clocks.** Golden Hour, ShieldTrace and Satark compute Indian RBI deadlines only. A clock engine per jurisdiction is new: AFASA 30 days, RBI 3 and 7 working days, SG SRF reporting, AU 24h bank notification.
5. **Japan elder "pause and verify" voice mode.** Prevention-side analogues exist (NTT adapter, Truecaller Family), but none is tied to a recovery copilot.

## Pitch differentiation guidance

- **Rename it.** "Golden Hour" is taken by an almost identical repo from last week, and Satark uses "golden-hour complaint pack".
- **Do not pitch "AI drafts your 1930 complaint and bank letter"** as the novelty. Judges searching GitHub will find at least three identical builds. Treat it as table stakes.
- **Lead with B2B2C for banks.** The bank embeds the copilot in its app. Every victim intake becomes a structured, deduplicated case that feeds the bank's mule-cluster console, with AFASA/SRF/SPF obligations tracked. That ties into the regulatory liability pressure on banks: SPF fines up to AU$50M, SRF waterfall liability, AFASA duties.
- **Lead with multi-country, multilingual voice** (Tagalog, Thai, Bahasa, Hindi), with the scam timeline built from a voice note.
- **Be honest about recovery.** Recovery scams are rampant (FBI IC3 warnings, OpenAI takedowns of fake "law firm" recovery operations). Build in "we never ask for fees, we only file with official channels" as a trust feature.
- **Position against Scam.org.** Scam.org routes victims, while this product files the case and tracks the clocks. Unscammed covers the US, UK and AU and is not built for Asian rails (UPI, PayNow, InstaPay, PromptPay).

## Key sources
- https://github.com/Letusfightcorona/golden-hour
- https://github.com/Limitha1/AI-Powered-Financial-Scam-Recovery-Evidence-Assistant
- https://github.com/BhuvanT1/satark-agent
- https://unscammed.com ; https://ch.trustpilot.com/review/unscammed.com
- https://proto.cx/case-study/cicc-scales-national-scam-reporting-with-proto-ai-agent/
- https://gasa.org/knowledge-base/blog/global-anti-scam-alliance-launches-scam.org-with-openai-and-key-partners
- https://github.com/arunthathiB15/ScamTrap ; https://github.com/spsneh07/CyberSahayak ; https://github.com/Dhwanitisshah/satark
- https://ai.google.dev/competition/projects/scammune ; https://lablab.ai/event/langflow-hackathon/avjo
- https://guide.scamshield.gov.sg/introduction/help-ive-been-scammed
- https://ausbanking.org.au/australian-banks-join-new-fraud-reporting-exchange-digital-platform-to-help-halt-payments-to-scammers
- https://www.respicio.ph/commentaries/how-to-recover-money-from-online-scams-paid-through-digital-wallets-or-e-wallets-in-the-philippines (AFASA 5+25-day hold)
- https://arxiv.org/abs/2607.07751
- https://www.mdes.go.th/AOC1441/En
- https://www.biocatch.com/press-release/more-than-150000-money-laundering-accounts-detected-in-apac
