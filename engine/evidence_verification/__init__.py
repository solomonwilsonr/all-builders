"""Evidence Intelligence & Verification (plan v2.2 workstream J): one shared subsystem that every verdict path uses.

    claims          the claim-level evidence passport (EvidenceClaim)
    source_check    is the source real and official, and does its text support the claim?
    identity_scope  does the notice cover this exact model, variant and batch, in this market?
    corroboration   which reports are independent observations (copies count once)
    contradictions  corrections, retractions, unaffected models or batches, alternative causes
    adjudicator     the deterministic policy that sets the outcome (agents can't override it)

Four checks stay separate: source authenticity, claim support, product applicability and independent corroboration.
A verified source does not make a verified hazard for the shopper's product.
"""
POLICY_VERSION = "2026-10-16.1"
