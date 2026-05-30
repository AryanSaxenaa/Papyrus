from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import (
    CitationIntent,
    ConfidenceLevel,
    EvidenceTier,
    HallucinationType,
    NliVerdict,
    ResolutionSource,
    RiskLevel,
)


class ResolutionAttempt(BaseModel):
    source: ResolutionSource
    query: str
    success: bool
    summary: str
    payload: dict[str, Any] | None = None


class BibliographyEntry(BaseModel):
    index: int
    raw: str
    authors: list[str] = Field(default_factory=list)
    title: str | None = None
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None


class InlineCitation(BaseModel):
    marker: str
    bibliography_index: int
    context_window: str


class VersionEntry(BaseModel):
    label: str
    date: str | None = None
    title: str | None = None
    abstract: str | None = None
    source: str | None = None


class VersionMismatchInfo(BaseModel):
    preprint: VersionEntry | None = None
    published: VersionEntry | None = None
    revisions: list[VersionEntry] = Field(default_factory=list)
    material_difference: bool = False


class CitationRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    index: int
    bibliography: BibliographyEntry
    inline_markers: list[InlineCitation] = Field(default_factory=list)

    intent: CitationIntent = CitationIntent.BACKGROUND
    intent_user_override: bool = False

    resolution_attempts: list[ResolutionAttempt] = Field(default_factory=list)
    evidence_tier: EvidenceTier = EvidenceTier.TIER_4
    resolved_title: str | None = None
    resolved_doi: str | None = None
    resolved_year: int | None = None
    resolved_authors: list[str] = Field(default_factory=list)
    retracted: bool = False
    oa_pdf_url: str | None = None
    exa_signal: str | None = None
    source_verify_url: str | None = None

    hallucination_type: HallucinationType = HallucinationType.NONE
    title_edit_distance: float | None = None
    version_mismatch: VersionMismatchInfo | None = None

    extracted_claim: str | None = None
    claim_user_corrected: str | None = None
    claim_pending_review: bool = False
    evidence_passage: str | None = None
    evidence_provenance: str | None = None
    evidence_retrieved_at: datetime | None = None
    nli_verdict: NliVerdict = NliVerdict.SKIPPED
    quantitative_claim: bool = False
    quantitative_caveat: str | None = None
    confidence: ConfidenceLevel | None = None
    claim_alignment_verdict: str | None = None
    quality_flags: list[str] = Field(default_factory=list)

    status: str = "pending"  # pending | resolving | complete
    verdict_color: str = "pending"  # UI token


class CoverageSummary(BaseModel):
    total: int = 0
    tier_1: int = 0
    tier_2: int = 0
    tier_3: int = 0
    tier_4: int = 0
    coverage_percent: float = 0.0
    coverage_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class FailureSummary(BaseModel):
    supported: int = 0
    not_supported: int = 0
    cannot_assess: int = 0
    type_1: int = 0
    type_2: int = 0
    type_5: int = 0
    type_6: int = 0
    type_7: int = 0
    retraction: int = 0
    version_mismatch: int = 0
    confirmed_failure_rate: float = 0.0


class AuditRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    paper_title: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    pipeline_version: str = "2.0"
    status: str = "queued"  # queued | running | complete | failed
    error: str | None = None

    citations: list[CitationRecord] = Field(default_factory=list)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    failures: FailureSummary = Field(default_factory=FailureSummary)
    risk_level: RiskLevel = RiskLevel.LOW
    risk_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    events: list[dict[str, Any]] = Field(default_factory=list)
    limitations: dict[str, Any] | None = None
    quality_summary: dict[str, Any] | None = None
    bulk_job_id: UUID | None = None
    source_url: str | None = None
    paper_text: str | None = None


class BulkAuditJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "queued"  # queued | running | complete | failed
    total: int = 0
    completed: int = 0
    failed: int = 0
    audit_ids: list[UUID] = Field(default_factory=list)
    avg_seconds_per_paper: float | None = None
    estimated_seconds_remaining: int | None = None
    error: str | None = None
