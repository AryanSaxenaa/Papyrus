from __future__ import annotations

import pytest

from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import BibliographyEntry, CitationRecord, ScholarCandidate, ScholarEvidence
from app.pipeline.scholar_match import match_scholar_candidates


def _record(title: str) -> CitationRecord:
    return CitationRecord(
        index=1,
        bibliography=BibliographyEntry(index=1, raw=title, title=title, authors=["Ada Lovelace"]),
    )


@pytest.mark.parametrize(
    ("entry_title", "candidate_title", "sim", "expected"),
    [
        ("Deep Learning", "Deep Learning", 0.99, "match"),
        ("Deep Learning", "deep learning", 0.95, "match"),
        ("Attention Is All You Need", "Attention is all you need", 0.98, "match"),
        ("Graph Neural Networks", "Graph Neural Network Survey", 0.80, "near"),
        ("Unrelated Paper Title", "Completely Different Work", 0.10, "miss"),
    ],
)
def test_scholar_match_states(entry_title, candidate_title, sim, expected):
    record = _record(entry_title)
    candidate = ScholarCandidate(result_id="1", title=candidate_title, title_sim=sim)
    best, state = match_scholar_candidates(record.bibliography, [candidate])
    if expected == "miss":
        assert best is None
    else:
        assert best is not None
    assert state == expected


def test_scholar_veto_doi404():
    from app.pipeline.scholar_verdicts import scholar_veto_doi404

    record = _record("Known Work")
    record.hallucination_type = HallucinationType.DOI_404
    record.evidence_tier = EvidenceTier.TIER_4
    evidence = ScholarEvidence(state="match", best=ScholarCandidate(result_id="x", title="Known Work", title_sim=0.99))
    assert scholar_veto_doi404(record, evidence) is True
    assert record.hallucination_type == HallucinationType.NONE


def test_author_unknown_never_failure():
    record = _record("Paper")
    record.hallucination_type = HallucinationType.NONE
    before = record.hallucination_type
    record.scholar = ScholarEvidence(state="match", author_presence="unknown")
    assert record.scholar.author_presence == "unknown"
    assert record.hallucination_type == before
