from app.domain.enums import EvidenceTier, ResolutionSource
from app.domain.models import CitationRecord, BibliographyEntry, ResolutionAttempt
from app.pipeline.evidence import build_evidence_provenance


def _record(tier: EvidenceTier, attempts: list[ResolutionAttempt] | None = None) -> CitationRecord:
    return CitationRecord(
        index=1,
        bibliography=BibliographyEntry(index=1, raw="ref"),
        evidence_tier=tier,
        resolution_attempts=attempts or [],
    )


def test_provenance_tier2_from_crossref() -> None:
    record = _record(
        EvidenceTier.TIER_2,
        [
            ResolutionAttempt(
                source=ResolutionSource.CROSSREF,
                query="10.1/x",
                success=True,
                summary="hit",
                payload={"abstract": "We found an effect."},
            )
        ],
    )
    assert build_evidence_provenance(record) == "Tier 2 — abstract from crossref"


def test_provenance_tier1_fulltext() -> None:
    record = _record(
        EvidenceTier.TIER_1,
        [
            ResolutionAttempt(
                source=ResolutionSource.FULLTEXT,
                query="https://oa.example/paper.pdf",
                success=True,
                summary="hit",
                payload={"full_text": "Long body text."},
            )
        ],
    )
    assert "Tier 1" in (build_evidence_provenance(record) or "")
    assert "fulltext" in (build_evidence_provenance(record) or "")
