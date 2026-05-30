from app.domain.enums import EvidenceTier, HallucinationType, NliVerdict
from app.domain.models import AuditRun, BibliographyEntry, CitationRecord
from app.pipeline.scoring import finalize_scores


def test_not_addressed_does_not_inflate_confirmed_failure_rate() -> None:
    audit = AuditRun(
        citations=[
            CitationRecord(
                index=1,
                bibliography=BibliographyEntry(index=1, raw="ref"),
                evidence_tier=EvidenceTier.TIER_1,
                hallucination_type=HallucinationType.NONE,
                claim_alignment_verdict="not_addressed",
                nli_verdict=NliVerdict.NEUTRAL,
            ),
            CitationRecord(
                index=2,
                bibliography=BibliographyEntry(index=2, raw="ref"),
                evidence_tier=EvidenceTier.TIER_2,
                hallucination_type=HallucinationType.NONE,
                claim_alignment_verdict="supported",
            ),
            CitationRecord(
                index=3,
                bibliography=BibliographyEntry(index=3, raw="ref"),
                evidence_tier=EvidenceTier.TIER_2,
                hallucination_type=HallucinationType.NONE,
                claim_alignment_verdict="supported",
            ),
            CitationRecord(
                index=4,
                bibliography=BibliographyEntry(index=4, raw="ref"),
                evidence_tier=EvidenceTier.TIER_2,
                hallucination_type=HallucinationType.NONE,
                claim_alignment_verdict="supported",
            ),
            CitationRecord(
                index=5,
                bibliography=BibliographyEntry(index=5, raw="ref"),
                evidence_tier=EvidenceTier.TIER_2,
                hallucination_type=HallucinationType.NONE,
                claim_alignment_verdict="supported",
            ),
        ]
    )
    finalize_scores(audit)
    assert audit.failures.not_supported == 1
    assert audit.failures.confirmed_failure_rate == 0.0
    assert audit.risk_level.value == "low"
