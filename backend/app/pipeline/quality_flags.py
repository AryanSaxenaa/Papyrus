from __future__ import annotations

from typing import Any
from uuid import UUID

from app.config import get_settings
from app.domain.models import AuditRun, CitationRecord
from app.services.cache import cache_service
from app.services.events import event_bus
from app.services.semantic_scholar import semantic_scholar_client


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    return doi.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/").lower()


def detect_duplicate_dois(citations: list[CitationRecord]) -> list[dict[str, Any]]:
    by_doi: dict[str, list[int]] = {}
    for record in citations:
        doi = _normalize_doi(record.resolved_doi or record.bibliography.doi)
        if not doi:
            continue
        by_doi.setdefault(doi, []).append(record.index)
    return [
        {"doi": doi, "citation_indices": indices}
        for doi, indices in by_doi.items()
        if len(indices) > 1
    ]


async def _reference_dois_cached(doi: str) -> list[str]:
    cache_key = _normalize_doi(doi) or doi
    cached = await cache_service.get_json("s2_refs", cache_key)
    if cached is not None:
        return cached.get("dois", [])
    dois = await semantic_scholar_client.reference_dois(doi)
    await cache_service.set_json("s2_refs", cache_key, {"dois": dois})
    return dois


async def detect_circular_pairs(audit_id: UUID, citations: list[CitationRecord]) -> list[dict[str, Any]]:
    """v2 preview: flag reciprocal DOI pairs within the same bibliography (signal only, not a verdict)."""
    settings = get_settings()
    if not settings.enable_circular_check:
        return []

    doi_to_index: dict[str, int] = {}
    for record in citations:
        doi = _normalize_doi(record.resolved_doi or record.bibliography.doi)
        if doi:
            doi_to_index[doi] = record.index

    if len(doi_to_index) < 2:
        return []

    checked = 0
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for record in citations:
        if checked >= settings.circular_check_max_citations:
            break
        source_doi = _normalize_doi(record.resolved_doi or record.bibliography.doi)
        if not source_doi:
            continue
        checked += 1
        refs = await _reference_dois_cached(source_doi)
        for ref_doi in refs:
            target_index = doi_to_index.get(ref_doi)
            if target_index is None or target_index == record.index:
                continue
            back_refs = await _reference_dois_cached(ref_doi)
            if source_doi not in back_refs:
                continue
            key = tuple(sorted((source_doi, ref_doi)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append(
                {
                    "citation_a": record.index,
                    "citation_b": target_index,
                    "doi_a": source_doi,
                    "doi_b": ref_doi,
                    "note": (
                        "Reciprocal bibliography link detected via Semantic Scholar references. "
                        "This is a methodological signal, not a hallucination verdict."
                    ),
                }
            )
            event_bus.emit(
                audit_id,
                "circular",
                f"Circular citation signal: #{record.index} ↔ #{target_index}",
                citation_index=record.index,
            )

    return pairs


async def apply_quality_flags(audit_id: UUID, audit: AuditRun) -> None:
    duplicates = detect_duplicate_dois(audit.citations)
    circular = await detect_circular_pairs(audit_id, audit.citations)

    for entry in duplicates:
        flag = f"Duplicate DOI {entry['doi']} at citations {entry['citation_indices']}"
        for record in audit.citations:
            if record.index in entry["citation_indices"]:
                record.quality_flags.append(flag)

    for pair in circular:
        for record in audit.citations:
            if record.index == pair["citation_a"]:
                record.quality_flags.append(f"Circular signal with citation #{pair['citation_b']}")
            if record.index == pair["citation_b"]:
                record.quality_flags.append(f"Circular signal with citation #{pair['citation_a']}")

    audit.quality_summary = {
        "duplicate_dois": duplicates,
        "circular_pairs": circular,
        "circular_check_enabled": get_settings().enable_circular_check,
    }
