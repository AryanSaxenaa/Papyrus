from __future__ import annotations

from app.config import get_settings
from app.domain.enums import EvidenceTier, HallucinationType
from app.domain.models import CitationRecord
from app.pipeline.verdicts import _tier_from_text, compare_titles
from app.services.embeddings import embedding_similarity


async def apply_title_drift_gate(
    record: CitationRecord,
    cited_title: str | None,
    crossref: dict | None,
) -> None:
    """Type 6 two-gate check: edit distance + semantic (token or embedding) mismatch."""
    if not cited_title or not crossref or not crossref.get("title"):
        return
    if record.hallucination_type not in {HallucinationType.NONE}:
        return

    resolved_title = crossref.get("title") or ""
    ratio, _partial = compare_titles(cited_title, resolved_title)
    record.title_edit_distance = round((1 - ratio) * 100, 1)

    settings = get_settings()
    if ratio >= settings.title_drift_ratio_threshold:
        return

    token_mismatch = ratio < settings.title_drift_token_threshold
    embed_mismatch = False
    similarity = await embedding_similarity(cited_title, resolved_title)
    if similarity is not None:
        embed_mismatch = similarity < 0.82

    if not (token_mismatch or embed_mismatch):
        return

    record.hallucination_type = HallucinationType.TITLE_DRIFT
    record.verdict_color = "failure"
    record.evidence_tier = _tier_from_text(crossref)
