from __future__ import annotations

import difflib
import re

from app.domain.enums import (
    CitationIntent,
    ConfidenceLevel,
    EvidenceTier,
    HallucinationType,
    NliVerdict,
)
from app.domain.models import CitationRecord
from app.pipeline import nli as nli_pipeline
from app.pipeline.evidence_tier import tier_from_resolved
from app.text.sentences import split_sentences
from app.text.similarity import author_sets_equal, coerce_author_list, compare_titles


QUANT_PATTERN = re.compile(
    r"(\d+%|\d+\.\d+|\bp\s*[<=>]\s*|\bconfidence interval\b|\beffect size\b|"
    r"\bcauses?\b|\bcausal\b)",
    re.I,
)


def detect_hallucination(
    record: CitationRecord,
    crossref: dict | None,
    scholar: dict | None,
    openalex: dict | None,
    merged_override: dict | None = None,
) -> None:
    cited = record.bibliography

    resolved = merged_override or crossref or scholar or openalex
    if not resolved:
        record.hallucination_type = HallucinationType.NONE
        record.evidence_tier = EvidenceTier.TIER_4
        record.verdict_color = "unresolvable"
        return

    record.resolved_title = resolved.get("title")
    record.resolved_doi = resolved.get("doi") or cited.doi
    record.resolved_year = resolved.get("year")
    record.resolved_authors = coerce_author_list(resolved.get("authors") or [])
    record.retracted = bool(resolved.get("retracted"))

    if record.retracted:
        record.hallucination_type = HallucinationType.RETRACTION
        record.verdict_color = "retraction"
        record.evidence_tier = tier_from_resolved(resolved)
        return

    doi_metadata = crossref or (merged_override if cited.doi else None)
    if cited.doi and doi_metadata:
        title_mismatch = False
        if cited.title and doi_metadata.get("title"):
            ratio, _partial = compare_titles(cited.title, doi_metadata.get("title"))
            record.title_edit_distance = round((1 - ratio) * 100, 1)
            title_mismatch = ratio < 0.35
        resolved_authors = coerce_author_list(doi_metadata.get("authors") or [])
        author_equal = author_sets_equal(cited.authors, resolved_authors)
        author_mismatch = author_equal is False
        if title_mismatch or author_mismatch:
            record.hallucination_type = HallucinationType.DOI_REDIRECT
            record.verdict_color = "failure"
            record.evidence_tier = tier_from_resolved(doi_metadata)
            return

    record.hallucination_type = HallucinationType.NONE
    record.evidence_tier = tier_from_resolved(resolved)
    record.verdict_color = _color_for_success(record)


def _color_for_success(record: CitationRecord) -> str:
    if record.intent in {CitationIntent.METHODOLOGICAL, CitationIntent.BACKGROUND, CitationIntent.CONTRASTIVE}:
        return "neutral"
    if record.evidence_tier == EvidenceTier.TIER_3:
        return "cannot_assess"
    return "supported"


def extract_claim(context: str) -> str:
    sentences = split_sentences(context)
    if not sentences:
        return context.strip()
    return max(sentences, key=len)


def has_quantitative_language(claim: str) -> bool:
    return bool(QUANT_PATTERN.search(claim))


async def run_claim_alignment_async(record: CitationRecord) -> None:
    if record.intent != CitationIntent.EVIDENTIARY:
        record.nli_verdict = NliVerdict.SKIPPED
        return
    if record.evidence_tier not in {EvidenceTier.TIER_1, EvidenceTier.TIER_2}:
        record.claim_alignment_verdict = "cannot_determine"
        record.confidence = ConfidenceLevel.LOW
        record.verdict_color = "cannot_assess"
        return

    claim = record.claim_user_corrected or record.extracted_claim or ""
    evidence = record.evidence_passage or ""
    if not claim or not evidence:
        record.claim_alignment_verdict = "cannot_determine"
        record.confidence = ConfidenceLevel.LOW
        return

    nli_result = await nli_pipeline.classify_entailment(claim, evidence)
    if nli_result is None:
        _apply_lexical_fallback(record, claim, evidence)
    else:
        _apply_nli_verdict(record, nli_result)

    if has_quantitative_language(claim):
        record.quantitative_claim = True
        record.quantitative_caveat = (
            "Quantitative claim detected. NLI reasoning is reliable for logical contradiction "
            "and topic mismatch but may not detect numerical discrepancies or differences between "
            "causal and correlational language. Manual verification of the specific figures is recommended."
        )


def _set_human_review_flag(record: CitationRecord) -> None:
    if record.intent != CitationIntent.EVIDENTIARY:
        record.needs_human_review = False
        return
    if record.confidence in {ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW}:
        record.needs_human_review = True
    elif record.evidence_tier == EvidenceTier.TIER_2 and record.nli_verdict == NliVerdict.NEUTRAL:
        record.needs_human_review = True
    else:
        record.needs_human_review = False


def _apply_nli_verdict(record: CitationRecord, nli_result: NliVerdict) -> None:
    record.nli_verdict = nli_result
    verdict_label, confidence_token = nli_pipeline.confidence_for_verdict(nli_result, record.evidence_tier)
    record.claim_alignment_verdict = verdict_label
    record.confidence = ConfidenceLevel(confidence_token)
    _set_human_review_flag(record)
    if nli_result == NliVerdict.CONTRADICTS:
        record.hallucination_type = HallucinationType.CLAIM_CONTRADICTION
        record.verdict_color = "failure"
    elif nli_result == NliVerdict.ENTAILS:
        record.verdict_color = "supported"
    else:
        record.verdict_color = "amber" if record.evidence_tier == EvidenceTier.TIER_1 else "cannot_assess"


def _apply_lexical_fallback(record: CitationRecord, claim: str, evidence: str) -> None:
    overlap = difflib.SequenceMatcher(None, claim.lower(), evidence.lower()).ratio()
    if overlap >= 0.55:
        record.nli_verdict = NliVerdict.ENTAILS
        record.claim_alignment_verdict = "supported"
        record.confidence = (
            ConfidenceLevel.HIGH if record.evidence_tier == EvidenceTier.TIER_1 else ConfidenceLevel.MEDIUM
        )
        record.verdict_color = "supported"
        _set_human_review_flag(record)
        return
    elif overlap <= 0.25:
        record.nli_verdict = NliVerdict.CONTRADICTS
        record.hallucination_type = HallucinationType.CLAIM_CONTRADICTION
        record.claim_alignment_verdict = "claim_contradiction"
        record.confidence = ConfidenceLevel.MEDIUM
        record.verdict_color = "failure"
        _set_human_review_flag(record)
        return
    else:
        record.nli_verdict = NliVerdict.NEUTRAL
        record.claim_alignment_verdict = "not_addressed"
        record.confidence = ConfidenceLevel.MEDIUM
        record.verdict_color = "amber"
    _set_human_review_flag(record)


