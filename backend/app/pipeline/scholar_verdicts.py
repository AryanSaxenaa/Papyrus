from __future__ import annotations

from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import CitationRecord, ScholarEvidence
from app.pipeline.evidence_tier import tier_with_scholar


def scholar_veto_doi404(record: CitationRecord, evidence: ScholarEvidence) -> bool:
    if evidence.state != "match":
        return False
    if record.hallucination_type != HallucinationType.DOI_404:
        return False
    record.hallucination_type = HallucinationType.NONE
    record.verdict_color = "supported"
    record.evidence_tier = tier_with_scholar(record.evidence_tier, scholar_corroborated=True)
    record.scholar_note = (
        "DOI did not resolve in free indexes, but Google Scholar lists a matching work (witness only)."
    )
    return True


def apply_scholar_post_rules(record: CitationRecord, evidence: ScholarEvidence) -> None:
    if evidence.state == "match" and record.evidence_tier == EvidenceTier.TIER_4:
        record.evidence_tier = tier_with_scholar(record.evidence_tier, scholar_corroborated=True)
    if evidence.state == "miss" and record.evidence_tier == EvidenceTier.TIER_4:
        record.scholar_limitation = (
            "Scholar returned no match; coverage of regional or non-English works is limited. "
            "Unknown is not evidence of fabrication."
        )
    if evidence.author_presence == "unknown":
        record.author_presence_note = "Author profile did not list this work — unknown, not a failure signal."


def apply_scholar_before_doi404(record: CitationRecord) -> None:
    evidence = record.scholar
    if not evidence:
        return
    if record.hallucination_type == HallucinationType.DOI_404:
        scholar_veto_doi404(record, evidence)
