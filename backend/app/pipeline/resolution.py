from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.enums import EvidenceTier, HallucinationType, ResolutionSource
from app.domain.models import CitationRecord, ResolutionAttempt
from app.domain.enums import HallucinationType
from app.pipeline.verdicts import compare_titles, detect_hallucination
from app.services.arxiv import arxiv_client
from app.services.cache import cache_service
from app.services.crossref import crossref_client
from app.services.events import event_bus
from app.services.exa import exa_client
from app.services.openalex import openalex_client
from app.services.semantic_scholar import semantic_scholar_client
from app.services.unpaywall import unpaywall_client


def merge_resolved(
    crossref: dict | None,
    scholar: dict | None,
    openalex: dict | None,
    arxiv: dict | None,
    unpaywall: dict | None,
) -> dict[str, Any]:
    base = crossref or scholar or openalex or arxiv or {}
    merged = dict(base)
    for extra in (scholar, openalex, arxiv):
        if not extra:
            continue
        merged.setdefault("title", extra.get("title"))
        merged.setdefault("abstract", extra.get("abstract"))
        merged.setdefault("authors", extra.get("authors"))
        merged.setdefault("year", extra.get("year"))
        merged.setdefault("doi", extra.get("doi"))
    if unpaywall and unpaywall.get("open_access_pdf"):
        merged["open_access_pdf"] = unpaywall["open_access_pdf"]
        merged["oa_url"] = unpaywall.get("oa_url")
    return merged


async def resolve_record(audit_id: UUID, record: CitationRecord) -> dict[str, Any] | None:
    cited = record.bibliography
    crossref = None
    scholar = None
    openalex = None
    arxiv = None
    unpaywall = None

    if cited.doi:
        crossref = await cache_service.get_json("doi", cited.doi)
        if crossref is None:
            crossref = await crossref_client.resolve_doi(cited.doi)
            if crossref:
                await cache_service.set_json("doi", cited.doi, crossref)
        record.resolution_attempts.append(_attempt(ResolutionSource.CROSSREF, cited.doi, crossref is not None, crossref))
        event_bus.emit(
            audit_id,
            "crossref",
            "CrossRef DOI lookup",
            citation_index=record.index,
            success=crossref is not None,
            title=(crossref or {}).get("title"),
        )

        unpaywall = await cache_service.get_json("unpaywall", cited.doi)
        if unpaywall is None:
            unpaywall = await unpaywall_client.lookup(cited.doi)
            if unpaywall:
                await cache_service.set_json("unpaywall", cited.doi, unpaywall)
        record.resolution_attempts.append(
            _attempt(ResolutionSource.UNPAYWALL, cited.doi, bool(unpaywall and unpaywall.get("is_oa")), unpaywall)
        )
        if unpaywall and unpaywall.get("oa_url"):
            record.oa_pdf_url = unpaywall["oa_url"]

    arxiv_id = arxiv_client.extract_id(cited.doi) or arxiv_client.extract_id(cited.raw)
    if arxiv_id:
        arxiv = await arxiv_client.fetch(arxiv_id)
        record.resolution_attempts.append(
            _attempt(ResolutionSource.ARXIV, arxiv_id, arxiv is not None, arxiv)
        )
        event_bus.emit(
            audit_id,
            "arxiv",
            "arXiv metadata lookup",
            citation_index=record.index,
            success=arxiv is not None,
        )

    if not crossref and cited.title:
        scholar = await semantic_scholar_client.search_title(cited.title)
        record.resolution_attempts.append(
            _attempt(ResolutionSource.SEMANTIC_SCHOLAR, cited.title, scholar is not None, scholar)
        )
        event_bus.emit(
            audit_id,
            "semantic_scholar",
            "Semantic Scholar title search",
            citation_index=record.index,
            success=scholar is not None,
        )
        if not scholar:
            openalex = await openalex_client.search_title(cited.title)
            record.resolution_attempts.append(
                _attempt(ResolutionSource.OPENALEX, cited.title, openalex is not None, openalex)
            )
            event_bus.emit(
                audit_id,
                "openalex",
                "OpenAlex title search",
                citation_index=record.index,
                success=openalex is not None,
            )

    merged = merge_resolved(crossref, scholar, openalex, arxiv, unpaywall)
    detect_hallucination(record, crossref, scholar, openalex, merged_override=merged or None)

    if (
        record.hallucination_type == HallucinationType.NONE
        and arxiv
        and crossref
        and arxiv.get("title")
        and crossref.get("title")
    ):
        ratio, _ = compare_titles(arxiv["title"], crossref["title"])
        if ratio < 0.5:
            record.hallucination_type = HallucinationType.VERSION_MISMATCH
            record.verdict_color = "failure"

    if record.evidence_tier == EvidenceTier.TIER_4 and cited.title:
        exa = await exa_client.weak_signal_search(cited.title, cited.authors)
        record.resolution_attempts.append(
            _attempt(ResolutionSource.EXA, cited.title, exa.get("found", False), exa)
        )
        record.exa_signal = exa.get("message")
        event_bus.emit(
            audit_id,
            "exa",
            exa.get("message", "Exa search complete"),
            citation_index=record.index,
            found=exa.get("found", False),
        )

    doi = record.resolved_doi or cited.doi
    if doi:
        record.source_verify_url = f"https://doi.org/{doi}"
    elif record.oa_pdf_url:
        record.source_verify_url = record.oa_pdf_url

    return merged if merged else None


def _attempt(source: ResolutionSource, query: str, success: bool, payload: Any) -> ResolutionAttempt:
    return ResolutionAttempt(
        source=source,
        query=query,
        success=success,
        summary="hit" if success else "miss",
        payload=payload if isinstance(payload, dict) else {"result": payload},
    )
