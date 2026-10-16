"""The claim-level evidence passport (plan v2.2 J2): one schema-validated EvidenceClaim per atomic claim, carrying its
source, its four timestamps, how it was extracted, and each verification result. Shared by the API (contracts) and
the store (evidence_claims table).
"""
import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ClaimType = Literal["recall", "safety_notice", "seizure", "hazard", "affected_models", "remedy", "incident_report",
                    "registry_record", "manufacturer_statement", "correction", "hazard_signal", "certification"]
Authenticity = Literal["authentic", "official_domain", "unofficial_domain", "missing_reference", "unavailable"]
Support = Literal["supported", "unsupported", "not_checked"]
MatchTier = Literal["exact", "variant", "suspected_rebrand", "lookalike", "family_named", "unresolved", "none"]
ScopeStatus = Literal["in_scope", "batch_excluded", "batch_unknown", "model_excluded", "not_applicable"]
Verification = Literal["verified", "partially_verified", "unverified", "contradicted", "retracted"]
Review = Literal["not_required", "pending", "approved", "corrected", "rejected"]


class EvidenceClaim(BaseModel):
    # identity
    claim_id: str
    claim_type: ClaimType
    claim_text: str
    product_id: str | None = None
    model: str | None = None
    variant: str | None = None
    batch_scope: list[str] = Field(default_factory=list)
    jurisdiction: str | None = None
    # source
    source_registry_id: str
    source_record_id: str
    source_url: str = ""
    source_type: str = ""
    source_document_hash: str = ""
    source_excerpt: str = ""
    source_language: str = "en"
    license_policy_id: str = ""
    attribution: str = ""
    # timeline (never merged)
    event_at: datetime | None = None
    source_published_at: datetime | None = None
    source_updated_at: datetime | None = None
    retrieved_at: datetime | None = None
    ingested_at: datetime | None = None
    # extraction
    extraction_method: str = "code"
    model_version: str | None = None
    tool_version: str = "engine.sources/0.2"
    prompt_version: str | None = None
    raw_artifact_pointer: str | None = None
    # verification
    source_authenticity_status: Authenticity = "missing_reference"
    claim_support_status: Support = "not_checked"
    product_match_tier: MatchTier = "none"
    identity_scope_status: ScopeStatus = "not_applicable"
    independence_group_id: str | None = None
    verification_status: Verification = "unverified"
    review_status: Review = "not_required"
    is_local: bool = False
    # revisions
    supersedes_claim_id: str | None = None
    retraction_reason: str | None = None
    contradicting_claim_ids: list[str] = Field(default_factory=list)
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    review_rationale: str | None = None

    def public(self) -> dict:
        return self.model_dump(mode="json", exclude={"reviewer_id"})


def claim_id(source_record_id: str, claim_type: str, text: str) -> str:
    return "CL-" + hashlib.sha1(f"{source_record_id}|{claim_type}|{text}".encode()).hexdigest()[:12].upper()


def verification_status(authenticity: str, support: str, tier: str, scope: str, retracted: bool,
                        contradicted: bool) -> str:
    """Rolls the four checks into one word; the parts stay visible next to it."""
    if retracted:
        return "retracted"
    if contradicted:
        return "contradicted"
    if authenticity in ("authentic", "official_domain") and support == "supported" and tier == "exact" \
            and scope == "in_scope":
        return "verified"
    if authenticity in ("authentic", "official_domain") and support == "supported":
        return "partially_verified"
    return "unverified"
