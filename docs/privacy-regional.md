# Regional privacy and data review

Scope: what SafeShelf collects from shoppers and businesses in India, Japan, Singapore and Australia (plus the other JAPAC markets), where it is kept, and for how long. This is a review for the hackathon build. It is not legal advice, and a qualified reviewer must check it before any production launch.

## What is collected, and what isn't

| Data | Where | Kept as | Retention |
|---|---|---|---|
| Shopper identity (Firebase uid or WhatsApp number) | watchlists, reports, review decisions | Salted SHA-256 (`OW-...`, `engine/tenancy.py owner_hash`); never raw | Until the shopper deletes the item; deleting a watchlist item erases its product details |
| Label photos (camera check) | not stored | SHA-256 of the image only; names, addresses, phone numbers and emails removed from what was read | The image is never written to disk or the database |
| Product reviews | evidence | Review text and date; reviewer ids hashed (existing M4 rule) | Kept as evidence; never contact details |
| Business API keys | api_keys | SHA-256 of the key; the key is shown once | Until revoked |
| Webhook secrets | not stored | Derived from the server key and the webhook id; only a hash is stored | n/a |
| Usage | usage_events | Tenant, operation, status, time | Per tenant `retention_days` (default 90) |
| Investigation queries | assessment_snapshots | Brand, model, batch, market. No personal data | Kept for audit and evaluation (immutable) |
| Purchase history | not collected | n/a | n/a |

## Country notes
- **India (DPDP Act 2023):** consent for watchlist alerts is opt-in (`notify`). The purpose is limited to product-safety alerts, deletion is available through `DELETE /v1/watchlists/{id}`, and nothing personal goes to third parties. WhatsApp numbers are hashed before storage.
- **Japan (APPI):** no sensitive personal information is collected. Label photos aren't kept, so none is transferred abroad. Japanese notice text is official public data used under PDL 1.0 with the source credited.
- **Singapore (PDPA):** notification and purpose are stated in the screens, data is limited to the hashed owner id, and alerts can be withdrawn by setting notify=false or deleting the item.
- **Australia (Privacy Act 1988, APP 11):** data is protected by hashing and Secret Manager and destroyed on deletion. No marketing use.

## Safeguards in code
- Request size limits and an SSRF allowlist (`api/app/main.py`, `engine/sources/policy.py`). Tenant isolation: watchlists, jobs, reviews and usage are scoped by tenant, and another tenant gets a 404.
- Page and notice text is data, never instructions. Prompt-injection cases are in the red-team benchmark (`bench/fixtures/evidence/`).
- Review decisions, case transitions and identity labels are audited (`audit_events`, `case_reviews`, `review_decisions`).

## Open items before production
- A legal review per country of data residency (Cloud SQL is in asia-south1, Mumbai).
- A data-processing agreement template for business tenants.
- Automatic deletion jobs for `usage_events` and `source_fetches` past their retention.
