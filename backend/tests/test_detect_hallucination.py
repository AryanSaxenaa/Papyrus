from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import BibliographyEntry, CitationRecord
from app.pipeline.verdicts import detect_hallucination


def test_unresolved_doi_defers_type1_until_post_exa() -> None:
    record = CitationRecord(
        index=1,
        bibliography=BibliographyEntry(index=1, raw="x", doi="10.0000/missing"),
    )
    detect_hallucination(record, None, None, None, merged_override=None)
    assert record.hallucination_type == HallucinationType.NONE
    assert record.evidence_tier == EvidenceTier.TIER_4
    assert record.verdict_color == "unresolvable"
