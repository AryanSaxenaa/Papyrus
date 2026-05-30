from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import BibliographyEntry, CitationRecord
from app.pipeline.verdicts import author_lists_match_exactly, detect_hallucination


def test_author_lists_match_exactly() -> None:
    assert author_lists_match_exactly(["Smith, J.", "Doe, A."], ["Smith, J", "Doe A"])
    assert not author_lists_match_exactly(["Smith, J."], ["Jones, K."])


def test_type2_on_author_mismatch_with_matching_title() -> None:
    record = CitationRecord(
        index=1,
        bibliography=BibliographyEntry(
            index=1,
            raw="ref",
            title="Exact Paper Title Here",
            doi="10.1234/example",
            authors=["Alice Smith", "Bob Jones"],
        ),
    )
    crossref = {
        "title": "Exact Paper Title Here",
        "authors": ["Alice Smith", "Carol Lee"],
        "year": 2020,
        "abstract": "Abstract text.",
    }
    detect_hallucination(record, crossref, None, None)
    assert record.hallucination_type == HallucinationType.DOI_REDIRECT
    assert record.verdict_color == "failure"


def test_type2_not_raised_when_authors_match() -> None:
    record = CitationRecord(
        index=1,
        bibliography=BibliographyEntry(
            index=1,
            raw="ref",
            title="Exact Paper Title Here",
            doi="10.1234/example",
            authors=["Alice Smith"],
        ),
    )
    crossref = {
        "title": "Exact Paper Title Here",
        "authors": ["Alice Smith"],
        "year": 2020,
        "abstract": "Abstract text.",
    }
    detect_hallucination(record, crossref, None, None)
    assert record.hallucination_type == HallucinationType.NONE
    assert record.evidence_tier == EvidenceTier.TIER_2
