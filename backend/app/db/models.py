from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
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
