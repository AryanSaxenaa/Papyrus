from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.domain.enums import CitationIntent, ResolutionSource
from app.domain.models import AuditRun, CitationRecord
from app.pipeline.intent import apply_negation_override, classify_intent
from app.pipeline.scoring import finalize_scores
from app.pipeline.verdicts import (
    detect_hallucination,
    extract_claim,
    run_claim_alignment_stub,
)
from app.services.cache import cache_service
from app.services.crossref import crossref_client
from app.services.events import event_bus
from app.services.fallback_parser import parse_pdf_fallback
from app.services.grobid import grobid_client
from app.services.openalex import openalex_client
from app.services.semantic_scholar import semantic_scholar_client
from app.store import audit_store


class AuditOrchestrator:
    async def run(self, audit_id: UUID, pdf_path: Path) -> AuditRun:
        audit = audit_store.get(audit_id)
        if not audit:
            raise ValueError("Audit not found")

        audit.status = "running"
        event_bus.emit(audit_id, "ingestion", "PDF upload received", path=str(pdf_path))

        bibliography, inline, paper_title = await self._parse_pdf(audit_id, pdf_path)
        audit.paper_title = paper_title
        event_bus.emit(
            audit_id,
            "grobid",
            "Citation extraction complete",
            bibliography_count=len(bibliography),
            inline_count=len(inline),
        )

        audit.citations = self._build_records(bibliography, inline)
        for record in audit.citations:
            record.intent = classify_intent(record)
            record.intent = apply_negation_override(record)

        intent_counts = {}
        for record in audit.citations:
            intent_counts[record.intent.value] = intent_counts.get(record.intent.value, 0) + 1
        event_bus.emit(audit_id, "intent", "Intent classification complete", counts=intent_counts)

        await asyncio.gather(*(self._resolve_citation(audit_id, record) for record in audit.citations))

        for record in audit.citations:
            if record.intent == CitationIntent.EVIDENTIARY and record.inline_markers:
                context = record.inline_markers[0].context_window
                record.extracted_claim = extract_claim(context)
                record.evidence_passage = self._evidence_text(record)
                run_claim_alignment_stub(record)

        finalize_scores(audit)
        audit.status = "complete"
        from datetime import datetime

        audit.completed_at = datetime.utcnow()
        event_bus.emit(
            audit_id,
            "summary",
            "Audit complete",
            coverage=audit.coverage.coverage_percent,
            risk=audit.risk_level.value,
        )
        audit_store.save(audit)
        return audit

    async def _parse_pdf(self, audit_id: UUID, pdf_path: Path):
        settings = get_settings()
        if settings.grobid_enabled:
            try:
                bibliography, inline, title = await grobid_client.parse_pdf(pdf_path)
                filled = sum(1 for b in bibliography if b.title and (b.doi or b.year))
                if bibliography and filled / len(bibliography) >= 0.4:
                    return bibliography, inline, title
                event_bus.emit(
                    audit_id,
                    "grobid",
                    "Sparse GROBID output — routing to PyMuPDF fallback",
                )
            except Exception as exc:  # noqa: BLE001
                event_bus.emit(audit_id, "grobid", f"GROBID unavailable: {exc}")
        return parse_pdf_fallback(pdf_path)

    def _build_records(self, bibliography, inline) -> list[CitationRecord]:
        by_index = {entry.index: entry for entry in bibliography}
        markers_by_index: dict[int, list] = {}
        for marker in inline:
            markers_by_index.setdefault(marker.bibliography_index, []).append(marker)

        records: list[CitationRecord] = []
        for entry in bibliography:
            records.append(
                CitationRecord(
                    index=entry.index,
                    bibliography=entry,
                    inline_markers=markers_by_index.get(entry.index, []),
                )
            )
        if not records and inline:
            for marker in inline:
                if marker.bibliography_index not in by_index:
                    by_index[marker.bibliography_index] = bibliography[0] if bibliography else None
        return records

    async def _resolve_citation(self, audit_id: UUID, record: CitationRecord) -> None:
        record.status = "resolving"
        record.verdict_color = "resolving"
        cited = record.bibliography
        event_bus.emit(
            audit_id,
            "resolve",
            f"Resolving citation #{record.index}",
            citation_index=record.index,
            doi=cited.doi,
        )

        crossref = None
        scholar = None
        openalex = None

        if cited.doi:
            crossref = await cache_service.get_json("doi", cited.doi)
            if crossref is None:
                crossref = await crossref_client.resolve_doi(cited.doi)
                if crossref:
                    await cache_service.set_json("doi", cited.doi, crossref)
            record.resolution_attempts.append(
                self._attempt(ResolutionSource.CROSSREF, cited.doi, crossref is not None, crossref)
            )
            event_bus.emit(
                audit_id,
                "crossref",
                "CrossRef DOI lookup",
                citation_index=record.index,
                success=crossref is not None,
                title=(crossref or {}).get("title"),
            )

        if not crossref and cited.title:
            scholar = await semantic_scholar_client.search_title(cited.title)
            record.resolution_attempts.append(
                self._attempt(ResolutionSource.SEMANTIC_SCHOLAR, cited.title, scholar is not None, scholar)
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
                    self._attempt(ResolutionSource.OPENALEX, cited.title, openalex is not None, openalex)
                )
                event_bus.emit(
                    audit_id,
                    "openalex",
                    "OpenAlex title search",
                    citation_index=record.index,
                    success=openalex is not None,
                )

        detect_hallucination(record, crossref, scholar, openalex)
        record.status = "complete"
        event_bus.emit(
            audit_id,
            "verdict",
            f"Citation #{record.index} verdict assigned",
            citation_index=record.index,
            hallucination=record.hallucination_type.value,
            tier=record.evidence_tier.value,
            color=record.verdict_color,
        )

    def _attempt(self, source: ResolutionSource, query: str, success: bool, payload):
        from app.domain.models import ResolutionAttempt

        summary = "hit" if success else "miss"
        return ResolutionAttempt(
            source=source,
            query=query,
            success=success,
            summary=summary,
            payload=payload,
        )

    def _evidence_text(self, record: CitationRecord) -> str | None:
        for attempt in record.resolution_attempts:
            if attempt.payload:
                if attempt.payload.get("abstract"):
                    return attempt.payload["abstract"]
        if record.resolved_title:
            return record.resolved_title
        return None


audit_orchestrator = AuditOrchestrator()
