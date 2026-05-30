from __future__ import annotations

from typing import Any
from uuid import UUID

from app.config import get_settings
from app.domain.models import AuditRun, CitationRecord
from app.pipeline.citation_graph import find_internal_cycles
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


async def _build_internal_adjacency(
    citations: list[CitationRecord],
    max_seeds: int,
) -> tuple[dict[str, int], dict[str, list[str]]]:
    doi_to_index: dict[str, int] = {}
    for record in citations:
        doi = _normalize_doi(record.resolved_doi or record.bibliography.doi)
        if doi:
            doi_to_index[doi] = record.index

    adjacency: dict[str, list[str]] = {doi: [] for doi in doi_to_index}
    checked = 0
    for record in citations:
        if checked >= max_seeds:
            break
        source_doi = _normalize_doi(record.resolved_doi or record.bibliography.doi)
        if not source_doi:
            continue
        checked += 1
        refs = await _reference_dois_cached(source_doi)
        adjacency[source_doi] = [r for r in refs if r in doi_to_index]

    return doi_to_index, adjacency


async def detect_circular_pairs(
    audit_id: UUID,
    citations: list[CitationRecord],
    doi_to_index: dict[str, int] | None = None,
    adjacency: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Direct reciprocal pairs (1-hop) within the bibliography."""
    settings = get_settings()
    if not settings.enable_circular_check:
        return []

    if doi_to_index is None or adjacency is None:
        doi_to_index, adjacency = await _build_internal_adjacency(citations, settings.circular_check_max_citations)
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for source_doi, refs in adjacency.items():
        for ref_doi in refs:
            if source_doi not in (adjacency.get(ref_doi) or []):
                continue
            key = tuple(sorted((source_doi, ref_doi)))
            if key in seen:
                continue
            seen.add(key)
            record_index = doi_to_index[source_doi]
            target_index = doi_to_index[ref_doi]
            pairs.append(
                {
                    "citation_a": record_index,
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
                f"Circular citation signal: #{record_index} ↔ #{target_index}",
                citation_index=record_index,
            )

    return pairs


async def detect_circular_cycles(
    audit_id: UUID,
    citations: list[CitationRecord],
    doi_to_index: dict[str, int] | None = None,
    adjacency: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Multi-hop cycles within bibliography (v2, depth-limited)."""
    settings = get_settings()
    if not settings.enable_circular_check or settings.circular_check_depth < 2:
        return []

    if doi_to_index is None or adjacency is None:
        doi_to_index, adjacency = await _build_internal_adjacency(citations, settings.circular_check_max_citations)
    cycles = find_internal_cycles(doi_to_index, adjacency, max_depth=settings.circular_check_depth)
    for cycle in cycles:
        indices = cycle.get("citation_indices") or []
        if indices:
            event_bus.emit(
                audit_id,
                "circular",
                f"Citation cycle detected: {' → '.join(f'#{i}' for i in indices)}",
                citation_index=indices[0],
            )
    return cycles


async def apply_quality_flags(audit_id: UUID, audit: AuditRun) -> None:
    duplicates = detect_duplicate_dois(audit.citations)
    settings = get_settings()
    doi_to_index: dict[str, int] | None = None
    adjacency: dict[str, list[str]] | None = None
    if settings.enable_circular_check:
        doi_to_index, adjacency = await _build_internal_adjacency(
            audit.citations, settings.circular_check_max_citations
        )
    circular_pairs = await detect_circular_pairs(audit_id, audit.citations, doi_to_index, adjacency)
    circular_cycles = await detect_circular_cycles(audit_id, audit.citations, doi_to_index, adjacency)

    for entry in duplicates:
        flag = f"Duplicate DOI {entry['doi']} at citations {entry['citation_indices']}"
        for record in audit.citations:
            if record.index in entry["citation_indices"]:
                record.quality_flags.append(flag)

    for pair in circular_pairs:
        for record in audit.citations:
            if record.index == pair["citation_a"]:
                record.quality_flags.append(f"Circular signal with citation #{pair['citation_b']}")
            if record.index == pair["citation_b"]:
                record.quality_flags.append(f"Circular signal with citation #{pair['citation_a']}")

    for cycle in circular_cycles:
        path = " → ".join(f"#{idx}" for idx in cycle.get("citation_indices", []))
        flag = f"Citation cycle ({cycle.get('length')} hops): {path}"
        for record in audit.citations:
            if record.index in cycle.get("citation_indices", []):
                record.quality_flags.append(flag)

    audit.quality_summary = {
        "duplicate_dois": duplicates,
        "circular_pairs": circular_pairs,
        "circular_cycles": circular_cycles,
        "circular_check_enabled": get_settings().enable_circular_check,
        "circular_check_depth": get_settings().circular_check_depth,
    }
