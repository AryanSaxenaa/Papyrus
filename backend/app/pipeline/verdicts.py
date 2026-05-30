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


QUANT_PATTERN = re.compile(
    r"(\d+%|\d+\.\d+|\bp\s*[<=>]\s*|\bconfidence interval\b|\beffect size\b|"
    r"\bcauses?\b|\bcausal\b)",
    re.I,
)


def compare_titles(cited: str | None, resolved: str | None) -> tuple[float, float]:
    if not cited or not resolved:
        return 0.0, 0.0
    cited_tokens = " ".join(sorted(cited.lower().split()))
    resolved_tokens = " ".join(sorted(resolved.lower().split()))
    ratio = difflib.SequenceMatcher(None, cited_tokens, resolved_tokens).ratio()
    partial = difflib.SequenceMatcher(None, cited.lower(), resolved.lower()).ratio()
    return ratio, partial


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
        if cited.doi:
            record.hallucination_type = HallucinationType.DOI_404
            record.evidence_tier = EvidenceTier.TIER_4
            record.verdict_color = "failure"
        else:
            record.hallucination_type = HallucinationType.NONE
            record.evidence_tier = EvidenceTier.TIER_4
            record.verdict_color = "unresolvable"
        return

    record.resolved_title = resolved.get("title")
    record.resolved_doi = resolved.get("doi") or cited.doi
    record.resolved_year = resolved.get("year")
    record.resolved_authors = resolved.get("authors") or []
    record.retracted = bool(resolved.get("retracted"))

    if record.retracted:
        record.hallucination_type = HallucinationType.RETRACTION
        record.verdict_color = "retraction"
        record.evidence_tier = _tier_from_text(resolved)
        return

    if cited.doi and crossref and cited.title:
        ratio, _partial = compare_titles(cited.title, crossref.get("title"))
        record.title_edit_distance = round((1 - ratio) * 100, 1)
        if ratio < 0.35:
            record.hallucination_type = HallucinationType.DOI_REDIRECT
            record.verdict_color = "failure"
            record.evidence_tier = _tier_from_text(crossref)
            return

    if cited.year and resolved.get("year") and cited.year != resolved.get("year") and crossref:
        record.hallucination_type = HallucinationType.DATE_IMPOSSIBLE
        record.verdict_color = "failure"
        record.evidence_tier = _tier_from_text(crossref)
        return

    record.hallucination_type = HallucinationType.NONE
    record.evidence_tier = _tier_from_text(resolved)
    record.verdict_color = _color_for_success(record)


def _tier_from_text(resolved: dict) -> EvidenceTier:
    if resolved.get("full_text"):
        return EvidenceTier.TIER_1
    if resolved.get("open_access_pdf") or resolved.get("oa_url"):
        return EvidenceTier.TIER_1
    if resolved.get("abstract"):
        return EvidenceTier.TIER_2
    if resolved.get("title"):
        return EvidenceTier.TIER_3
    return EvidenceTier.TIER_4


def _color_for_success(record: CitationRecord) -> str:
    if record.intent in {CitationIntent.METHODOLOGICAL, CitationIntent.BACKGROUND, CitationIntent.CONTRASTIVE}:
        return "neutral"
    if record.evidence_tier == EvidenceTier.TIER_3:
        return "cannot_assess"
    return "supported"


def extract_claim(context: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", context.strip())
    if not sentences:
        return context.strip()
    return max(sentences, key=len).strip()


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


def _apply_nli_verdict(record: CitationRecord, nli_result: NliVerdict) -> None:
    record.nli_verdict = nli_result
    verdict_label, confidence_token = nli_pipeline.confidence_for_verdict(nli_result, record.evidence_tier)
    record.claim_alignment_verdict = verdict_label
    record.confidence = ConfidenceLevel(confidence_token)
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
    elif overlap <= 0.25:
        record.nli_verdict = NliVerdict.CONTRADICTS
        record.hallucination_type = HallucinationType.CLAIM_CONTRADICTION
        record.claim_alignment_verdict = "claim_contradiction"
        record.confidence = ConfidenceLevel.MEDIUM
        record.verdict_color = "failure"
    else:
        record.nli_verdict = NliVerdict.NEUTRAL
        record.claim_alignment_verdict = "not_addressed"
        record.confidence = ConfidenceLevel.MEDIUM
        record.verdict_color = "amber"


