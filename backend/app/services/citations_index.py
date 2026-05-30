from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import CitationIndexRecord
from app.db.session import get_engine
from app.domain.enums import HallucinationType
from app.domain.models import AuditRun

FAILURE_HALLUCINATION_TYPES = frozenset(
    {
        HallucinationType.DOI_404,
        HallucinationType.DOI_REDIRECT,
        HallucinationType.DATE_IMPOSSIBLE,
        HallucinationType.TITLE_DRIFT,
        HallucinationType.CLAIM_CONTRADICTION,
        HallucinationType.RETRACTION,
        HallucinationType.VERSION_MISMATCH,
    }
)


def is_confirmed_failure(
    *,
    evidence_tier: str,
    hallucination_type: str,
    claim_alignment_verdict: str | None,
) -> bool:
    if evidence_tier == "tier_4":
        return False
    if hallucination_type in FAILURE_HALLUCINATION_TYPES:
        return True
    return claim_alignment_verdict in {"claim_contradiction", "not_addressed"}


def sync_citation_index(audit: AuditRun) -> None:
    engine = get_engine()
    if engine is None:
        return
    audit_id = str(audit.id)
    with Session(engine) as session:
        session.execute(delete(CitationIndexRecord).where(CitationIndexRecord.audit_id == audit_id))
        for citation in audit.citations:
            session.add(
                CitationIndexRecord(
                    id=str(uuid4()),
                    audit_id=audit_id,
                    citation_id=citation.id,
                    citation_index=citation.index,
                    intent=citation.intent.value,
                    evidence_tier=citation.evidence_tier.value,
                    verdict_color=citation.verdict_color,
                    hallucination_type=citation.hallucination_type.value,
                    claim_alignment_verdict=citation.claim_alignment_verdict,
                )
            )
        session.commit()


def reindex_all_audits() -> dict[str, int]:
    from app.store import audit_store

    indexed = 0
    for audit in audit_store.list():
        if audit.status != "complete":
            continue
        sync_citation_index(audit)
        indexed += 1
    return {"audits_indexed": indexed}


def failure_rate_by_audit(limit: int = 20) -> list[dict]:
    engine = get_engine()
    if engine is None:
        return []
    with Session(engine) as session:
        rows = session.scalars(select(CitationIndexRecord)).all()
    by_audit: dict[str, dict] = {}
    for row in rows:
        bucket = by_audit.setdefault(
            row.audit_id,
            {"audit_id": row.audit_id, "total": 0, "failures": 0},
        )
        if row.evidence_tier == "tier_4":
            continue
        bucket["total"] += 1
        if is_confirmed_failure(
            evidence_tier=row.evidence_tier,
            hallucination_type=row.hallucination_type,
            claim_alignment_verdict=row.claim_alignment_verdict,
        ):
            bucket["failures"] += 1
    ranked = sorted(by_audit.values(), key=lambda item: item["failures"] / max(item["total"], 1), reverse=True)
    for item in ranked:
        item["failure_rate"] = round((item["failures"] / item["total"]) * 100, 1) if item["total"] else 0.0
    return ranked[:limit]
