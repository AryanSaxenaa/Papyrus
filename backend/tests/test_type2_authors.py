from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import BibliographyEntry, CitationRecord
from app.pipeline.verdicts import detect_hallucination
from app.text.similarity import author_sets_equal


def test_author_sets_equal() -> None:
    assert author_sets_equal(["Smith, J.", "Doe, A."], ["Smith, J", "Doe A"]) is True
    assert author_sets_equal(["Smith, J."], ["Jones, K."]) is False
    assert author_sets_equal([], ["Jones, K."]) is None


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


def test_type2_uses_merged_metadata_when_crossref_missing() -> None:
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
    scholar = {
        "title": "Exact Paper Title Here",
        "authors": ["Alice Smith", "Wrong Author"],
        "year": 2020,
        "abstract": "Abstract text.",
    }
    detect_hallucination(record, None, scholar, None, merged_override=scholar)
    assert record.hallucination_type == HallucinationType.DOI_REDIRECT


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
