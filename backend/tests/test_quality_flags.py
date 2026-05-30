from app.domain.models import BibliographyEntry, CitationRecord
from app.pipeline.quality_flags import detect_duplicate_dois


def test_detect_duplicate_dois() -> None:
    citations = [
        CitationRecord(
            index=1,
            bibliography=BibliographyEntry(index=1, raw="a", doi="10.1234/a"),
            resolved_doi="10.1234/a",
        ),
        CitationRecord(
            index=2,
            bibliography=BibliographyEntry(index=2, raw="b", doi="10.1234/b"),
            resolved_doi="10.1234/b",
        ),
        CitationRecord(
            index=3,
            bibliography=BibliographyEntry(index=3, raw="a2", doi="10.1234/a"),
            resolved_doi="10.1234/a",
        ),
    ]
    duplicates = detect_duplicate_dois(citations)
    assert len(duplicates) == 1
    assert duplicates[0]["citation_indices"] == [1, 3]
