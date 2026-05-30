from app.services.citations_index import is_confirmed_failure


def test_confirmed_failure_hallucination_on_resolvable_tier() -> None:
    assert is_confirmed_failure(
        evidence_tier="tier_2",
        hallucination_type="type_1_doi_404",
        claim_alignment_verdict=None,
    )


def test_unresolvable_tier_not_counted_as_failure() -> None:
    assert not is_confirmed_failure(
        evidence_tier="tier_4",
        hallucination_type="type_1_doi_404",
        claim_alignment_verdict=None,
    )


def test_claim_contradiction_counts_as_failure() -> None:
    assert is_confirmed_failure(
        evidence_tier="tier_1",
        hallucination_type="none",
        claim_alignment_verdict="claim_contradiction",
    )
