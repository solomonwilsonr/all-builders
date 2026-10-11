# AI Builder Cup 2026 — Google Cloud JAPAC Hackathon

Source: https://aibuildercup.com/ (pulled 2026-10-07) · Operator: Hack2skill · Sponsor: Google Cloud

## Timeline
| Phase | Dates |
|---|---|
| Registration | Sep 1 – **Oct 11, 2026** (closed; we are registered) |
| Team formation | Sep 1 – **Oct 14, 2026** (extended from Oct 11) |
| Prototype building & submission | Sep 7 – **Oct 18, 2026** (submission deadline) |
| Evaluation (scoring round → shortlist) | Oct 19 – Nov 6, 2026 |
| Finalists announced | Nov 7, 2026 |
| **Top 50 teams shortlist announced** | Nov 7, 2026, 11:00 AM IST |
| Mentorship Week with Google Experts (likely for the Top 50) | Nov 10 – Nov 30, 2026 |
| Grand Finale / Demo Day (in person) | Dec 4, 2026, Singapore (9 AM – 5 PM) |

All deadlines are **11:59 PM IST**. Source: the Hack2skill dashboard roadmap, seen 2026-10-10. Our team: **Hashes**, 2 members: **Seshu Madhavan (team leader)** and Solomon Wilson R. The dashboard banner says teams need at least 2 members to be eligible to submit. Theme to choose on submission: **Retail & Commerce** (SafeShelf). Dashboard checked 2026-10-12.


## How many will submit (our estimate, 2026-10-12)
No official numbers have been published; this is our estimate and could be off by 2x.
- **Unteamed pool:** the dashboard's "Explore Public Profile" list has 1,927 pages of 10 people, so about **19,262 people are still looking for a team**. Registered teams are not in this list.
- **Total registered:** about **40,000–60,000**, assuming the pool is a third to a half of everyone.
- **Teams:** about **7,000–13,000**, assuming 50–60% of people join teams of about 2.7.
- **Submissions:** about **1,000–2,000**, assuming 10–20% submit; central guess **1,200–1,500**. A deployed app, video and deck is a high bar.
- **Retail:** about **13%** of public entries, so **~150–250 Retail submissions**, of which perhaps 30–50 are polished.
- **Top 50 shortlist:** covers all themes, so it is the top ~3–5% overall. Retail might get ~6–8 places.
- **To check:** rescan GitHub on Oct 17–18, when repos must go public, and ask on Discord.

## Eligibility
- Working professionals, entrepreneurs, startups only. **No students**; one student on the team disqualifies the whole team, even after selection.
- Age 21+, and every member must be based in JAPAC. Teams that span JAPAC countries are allowed.
- Team of 2–4. No solo submissions, though you can register solo and find a team later.
- One team per person. Each team submits one solution under one theme.
- **Fresh projects only.** Nothing started before the program launch.
- Free to enter.

## Themes (pick one; official wording)
Suggested directions and technologies come from the Challenges tab on the Hack2skill participant dashboard.
Every team builds against exactly one of these themes.

### 1. BFSI: Intelligent Risk, Fraud & Financial Experiences
Build an AI-powered solution that addresses meaningful challenges across banking, financial services, insurance, or related industries. Solutions may focus on detecting and mitigating fraud or risk, automating complex processes, improving customer interactions, or delivering more personalized and informed financial experiences.

**Suggested solution directions:** Fraud detection, transaction anomaly analysis, document intelligence, financial assistance, personalized recommendations, compliance automation, risk assessment

**Suggested Google Cloud technologies:** Gemini on Vertex AI for reasoning and conversational experiences, BigQuery for transaction and risk analytics, Vertex AI for predictive or classification models, Document AI for financial and non-traditional documents, Vertex AI Search / Agent Search for policy and knowledge retrieval, Cloud Run for application services, Cloud SQL or AlloyDB for application data, Pub/Sub for event-driven transaction processing

### 2. Retail & Commerce: Intelligent Customer and Business Experiences
Build an AI-powered solution that transforms how businesses understand, engage, and serve customers while improving operational efficiency across physical and digital commerce. Solutions may address discovery, personalization, conversational shopping, demand planning, inventory, customer insights, or fraud.

