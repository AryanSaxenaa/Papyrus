from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.domain.enums import CitationIntent, NliVerdict
from app.domain.models import AuditRun, BibliographyEntry, CitationRecord
from app.pipeline.evidence import refresh_evidence_passage
from app.pipeline.intent import apply_negation_override, classify_intent
from app.pipeline.llm import (
    classify_intent as llm_classify_intent,
    extract_claim as llm_extract_claim,
)
from app.pipeline.resolution import resolve_record
from app.pipeline.scoring import finalize_scores
from app.pipeline.verdicts import extract_claim, run_claim_alignment_async
from app.services.events import event_bus
from app.services.fallback_parser import parse_pdf_fallback
from app.services.grobid import grobid_client
from app.services.pdf_text import extract_paper_text
from app.store import audit_store
from app.text.identifiers import normalize_doi


class AuditOrchestrator:
    async def run(self, audit_id: UUID, pdf_path: Path) -> AuditRun:
        audit = audit_store.get(audit_id)
        if not audit:
            raise ValueError("Audit not found")

        audit.status = "running"
        audit_store.save(audit)
        event_bus.emit(audit_id, "ingestion", "PDF upload received", path=str(pdf_path))

        bibliography, inline, paper_title, paper_authors = await self._parse_pdf(audit_id, pdf_path)
        audit.paper_title = paper_title
        audit.paper_authors = paper_authors
        try:
            audit.paper_text = extract_paper_text(pdf_path)
        except (OSError, RuntimeError, ValueError):
            audit.paper_text = None
        event_bus.emit(
            audit_id,
            "ingestion",
            "Citation extraction complete",
            bibliography_count=len(bibliography),
            inline_count=len(inline),
        )

        audit.citations = self._build_records(bibliography, inline)
        audit_store.save(audit)
        await self._classify_intents(audit_id, audit)
        audit_store.save(audit)
        await self._resolve_all(audit_id, audit)
        await self._align_claims(audit_id, audit)

        finalize_scores(audit)
        audit.status = "complete"
        audit.completed_at = datetime.now(timezone.utc)
        event_bus.emit(
            audit_id,
            "summary",
            "Audit complete",
            coverage=audit.coverage.coverage_percent,
            risk=audit.risk_level.value,
        )
        audit_store.save(audit)
        return audit

    async def run_doi(self, audit_id: UUID, doi: str) -> AuditRun:
        audit = audit_store.get(audit_id)
        if not audit:
            raise ValueError("Audit not found")

        normalized = normalize_doi(doi)
        audit.status = "running"
        audit_store.save(audit)
        audit.paper_title = f"DOI verification: {normalized}"
        event_bus.emit(audit_id, "ingestion", "Single DOI verification started", doi=normalized)

        entry = BibliographyEntry(index=1, raw=normalized, doi=normalized, title=None)
        record = CitationRecord(index=1, bibliography=entry, intent=CitationIntent.EVIDENTIARY)
        audit.citations = [record]

        await resolve_record(audit_id, record)
        record.extracted_claim = None
        record.status = "complete"
        finalize_scores(audit)
        audit.status = "complete"
        audit.completed_at = datetime.now(timezone.utc)
        audit_store.save(audit)
        event_bus.emit(audit_id, "summary", "DOI verification complete", doi=normalized)
        return audit

    async def _classify_intents(self, audit_id: UUID, audit: AuditRun) -> None:
        for record in audit.citations:
            context = " ".join(marker.context_window for marker in record.inline_markers)
            intent = None
            if context:
                intent = await llm_classify_intent(context)
            record.intent = intent or classify_intent(record)
            record.intent = apply_negation_override(record)

        intent_counts: dict[str, int] = {}
        for record in audit.citations:
            intent_counts[record.intent.value] = intent_counts.get(record.intent.value, 0) + 1
        event_bus.emit(audit_id, "intent", "Intent classification complete", counts=intent_counts)

    async def _resolve_all(self, audit_id: UUID, audit: AuditRun) -> None:
        async def _one(record: CitationRecord) -> None:
            record.status = "resolving"
            record.verdict_color = "resolving"
            try:
                await resolve_record(audit_id, record)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                record.status = "failed"
                record.verdict_color = "unresolvable"
                event_bus.emit(
                    audit_id,
                    "error",
                    f"Citation #{record.index} resolution failed: {_format_pipeline_error(exc)}",
                    citation_index=record.index,
                )
                return
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

        sem = asyncio.Semaphore(2)

        async def _limited(record: CitationRecord) -> None:
            async with sem:
                await _one(record)

        await asyncio.gather(*(_limited(record) for record in audit.citations))
        audit_store.save(audit)

    async def _align_claims(self, audit_id: UUID, audit: AuditRun) -> None:
        settings = get_settings()
        
        async def _process_claim(record: CitationRecord) -> None:
            if record.intent != CitationIntent.EVIDENTIARY:
                return
            context = record.inline_markers[0].context_window if record.inline_markers else ""
            if context:
                claim = await llm_extract_claim(context)
                record.extracted_claim = claim or extract_claim(context)
                event_bus.emit(
                    audit_id,
                    "claim",
                    "Claim extracted",
                    citation_index=record.index,
                    claim=(record.extracted_claim or "")[:120],
                )
            record.intent = apply_negation_override(record)
            await refresh_evidence_passage(record)
            if settings.nli_requires_claim_approval and not record.claim_user_corrected:
                record.claim_pending_review = True
                record.nli_verdict = NliVerdict.SKIPPED
                event_bus.emit(
                    audit_id,
                    "claim",
                    "Awaiting user claim approval before NLI",
                    citation_index=record.index,
                )
                return
            record.claim_pending_review = False
            await run_claim_alignment_async(record)
        
        claim_results = await asyncio.gather(
            *(_process_claim(record) for record in audit.citations),
            return_exceptions=True,
        )
        for record, result in zip(audit.citations, claim_results, strict=True):
            if isinstance(result, BaseException):
                event_bus.emit(
                    audit_id,
                    "error",
                    f"Citation #{record.index} claim alignment failed: {result}",
                    citation_index=record.index,
                )

    async def run_from_url(self, audit_id: UUID, source_url: str, pdf_path: Path) -> AuditRun:
        audit = audit_store.get(audit_id)
        if not audit:
            raise ValueError("Audit not found")
        audit.source_url = source_url
        audit_store.save(audit)
        return await self.run(audit_id, pdf_path)

    async def _parse_pdf(self, audit_id: UUID, pdf_path: Path):
        settings = get_settings()
        if settings.grobid_enabled:
            try:
                bibliography, inline, title, paper_authors = await grobid_client.parse_pdf(pdf_path)
                filled = sum(1 for b in bibliography if b.title and (b.doi or b.year))
                min_fill = settings.grobid_min_bibliography_fill_ratio
                if bibliography and filled / len(bibliography) >= min_fill:
                    return bibliography, inline, title, paper_authors
                event_bus.emit(audit_id, "grobid", "Sparse GROBID output — routing to PyMuPDF fallback")
            except Exception as exc:  # noqa: BLE001
                event_bus.emit(audit_id, "grobid", f"GROBID unavailable: {exc}")
        bibliography, inline, paper_title, paper_authors = parse_pdf_fallback(pdf_path)
        if settings.enable_llm_pdf_ingestion:
            from app.pipeline.llm import parse_pdf_citations as llm_parse_pdf_citations

            try:
                import fitz

                doc = fitz.open(pdf_path)
                text = "\n".join(page.get_text() for page in doc)
                doc.close()
                parsed = await llm_parse_pdf_citations(text)
                if parsed:
                    return parsed
                event_bus.emit(
                    audit_id,
                    "ingestion",
                    "LLM PDF parse returned no usable bibliography — using PyMuPDF output",
                )
            except (OSError, RuntimeError, ValueError) as exc:
                event_bus.emit(
                    audit_id,
                    "ingestion",
                    f"LLM PDF parse failed: {exc}",
                )
        return bibliography, inline, paper_title, paper_authors

    def _build_records(self, bibliography, inline) -> list[CitationRecord]:
        markers_by_index: dict[int, list] = {}
        for marker in inline:
            markers_by_index.setdefault(marker.bibliography_index, []).append(marker)

        return [
            CitationRecord(
                index=entry.index,
                bibliography=entry,
                inline_markers=markers_by_index.get(entry.index, []),
            )
            for entry in bibliography
        ]

def _format_pipeline_error(exc: BaseException) -> str:
    message = str(exc).strip()
    if message:
        return message
    return f"{type(exc).__name__} (no message)"


audit_orchestrator = AuditOrchestrator()
