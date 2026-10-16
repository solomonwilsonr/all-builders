# Source access log

Which official sources SafeShelf queries, how, under what terms, and what happens when one can't be reached. The machine-readable copy is [data/source_registry_japac.yaml](../data/source_registry_japac.yaml); an adapter runs only when its entry says `verified` (or `key_required` with the key set, or `browser_only` with the Research Agent configured). Live status: `GET /v1/sources/health` or `make source-health`.

Checked 16 Oct 2026 from Solomon's laptop. Cloud Run's outgoing addresses may be treated differently, so re-check after each deploy.

| Source | Country | Access | Status | Terms | If unavailable |
|---|---|---|---|---|---|
| CPSC recalls API | US | REST JSON, plain HTTP | ✅ verified | US federal work, public domain | "source unavailable" in the coverage list |
| SaferProducts.gov incidents | US | OData; free key | 🔑 needs `SAFERPRODUCTS_API_KEY` (service answers 401 without; confirm the auth scheme when the key arrives) | Public reports, which are allegations | "not supported" |
| OECD GlobalRecalls | AU, JP, KR, SG, TW, ASEAN | Open JSON web service | ✅ verified | © OECD; SafeShelf keeps metadata, short excerpts and links, with no bulk republication. SG and ASEAN feeds stop in 2022 | "source unavailable" |
| Consumer Affairs Agency recall site | JP | Public HTML: session cookie, then the site's own search form; detail pages | ✅ verified | **PDL 1.0** (recall.caa.go.jp/about): reuse allowed with the source credited and edits marked. Every record carries 「出典：消費者庁リコール情報サイト」 | "source unavailable" |
| NITE accident information | JP | Site reachable; no documented query interface | ⏸ unverified | Not reviewed for automated use | "not supported" |
| METI recall notices | JP | HTML | ⛔ blocked (403) | CAA links METI notices, so they're reached through CAA | "not supported" |
| ACCC recalls RSS | AU | RSS; parser built and tested | ⛔ blocked (403, Akamai) | Official public feed | Australian notices come through OECD GlobalRecalls |
| CPSO recalls and alerts | SG | HTML | ⛔ blocked (403) | n/a | "not supported"; older notices through OECD |
| SAFETY Mark registry | SG | Public search for people | ⏸ unverified | Only controlled goods need the mark | "not supported" |
| EU Safety Gate | EU | JS portal; no permitted JSON endpoint confirmed | 🌐 browser only (Research Agent, deep checks) | Official public portal | "not supported" on quick checks |
| Product Safety NZ | NZ | HTML | 🌐 browser only | Official public site | "not supported" on quick checks |
| CCPA orders and BIS raids (PIB releases) | IN | Plain HTTP, stored by `data/load_india_notices.py` | ✅ verified (stored copy) | Government press releases, free to use with credit | "source unavailable" |
| BIS certification lookup | IN | Lookup for people (bis.gov.in, BIS Care app) | ❌ no automation API | A public lookup doesn't permit automated access | Mark shown as "not verified" with the lookup link; never "fake" |
| Manufacturer feeds | any | Only with written permission | ❌ none signed up | n/a | n/a |

## Rules every adapter follows
- **Allowlist:** each source has its own official domains. Requests to anything else are refused, a redirect off those domains is refused, and bare IP addresses and private addresses are never fetched (`engine/sources/policy.py`).
- **Never work around a block:** a 403, captcha or block page becomes `blocked`, and the answer says a person needs to look.
- **Short timeouts and one retry for transient errors.** A circuit breaker rests a source after 3 failures in a row. SafeShelf also applies its own per-source rate limit.
- **Caching per source** (`ttl_s`). Answers from the cache are marked `checked_cache`, with their original retrieval time.
- **Every fetch is logged** in `source_fetches`: status, latency and a hash of the raw answer. Raw answers are stored only where a licence allows.
- **A failure is never shown as clear:** coverage states are `checked_live`, `checked_cache`, `no_matching_notice_found`, `source_unavailable` and `not_supported`.

## Before switching a source on
1. Confirm the documented access method and the reuse terms. Record them here and in the registry, with the date.
2. Record real responses as fixtures in `engine/tests/fixtures/sources/` and test empty, malformed, 403, 429, 5xx and timeout answers.
3. Set `access_status: verified`, then `make test-sources` and `make bench-japac`.