**Suggested solution directions:** Hyper-personalization, conversational commerce, product discovery, demand forecasting, basket analysis, customer segmentation, inventory intelligence

**Suggested Google Cloud technologies:** Gemini on Vertex AI, Vertex AI Search / Agent Search for intelligent product and information discovery, BigQuery for customer and transaction analytics, BigQuery AI for AI-assisted analysis, Cloud Run for commerce applications and APIs, Cloud Storage for product assets, AlloyDB or Cloud SQL for operational data, Looker for business insights

### 3. Manufacturing: Intelligent Operations & Industrial Efficiency
Build an AI-powered solution that addresses challenges related to efficiency, quality, reliability, supply and demand, or sustainability across manufacturing and industrial operations. Solutions should demonstrate how AI can transform operational data into meaningful insights, recommendations, or actions.

**Suggested solution directions:** Predictive maintenance, visual quality inspection, production optimization, supply-chain intelligence, demand forecasting, waste reduction, operational copilots

**Suggested Google Cloud technologies:** Gemini on Vertex AI for reasoning and operational assistance, Vertex AI for predictive and machine-learning workloads, BigQuery for sensor and operational data analysis, Cloud Storage for images, sensor data, and files, Vision AI or image/video analysis capabilities where relevant, Pub/Sub for streaming or event-driven data, Dataflow for data pipelines, Cloud Run for application and processing services

### 4. Media, Content & Digital Experiences
Build an AI-powered solution that transforms how content is created, discovered, personalized, understood, or experienced. Solutions may address challenges across media, entertainment, publishing, education, communication, or other digital content ecosystems.

**Suggested solution directions / technologies:** _not captured yet (no screenshot of this modal)._

### 5. Future of Work & Enterprise Productivity
Build an AI-powered solution that transforms how individuals and organizations access knowledge, collaborate, make decisions, and complete everyday work. Solutions should demonstrate meaningful improvements in productivity, efficiency, knowledge accessibility, or workflow execution.

**Suggested solution directions:** Enterprise knowledge assistants, AI copilots, document intelligence, meeting intelligence, workflow automation, research assistants, intelligent search

**Suggested Google Cloud technologies:** Gemini on Vertex AI, Vertex AI Search / Agent Search for enterprise search and knowledge retrieval, Document AI for document processing, Vertex AI Agent Engine and ADK for agentic workflows, Cloud Run for application deployment, BigQuery for enterprise data analysis, AlloyDB or Firestore for application and contextual data

### 6. Sustainability & Social Impact
Build an AI-powered solution that addresses a meaningful environmental or societal challenge. Solutions may focus on improving resource efficiency, increasing accessibility, strengthening resilience, supporting communities, or enabling more informed and sustainable decision-making.

**Suggested solution directions:** Climate and environmental intelligence, disaster preparedness, sustainable agriculture, resource optimization, accessibility, community services, waste reduction

**Suggested Google Cloud technologies:** Gemini on Vertex AI for reasoning and natural-language interfaces, BigQuery for analysing large environmental or social datasets, Vertex AI for predictive models, Earth Engine for geospatial and environmental analysis where applicable, Cloud Storage for datasets and imagery, Vision AI or image analysis capabilities, Cloud Run for deploying applications, Pub/Sub for event-driven alerts or workflows

> Organizers say the goal is "a functional solution that demonstrates a clear idea in action—not just a pitch deck or a mockup." Online sessions will walk through the problem statements.

## Required tech stack
- **Models:** Gemini or Gemma family
- **Agentic platform:** Agent Platform, Antigravity, or AI Studio
- **Deployment:** Google Cloud, via Cloud Run or Firebase
- Solutions built mainly on other clouds are ineligible.

## Submission
- Working **deployed link**, with the prototype running end to end on Cloud Run/GCP/Firebase
- **Public GitHub repo**
- **Demo video, 3 min max** (YouTube, Vimeo or Google Drive)
- **Deck or PDF proposal** that explains the solution, its impact and feasibility
- Name your theme clearly. Everything must be in English.

## Judging (the same for all themes)
**Technical Merit & Gen AI Implementation (40%)**
- *Meaningful use of Gen AI:* does Gen AI directly contribute to solving the problem?
- *Technical implementation:* is the solution functional, sound and appropriately implemented?
- *Scalability & sustainability:* can it be adopted more widely and developed beyond the prototype?

