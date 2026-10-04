from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

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
    payload: dict[str, object] | None = None


class AuditLimitations(BaseModel):
    not_ai_detection: bool = True
    exa_absence_not_verdict: bool = True
    unresolvable_count: int = 0
    field_coverage_note: str | None = None
    misappropriation_not_detected: str = (
        "Papyrus does not detect misappropriated citations where a real paper is cited "
        "out of context to support a claim its authors never made."
    )
    nli_quantitative_caveat: str = (
        "NLI may not detect numerical discrepancies or causal vs correlational differences. "
        "Manual verification is recommended for quantitative claims."
    )
    out_of_scope: list[str] = Field(
        default_factory=lambda: [
            "AI authorship detection",
            "Journal Phantom via DOAJ",
            "Circular citation analysis (v2)",
            "Self-citation manipulation",
            "Research quality beyond reference integrity",
        ]
    )
    scholar_coverage_note: str = (
        "Google Scholar via SerpApi is an independent witness with uneven coverage "
        "(books, theses, regional journals). A Scholar miss is unknown, not proof of fabrication."
    )
    author_profile_note: str = (
        "Author profile presence is positive-only: confirmed when the author's Scholar profile lists the work; "
        "otherwise unknown — never counted as a failure."
    )


class AuditStreamEvent(BaseModel):
    """SSE / audit log event payload."""

    model_config = ConfigDict(extra="allow")

    ts: str
    type: str
    message: str
    citation_index: int | None = None
    path: str | None = None
    bibliography_count: int | None = None
    inline_count: int | None = None
    coverage: float | None = None
    risk: str | None = None
    doi: str | None = None
    counts: dict[str, int] | None = None
    hallucination: str | None = None
    tier: str | None = None
    color: str | None = None
    claim: str | None = None
    intent: str | None = None
    error: str | None = None
    job_id: str | None = None
    completed: int | None = None
    failed: int | None = None


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


class SerpApiReceipt(BaseModel):
    call_id: str
    engine: Literal[
        "google_scholar",
        "google_scholar_cite",
        "google_scholar_author",
        "google",
    ]
    params: dict[str, Any]
    search_metadata_id: str | None = None
    json_endpoint: str | None = None
    http_status: int
    credits: int
    cache_hit: bool
    latency_ms: int
    created_at: datetime
    raw_ref: str
    sha256_raw: str


class ScholarCandidate(BaseModel):
    result_id: str
    title: str
    link: str | None = None
    summary: str | None = None
    authors: list[dict[str, Any]] = Field(default_factory=list)
    year: int | None = None
    cited_by: int | None = None
    cites_id: str | None = None
    versions_total: int | None = None
    cluster_id: str | None = None
    title_sim: float = 0.0


class ConcordanceReport(BaseModel):
    source_format: Literal["APA", "MLA"]
    authors: Literal["agree", "disagree", "unknown"]
    year: Literal["agree", "disagree", "unknown"]
    venue: Literal["agree", "disagree", "unknown"]
    scholar_string: str


class ScholarEvidence(BaseModel):
    state: Literal["match", "near", "miss", "fetch_error", "skipped", "disabled"]
    skipped_reason: str | None = None
    best: ScholarCandidate | None = None
    concordance: ConcordanceReport | None = None
    author_presence: Literal["confirmed", "unknown", "not_checked"] = "not_checked"
    author_matched_title: str | None = None
    receipts: list[SerpApiReceipt] = Field(default_factory=list)


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
    abstract_only_caveat: str | None = None
    confidence: ConfidenceLevel | None = None
    claim_alignment_verdict: str | None = None
    needs_human_review: bool = False

    status: str = "pending"  # pending | resolving | complete
    verdict_color: str = "pending"  # UI token

    scholar: ScholarEvidence | None = None
    scholar_note: str | None = None
    scholar_limitation: str | None = None
    author_presence_note: str | None = None
    serpapi_receipts: list[SerpApiReceipt] = Field(default_factory=list)


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
    paper_authors: list[str] = Field(default_factory=list)
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

    events: list[dict[str, object]] = Field(default_factory=list)
    limitations: AuditLimitations | None = None
    bulk_job_id: UUID | None = None
    source_url: str | None = None
    paper_text: str | None = None


class AuditSummary(BaseModel):
    """Lightweight row for audit list UIs (`GET /api/audits/summaries`)."""

    id: str
    paper_title: str | None = None
    status: str
    coverage_percent: float
    failure_rate: float
    risk_level: str
    citation_count: int
    created_at: str | None = None


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


class BulkDashboardPaper(BaseModel):
    """One ranked paper row in `GET /api/bulk/{id}/dashboard`."""

    audit_id: str
    title: str | None = None
    first_author: str | None = None
    status: str
    coverage_percent: float
    confirmed_failure_rate: float
    risk_level: str
    resolvable_citations: int
    type_1: int = 0
    type_2: int = 0
    type_5: int = 0
    type_6: int = 0
    type_7: int = 0
    retraction: int = 0
    version_mismatch: int = 0


class BulkDashboard(BaseModel):
    job: BulkAuditJob
    papers: list[BulkDashboardPaper]
    pending_papers: int
    note: str
