# Media idea: "NightDesk", a health-harm triage desk for vernacular fact-checkers

**Theme:** Media, Content & Digital Experiences ("how content is … understood"). **Market:** Philippines and India first (Tagalog/Taglish, Tamil/Hinglish), then Indonesia and Thailand.

> **One-line pitch:** "200 vernacular forwards come in overnight. NightDesk puts the 3 that could kill someone on top, already matched to past fact-checks in any language and drafted in Tagalog, ready for the editor to approve."

## The user
**Joanna**, the lone night-shift duty editor at a 5-person Philippine fact-checking team (like VERA Files or Tsek.ph partners). Tips arrive from a WhatsApp/Meedan Check tipline as TikToks, Reels and voice notes in Taglish. She can check about 3 a night by hand, and has to guess which 3.

## Why it can win
| Winner pattern | NightDesk |
|---|---|
| One named user, one painful workflow | One duty editor facing hundreds of tips |
| Health / public-interest stakes | 86% of fact-checkers cover public health. Demo cases: AI-faked ads of Dr. Willie Ong selling cures (PH) and the viral Sidhu "cancer diet" claim (IN) |
| A before/after number | Measured live: time from reel to claim list (manual about 10–20 min of watching and transcribing → under 1 min), harm-ranking agreement with an expert's picks, share of tips auto-matched to an existing fact-check, share of drafts the editor accepts |
| A safeguard | It never says "true/false". It ranks, matches and drafts, and the editor approves before anything is published |
| Deep use of Google tech | Gemini long-video + code-mixed audio understanding, **Google Fact Check Tools API** (search past checks and publish new ones as ClaimReview), Gemma as a cheap spam filter, Cloud Run, Firestore |
| Media theme fit | It is literally about how content is understood. It's newsroom tooling, not healthcare software |
| Human story | IFCN 2026: 76% of fact-checkers are financially vulnerable or in crisis, 38% cut staff in 2025. Logically collapsed in 2025, leaving India with a gap |

## Competition
- **In this hackathon:** the public Media entries are audio description, ad localization, cricket analytics and curriculum lessons. **None touches misinformation.**
- **In the market:**
  - **Full Fact "Raphael":** the nearest match. Gemini finds health claims in video with timestamps, but only in English, French and Arabic, with no APAC presence and no drafting.
  - **Factiverse / ShortCheck:** claim spotting, evaluated only in Norwegian and English.
  - **Meedan Check:** runs the tiplines but doesn't extract or draft. **NightDesk plugs into it rather than competing with it.**
  - **Logically:** collapsed.
- **Hackathon prior art:** lots of consumer apps along the lines of "paste a link, get a verdict". **Never pitch it that way.** Pitch it as a professional desk with a harm-ranked queue, cross-language matching, a local-language draft and editor approval.

## What's actually new
1. **Code-mixed video claims with timestamps:** Taglish/Hinglish speech plus on-screen text.
2. **Cross-language "already debunked?" matching:** a Tamil reel is matched to an English or Tagalog fact-check.
3. **Health-harm ranking**, plus a fake-doctor-endorsement detector.
4. **A local-language draft → editor approval → publish back to Google's fact-check database** through the Fact Check Tools API. This keeps the ecosystem going after Google removed the ClaimReview snippet from Search in 2025.

## Demo flow (3 min)
1. Joanna's night, with the IFCN numbers on screen.
2. 50 real, already-debunked forwards flow in. Gemma drops the spam.
3. Gemini extracts the claims with timestamps (click a claim and the video jumps to that moment).
4. **Wow moment:** the Dr. Willie Ong fake ad goes to the top, labelled "HIGH HARM: medical cure claim, impersonated doctor", and is matched to VERA Files' existing Tagalog fact-check.
5. A new claim with no match gets a Tagalog draft with sources. Joanna edits and approves, and it's published as ClaimReview.
6. Scoreboard: minutes saved, matches found, drafts accepted.

## Rubric map
| Criterion | Proof |
|---|---|
| Technical & GenAI 40% | Multimodal video/audio, cross-language retrieval, an ADK pipeline (triage → extract → match → rank → draft), a Gemma first filter, the Fact Check Tools API in both directions |
| Problem & Impact 25% | Health misinformation, struggling fact-checkers, Reuters DNR 2025 (53% in India see WhatsApp as the top misinformation threat; 49% of Thais use TikTok for news) |
| Innovation 25% | Vernacular code-mixed video, cross-language debunk matching, harm ranking, publishing back to the ecosystem |
| UX 10% | One queue screen, timestamp jump, side-by-side draft editor |

## Data
- MultiClaim (28k posts / 206k fact-checks / 39 languages), SemEval-2025 Task 7
- Live Google Claim Search API filtered by `hi/ta/tl/id/th`
- Public, already-debunked videos as ground truth (Willie Ong fake ads, the Sidhu cancer diet)

## Risks
- **Reads as "yet another fact-check app":** the first 10 seconds must show the desk and the queue, not a verdict.
- **Gemini's Tagalog/Tamil audio accuracy:** test on day 1 and pick the language that works best.
- **Copyright of the demo videos:** use short clips of already-public debunked content and cite the fact-checker.
- **Model retirement:** Gemini 2.5 retires Oct 16, so build on a current 3.x model.

## Runner-up (Media): "Yasashii Clinic Pack"
A Japanese clinic's international-desk nurse uploads an after-visit sheet. Gemini extracts the critical facts (dose, timing, red flags) and writes Yasashii Nihongo with furigana plus the patient's language (Vietnamese/Nepali). A second Gemini pass checks that no fact was lost or changed, then generates a pictogram card, TTS audio and a QR code with a 3-question quiz. **Novel as a combination** (existing converters have no fact check and no audio or pictograms). 4.1M foreign residents in Japan; 76% prefer Yasashii Nihongo. **Risk:** judges may read it as healthcare rather than media.

## Also checked, not recommended
- SEBI/ASCI influencer-video clearance desk (BanProof overlap, no real before/after figure)
- YouTube copyright-claim disputes (episodic, YouTube's own tools)
- OTT age-rating drafter (Spherex and PFT CLEAR already do it)
- Sign language (too hard in 8 days), minority-language radio archives (consent issues)

Notes: research_notes/Media idea search/