**Problem Alignment & Impact (25%)**
- *Problem alignment:* how well does it address the chosen theme?
- *Potential impact:* does it deliver clear value to users, organizations, industry or the community?

**Innovation & Creativity (25%)**
- *Originality & differentiation:* is it a fresh perspective or novel approach?
- *Innovation in the use of Gen AI:* is it a creative use of Gen AI that goes beyond a basic or superficial implementation?

**User Experience & Solution Design (10%)**
- *Usability & accessibility:* is it intuitive and accessible?
- *Experience & integration:* do the components, including the Gen AI, work together smoothly?

Judges have not been announced yet.

## Prizes (USD 30,000 total)
| Award | USD |
|---|---|
| Winner | 10,000 |
| 1st runner-up | 7,000 |
| 2nd runner-up | 5,000 |
| Best use of Google Cloud AI tools | 2,000 |
| Most Impactful Solution | 2,000 |
| Social Choice Award | 2,000 |
| Best UI/UX | 2,000 |

**Finalists:** sponsored flights, accommodation and meals on finale day for **2 members only**. Extra members cannot attend, even if they pay their own way. You arrange and pay for your own visa. Finalists get a live demo in front of Google Cloud leaders and a chance to network.

## Support & contact
- Online sessions on the program and the problem statements
- Discord: https://discord.gg/x5GRzJbKpa
- Email: support+aibuildercup@hack2skill.com · Phone: +91 98703 30830
- Pages: [Themes](https://aibuildercup.com/themes.html) · [Rewards](https://aibuildercup.com/rewards.html) · [FAQs](https://aibuildercup.com/Faqs.html) · Terms & Conditions (a Google Doc linked from the site)

## Gemini models: important
- **Gemini 2.5 Pro/Flash/Flash-Lite retire on Vertex on Oct 16, 2026**, during judging. Don't build on them.
- On day one, list the 3.x model IDs the project can actually call. Keep the model ID in an environment variable.
- The $300 Google Cloud trial credit can't pay for Gemini API calls through AI Studio. Call Gemini through Vertex billed to the trial.

## Inconsistencies on the official site
- The rewards page shows a "USD 0" total (placeholder); the home page says $30k, and the individual prizes add up to that.
- The themes page asks for a "PDF proposal"; the FAQ says "deck". The official PPTX template settles it: deck → PDF.
- A "Category Specification" line lists Healthcare/Education/etc. That's copied from an older event; use the six themes.
- One aggregator site lists the event as ending Oct 11. The official dashboard confirms **Oct 18** for submission.

## Submission deck template (`Submission Template _ AI Builder Cup.pptx`, 16 slides)
| # | Slide | Notes |
|---|---|---|
| 1 | Team details | Team name Hashes, leader, problem statement/theme |
| 2 | Instructions | Delete before submitting |
| 3 | Brief about the idea | Pitch + user story |
| 4 | Opportunities: how it differs, how it solves, USP | Competitor comparison |
| 5 | Features | |
| 6 | Process flow / use-case diagram | |
| 7 | Wireframes (optional) | Can skip; slide 11 shows real screens |
| 8 | Architecture diagram | Google stack |
| 9 | Technologies | |
| 10 | Implementation cost (optional) | Worth filling; makes it look like a real product |
| 11 | **Prototype snapshots** | Needs real screenshots |
| 12 | **Performance / benchmarking** | Needs measured numbers |
| 13 | Future development | |
| 14 | Links | GitHub, 3-min video, live URL |
| 15–16 | Closing | |

## What wins hackathons (from a study of 16 hackathons in 2026)
- **One named user, one painful workflow**, often public-service paperwork
- **A measurable before/after** ("weeks → 5 hours")
- **A human-in-the-loop safeguard**: the AI says "verify", the human decides
- **Deep use of the sponsor's tech**, not a token API call
- **Looks like a product, not a demo**: works end to end, polished, with tests
- **A credible builder or human story**, and one memorable **wow moment**
- **What didn't win:** generic "AI for X", novelty that isn't feasible, overbuilding
