from __future__ import annotations

import json
from uuid import uuid4

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import (
    AuditEventRow,
    AuditMetadataRecord,
    CitationRow,
    ResolutionAttemptRow,
)
from app.db.session import get_engine
from app.domain.models import AuditRun, CitationRecord


def _should_sync() -> bool:
    settings = get_settings()
    return settings.sync_relational_audits and settings.persistence_backend in {"postgres", "both"}


def sync_relational_audit(audit: AuditRun) -> None:
    if not _should_sync():
        return
    engine = get_engine()
    if engine is None:
        return

    audit_id = str(audit.id)
    with Session(engine) as session:
        session.execute(delete(ResolutionAttemptRow).where(ResolutionAttemptRow.audit_id == audit_id))
        session.execute(delete(CitationRow).where(CitationRow.audit_id == audit_id))

        meta = session.get(AuditMetadataRecord, audit_id)
        if meta is None:
            meta = AuditMetadataRecord(id=audit_id)
            session.add(meta)
        meta.paper_title = (audit.paper_title or "")[:512] or None
        meta.status = audit.status
        meta.pipeline_version = audit.pipeline_version
        meta.risk_level = audit.risk_level.value
        meta.risk_confidence = audit.risk_confidence.value
        meta.coverage_json = json.dumps(audit.coverage.model_dump(mode="json"))
        meta.failures_json = json.dumps(audit.failures.model_dump(mode="json"))
        meta.limitations_json = json.dumps(audit.limitations) if audit.limitations else None
        meta.quality_summary_json = json.dumps(audit.quality_summary) if audit.quality_summary else None
        meta.source_url = audit.source_url
        meta.bulk_job_id = str(audit.bulk_job_id) if audit.bulk_job_id else None
        meta.error = audit.error
        meta.completed_at = audit.completed_at

        for citation in audit.citations:
            extra = {
                "nli_verdict": citation.nli_verdict.value,
                "quantitative_claim": citation.quantitative_claim,
                "quantitative_caveat": citation.quantitative_caveat,
                "claim_pending_review": citation.claim_pending_review,
                "oa_pdf_url": citation.oa_pdf_url,
                "exa_signal": citation.exa_signal,
                "source_verify_url": citation.source_verify_url,
                "version_mismatch": citation.version_mismatch.model_dump(mode="json")
                if citation.version_mismatch
                else None,
                "quality_flags": citation.quality_flags,
                "resolved_authors": citation.resolved_authors,
            }
            session.add(
                CitationRow(
                    id=citation.id,
                    audit_id=audit_id,
                    citation_index=citation.index,
                    intent=citation.intent.value,
                    evidence_tier=citation.evidence_tier.value,
                    verdict_color=citation.verdict_color,
                    hallucination_type=citation.hallucination_type.value,
                    status=citation.status,
                    resolved_title=citation.resolved_title,
                    resolved_doi=citation.resolved_doi,
                    resolved_year=citation.resolved_year,
                    retracted=citation.retracted,
                    claim_alignment_verdict=citation.claim_alignment_verdict,
                    confidence=citation.confidence.value if citation.confidence else None,
                    title_edit_distance=citation.title_edit_distance,
                    extracted_claim=citation.extracted_claim,
                    claim_user_corrected=citation.claim_user_corrected,
                    evidence_passage=citation.evidence_passage,
                    evidence_provenance=citation.evidence_provenance,
                    bibliography_json=json.dumps(citation.bibliography.model_dump(mode="json")),
                    inline_markers_json=json.dumps(
                        [m.model_dump(mode="json") for m in citation.inline_markers]
                    ),
                    extra_json=json.dumps(extra),
                )
            )
            for attempt in citation.resolution_attempts:
                session.add(
                    ResolutionAttemptRow(
                        id=str(uuid4()),
                        citation_id=citation.id,
                        audit_id=audit_id,
                        source=attempt.source.value,
                        query=attempt.query[:512],
                        success=attempt.success,
                        summary=attempt.summary[:64],
                        payload_json=json.dumps(attempt.payload) if attempt.payload else None,
                    )
                )
        session.commit()


def persist_audit_event(audit_id: str, event: dict) -> None:
    if not _should_sync():
        return
    engine = get_engine()
    if engine is None:
        return
    extra = {k: v for k, v in event.items() if k not in {"ts", "type", "message"}}
    ts_raw = event.get("ts")
    if isinstance(ts_raw, str):
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    else:
        ts = datetime.utcnow()
    with Session(engine) as session:
        session.add(
            AuditEventRow(
                id=str(uuid4()),
                audit_id=audit_id,
                ts=ts,
                event_type=event.get("type", "event"),
                message=event.get("message", ""),
                extra_json=json.dumps(extra) if extra else None,
            )
        )
        session.commit()


def list_citation_attempts(audit_id: str, citation_id: str) -> list[dict]:
    engine = get_engine()
    if engine is None:
        return []
    with Session(engine) as session:
        rows = session.scalars(
            select(ResolutionAttemptRow)
            .where(
                ResolutionAttemptRow.audit_id == audit_id,
                ResolutionAttemptRow.citation_id == citation_id,
            )
            .order_by(ResolutionAttemptRow.created_at)
        ).all()
    return [
        {
            "source": row.source,
            "query": row.query,
            "success": row.success,
            "summary": row.summary,
            "payload": json.loads(row.payload_json) if row.payload_json else None,
        }
        for row in rows
    ]


def relational_schema_stats() -> dict:
    engine = get_engine()
    if engine is None:
        return {"postgres": False}
    with Session(engine) as session:
        def _count(model: type) -> int:
            return int(session.scalar(select(func.count()).select_from(model)) or 0)

        return {
            "postgres": True,
            "audit_metadata": _count(AuditMetadataRecord),
            "citations": _count(CitationRow),
            "resolution_attempts": _count(ResolutionAttemptRow),
            "audit_events": _count(AuditEventRow),
        }


def delete_relational_audit(audit_id: str) -> None:
    engine = get_engine()
    if engine is None:
        return
    with Session(engine) as session:
        session.execute(delete(ResolutionAttemptRow).where(ResolutionAttemptRow.audit_id == audit_id))
        session.execute(delete(CitationRow).where(CitationRow.audit_id == audit_id))
        session.execute(delete(AuditEventRow).where(AuditEventRow.audit_id == audit_id))
        meta = session.get(AuditMetadataRecord, audit_id)
        if meta:
            session.delete(meta)
        session.commit()
