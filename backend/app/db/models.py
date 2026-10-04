from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AuditRecord(Base):
    __tablename__ = "audits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditMetadataRecord(Base):
    """Relational audit header (v2) — complements JSON payload blob."""

    __tablename__ = "audit_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    pipeline_version: Mapped[str] = mapped_column(String(16))
    risk_level: Mapped[str] = mapped_column(String(16))
    risk_confidence: Mapped[str] = mapped_column(String(16))
    coverage_json: Mapped[str] = mapped_column(Text)
    failures_json: Mapped[str] = mapped_column(Text)
    limitations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bulk_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CitationRow(Base):
    """Per-citation relational row (v2)."""

    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    citation_index: Mapped[int] = mapped_column()
    intent: Mapped[str] = mapped_column(String(32))
    evidence_tier: Mapped[str] = mapped_column(String(16))
    verdict_color: Mapped[str] = mapped_column(String(24))
    hallucination_type: Mapped[str] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(16))
    resolved_title: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    resolved_doi: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolved_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retracted: Mapped[bool] = mapped_column(Boolean, default=False)
    claim_alignment_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    title_edit_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_claim: Mapped[str | None] = mapped_column(Text, nullable=True)
    claim_user_corrected: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_passage: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_provenance: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bibliography_json: Mapped[str] = mapped_column(Text)
    inline_markers_json: Mapped[str] = mapped_column(Text, default="[]")
    extra_json: Mapped[str] = mapped_column(Text, default="{}")


class ResolutionAttemptRow(Base):
    __tablename__ = "resolution_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    citation_id: Mapped[str] = mapped_column(String(36), index=True)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    source: Mapped[str] = mapped_column(String(32))
    query: Mapped[str] = mapped_column(String(512))
    success: Mapped[bool] = mapped_column(Boolean)
    summary: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEventRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class BulkJobRecord(Base):
    __tablename__ = "bulk_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditSummaryRecord(Base):
    """Denormalized index for listing audits without parsing full JSON payloads."""

    __tablename__ = "audit_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    paper_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    coverage_percent: Mapped[float] = mapped_column()
    failure_rate: Mapped[float] = mapped_column()
    risk_level: Mapped[str] = mapped_column(String(16))
    citation_count: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CitationIndexRecord(Base):
    """Denormalized per-citation rows for analytics and cross-audit queries."""

    __tablename__ = "citation_index"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    citation_id: Mapped[str] = mapped_column(String(36), index=True)
    citation_index: Mapped[int] = mapped_column()
    intent: Mapped[str] = mapped_column(String(32))
    evidence_tier: Mapped[str] = mapped_column(String(16))
    verdict_color: Mapped[str] = mapped_column(String(24))
    hallucination_type: Mapped[str] = mapped_column(String(48))
    claim_alignment_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)


class CitationCorrectionRecord(Base):
    """User intent/claim overrides for ground-truth dataset building."""

    __tablename__ = "citation_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_id: Mapped[str] = mapped_column(String(36), index=True)
    citation_id: Mapped[str] = mapped_column(String(36), index=True)
    citation_index: Mapped[int] = mapped_column()
    field: Mapped[str] = mapped_column(String(32))
    original_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SerpApiCallRow(Base):
    __tablename__ = "serpapi_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    citation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    engine: Mapped[str] = mapped_column(String(32))
    params_json: Mapped[str] = mapped_column(Text)
    search_metadata_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    json_endpoint: Mapped[str | None] = mapped_column(String(512), nullable=True)
    http_status: Mapped[int] = mapped_column(Integer)
    credits: Mapped[int] = mapped_column(Integer)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer)
    raw_key: Mapped[str] = mapped_column(String(256))
    sha256_raw: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
