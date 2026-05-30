from app.domain.enums import ConfidenceLevel, EvidenceTier, HallucinationType, RiskLevel
from app.domain.models import AuditRun, CoverageSummary, FailureSummary
from app.pipeline.limitations import build_limitations


FAILURE_TYPES = {
    HallucinationType.DOI_404,
    HallucinationType.DOI_REDIRECT,
    HallucinationType.DATE_IMPOSSIBLE,
    HallucinationType.TITLE_DRIFT,
    HallucinationType.CLAIM_CONTRADICTION,
    HallucinationType.RETRACTION,
    HallucinationType.VERSION_MISMATCH,
}


def finalize_scores(audit: AuditRun) -> None:
    citations = audit.citations
    total = len(citations)
    tier_1 = sum(1 for c in citations if c.evidence_tier == EvidenceTier.TIER_1)
    tier_2 = sum(1 for c in citations if c.evidence_tier == EvidenceTier.TIER_2)
    tier_3 = sum(1 for c in citations if c.evidence_tier == EvidenceTier.TIER_3)
    tier_4 = sum(1 for c in citations if c.evidence_tier == EvidenceTier.TIER_4)

    tier_2_plus = tier_1 + tier_2
    resolved = tier_1 + tier_2 + tier_3
    coverage_percent = round((tier_2_plus / total) * 100, 1) if total else 0.0
    unresolvable_ratio = (tier_4 / total) if total else 0.0
    if unresolvable_ratio > 0.5:
        coverage_confidence = ConfidenceLevel.LOW
    elif unresolvable_ratio > 0.25:
        coverage_confidence = ConfidenceLevel.MEDIUM
    else:
        coverage_confidence = ConfidenceLevel.HIGH

    audit.coverage = CoverageSummary(
        total=total,
        tier_1=tier_1,
        tier_2=tier_2,
        tier_3=tier_3,
        tier_4=tier_4,
        coverage_percent=coverage_percent,
        coverage_confidence=coverage_confidence,
    )

    failures = FailureSummary()
    resolvable = [c for c in citations if c.evidence_tier != EvidenceTier.TIER_4]
    for citation in resolvable:
        if citation.hallucination_type == HallucinationType.DOI_404:
            failures.type_1 += 1
        elif citation.hallucination_type == HallucinationType.DOI_REDIRECT:
            failures.type_2 += 1
        elif citation.hallucination_type == HallucinationType.DATE_IMPOSSIBLE:
            failures.type_5 += 1
        elif citation.hallucination_type == HallucinationType.TITLE_DRIFT:
            failures.type_6 += 1
        elif citation.hallucination_type == HallucinationType.VERSION_MISMATCH:
            failures.version_mismatch += 1
        elif citation.hallucination_type == HallucinationType.CLAIM_CONTRADICTION:
            failures.type_7 += 1
        elif citation.hallucination_type == HallucinationType.RETRACTION:
            failures.retraction += 1
        elif citation.claim_alignment_verdict == "supported":
            failures.supported += 1
        elif citation.claim_alignment_verdict in {"claim_contradiction", "not_addressed"}:
            failures.not_supported += 1
        elif citation.claim_alignment_verdict == "cannot_determine":
            failures.cannot_assess += 1

    confirmed_failures = sum(
        1
        for c in resolvable
        if c.hallucination_type in FAILURE_TYPES
        or c.claim_alignment_verdict in {"claim_contradiction", "not_addressed"}
    )
    failure_rate = (confirmed_failures / len(resolvable)) if resolvable else 0.0
    failures.confirmed_failure_rate = round(failure_rate * 100, 1)
    audit.failures = failures

    if not resolvable:
        audit.risk_level = RiskLevel.LOW
    elif failure_rate > 0.20:
        audit.risk_level = RiskLevel.CRITICAL
    elif failure_rate > 0.10:
        audit.risk_level = RiskLevel.HIGH
    elif failure_rate > 0.05:
        audit.risk_level = RiskLevel.ELEVATED
    else:
        audit.risk_level = RiskLevel.LOW

    if audit.coverage.coverage_confidence == ConfidenceLevel.LOW or len(resolvable) < 3:
        audit.risk_confidence = ConfidenceLevel.LOW
    elif failure_rate > 0.10 or audit.coverage.coverage_confidence == ConfidenceLevel.MEDIUM:
        audit.risk_confidence = ConfidenceLevel.MEDIUM
    else:
        audit.risk_confidence = ConfidenceLevel.HIGH

    audit.limitations = build_limitations(audit)
