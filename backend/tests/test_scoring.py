from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import AuditRun, CitationRecord, BibliographyEntry
from app.pipeline.scoring import finalize_scores


def _citation(index: int, tier: EvidenceTier, hall: HallucinationType = HallucinationType.NONE) -> CitationRecord:
    return CitationRecord(
        index=index,
        bibliography=BibliographyEntry(index=index, raw="ref"),
        evidence_tier=tier,
        hallucination_type=hall,
    )


def test_coverage_percent_excludes_tier_4() -> None:
    audit = AuditRun(
        citations=[
            _citation(1, EvidenceTier.TIER_1),
            _citation(2, EvidenceTier.TIER_2),
            _citation(3, EvidenceTier.TIER_4),
            _citation(4, EvidenceTier.TIER_4),
        ]
    )
    finalize_scores(audit)
    assert audit.coverage.total == 4
    assert audit.coverage.tier_4 == 2
    assert audit.coverage.coverage_percent == 50.0


def test_risk_critical_above_twenty_percent_failures() -> None:
    audit = AuditRun(
        citations=[
            _citation(1, EvidenceTier.TIER_1, HallucinationType.DOI_404),
            _citation(2, EvidenceTier.TIER_2, HallucinationType.DOI_404),
            _citation(3, EvidenceTier.TIER_2),
            _citation(4, EvidenceTier.TIER_2),
            _citation(5, EvidenceTier.TIER_2),
        ]
    )
    finalize_scores(audit)
    assert audit.risk_level.value == "critical"
