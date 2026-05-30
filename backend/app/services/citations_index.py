from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete
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
