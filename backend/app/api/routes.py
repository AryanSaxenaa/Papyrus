from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sse_starlette.sse import EventSourceResponse

from app.api.reports import render_json_report, render_text_report
from app.config import get_settings
from app.domain.enums import CitationIntent, NliVerdict
from app.bulk_store import bulk_job_store
from app.domain.models import (
    AuditRun,
    AuditSummary,
    BulkAuditJob,
    BulkDashboard,
    BulkDashboardPaper,
    CitationRecord,
)
from app.pipeline.orchestrator import audit_orchestrator
from app.pipeline.scoring import finalize_scores
from app.pipeline.evidence import refresh_evidence_passage
from app.pipeline.resolution import resolve_record
from app.pipeline.verdicts import extract_claim, run_claim_alignment_async
from app.services.deepseek import deepseek_client
from app.services.events import EventHistoryLoadError, event_bus
from app.services.corrections import correction_store
from app.services.relational_audit import list_citation_attempts
from app.services.background_dispatch import (
    celery_worker_available,
    enqueue_bulk_zip,
    enqueue_doi_audit,
    enqueue_pdf_audit,
    enqueue_url_audit,
)
from app.storage.files import bulk_zip_key, file_store, upload_key
from app.store import audit_store

router = APIRouter()


class IntentUpdate(BaseModel):
    intent: str


class ClaimUpdate(BaseModel):
    claim: str


class DoiAuditRequest(BaseModel):
    doi: str = Field(..., min_length=4, examples=["10.1038/s41586-021-03819-2"])


class UrlAuditRequest(BaseModel):
    url: str = Field(..., min_length=8, examples=["https://arxiv.org/abs/2301.00001"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "papyrus"}


@router.get("/health/detailed")
async def health_detailed() -> dict:
    settings = get_settings()
    checks: dict[str, dict] = {"api": {"ok": True}}

    try:
        from app.db.session import get_engine

        engine = get_engine()
        if engine is not None:
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["postgres"] = {"ok": True}
        else:
            checks["postgres"] = {"ok": False, "note": "not configured"}
    except SQLAlchemyError as exc:
        checks["postgres"] = {"ok": False, "error": str(exc)}

    try:
        from app.services.cache import cache_service

        checks["redis"] = {"ok": await cache_service.ping()}
    except (RedisError, OSError) as exc:
        checks["redis"] = {"ok": False, "error": str(exc)}

    if settings.grobid_enabled:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.grobid_url}/api/isalive")
                checks["grobid"] = {"ok": response.status_code == 200}
        except httpx.HTTPError as exc:
            checks["grobid"] = {"ok": False, "error": str(exc)}
    else:
        checks["grobid"] = {"ok": True, "skipped": True, "note": "GROBID_ENABLED=false"}

    celery_ready = await celery_worker_available()
    checks["background_queue"] = {
        "ok": True,
        "use_celery_background": settings.celery_background_enabled(),
        "celery_worker_available": celery_ready,
        "effective_mode": "celery" if celery_ready else "background_tasks",
        "file_storage_backend": settings.file_storage_backend,
    }

    return {"status": "ok" if all(c.get("ok") for c in checks.values()) else "degraded", "checks": checks}


@router.get("/audits/summaries")
async def list_audit_summaries() -> list[AuditSummary]:
    return audit_store.list_summaries()


@router.get("/audits")
async def list_audits() -> list[AuditRun]:
    return audit_store.list()


@router.delete("/audits/{audit_id}", status_code=204, response_class=Response)
async def delete_audit(audit_id: UUID) -> Response:
    if not audit_store.delete(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    return Response(status_code=204)


@router.get("/audits/{audit_id}/citations/{citation_id}/attempts")
async def get_citation_attempts(audit_id: UUID, citation_id: str) -> dict:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    attempts = list_citation_attempts(str(audit_id), citation_id)
    source = "postgres"
    if not attempts:
        source = "inline"
        attempts = [
            a.model_dump(mode="json", exclude_none=True) for a in record.resolution_attempts
        ]
    return {"citation_id": citation_id, "attempts": attempts, "source": source}


@router.get("/audits/{audit_id}")
async def get_audit(audit_id: UUID) -> AuditRun:
    from app.pipeline.limitations import build_limitations

    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status == "complete" and audit.limitations is None:
        audit.limitations = build_limitations(audit)
    return audit


@router.get("/audits/{audit_id}/paper.pdf")
async def get_audit_paper_pdf(audit_id: UUID) -> StreamingResponse:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    key = upload_key(str(audit_id))
    if not file_store.exists(key):
        raise HTTPException(status_code=404, detail="Source PDF not available for this audit")
    return StreamingResponse(
        iter([file_store.read_bytes(key)]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="papyrus-audit-{audit_id}.pdf"',
        },
    )


@router.post("/audits", status_code=202)
async def create_audit(background: BackgroundTasks, file: UploadFile) -> AuditRun:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {settings.max_upload_mb} MB limit")

    audit = AuditRun()
    storage_key = upload_key(str(audit.id))
    file_store.write_bytes(storage_key, content)
    audit_store.create(audit)
    await enqueue_pdf_audit(audit.id, storage_key, background)
    return audit


@router.post("/audits/doi", status_code=202)
async def create_doi_audit(background: BackgroundTasks, body: DoiAuditRequest) -> AuditRun:
    audit = AuditRun()
    audit_store.create(audit)
    await enqueue_doi_audit(audit.id, body.doi, background)
    return audit


@router.post("/audits/url", status_code=202)
async def create_url_audit(background: BackgroundTasks, body: UrlAuditRequest) -> AuditRun:
    audit = AuditRun(source_url=body.url)
    audit_store.create(audit)
    storage_key = upload_key(str(audit.id))
    await enqueue_url_audit(audit.id, body.url, storage_key, background)
    return audit


@router.post("/audits/bulk", status_code=202)
async def create_bulk_audit(background: BackgroundTasks, file: UploadFile) -> BulkAuditJob:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Bulk upload requires a ZIP of PDF files")

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024 * 4
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="ZIP exceeds upload size limit")

    job = BulkAuditJob()
    storage_key = bulk_zip_key(str(job.id))
    file_store.write_bytes(storage_key, content)
    bulk_job_store.create(job)
    queue_mode = await enqueue_bulk_zip(job.id, storage_key, background)
    event_bus.emit(
        job.id,
        "bulk",
        f"Bulk job queued ({queue_mode})",
        job_id=str(job.id),
    )
    return job


@router.get("/bulk/{job_id}")
async def get_bulk_job(job_id: UUID) -> BulkAuditJob:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    return job


@router.get("/bulk/{job_id}/audits")
async def list_bulk_audits(job_id: UUID) -> list[AuditRun]:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    audits: list[AuditRun] = []
    for audit_id in job.audit_ids:
        audit = audit_store.get(audit_id)
        if audit:
            audits.append(audit)
    return audits


@router.get("/bulk/{job_id}/events/history")
async def bulk_events_history(job_id: UUID) -> list[dict[str, object]]:
    if not bulk_job_store.get(job_id):
        raise HTTPException(status_code=404, detail="Bulk job not found")
    try:
        return event_bus.history(job_id)
    except EventHistoryLoadError as exc:
        raise HTTPException(
            status_code=503,
            detail="Event history temporarily unavailable",
        ) from exc


@router.get("/bulk/{job_id}/events")
async def stream_bulk_events(job_id: UUID) -> EventSourceResponse:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")

    async def generator():
        queue = await event_bus.subscribe(job_id)
        redis_task = asyncio.create_task(event_bus.listen_redis(job_id, queue))
        try:
            while True:
                event = await queue.get()
                yield {"event": event["type"], "data": json.dumps(event, default=str)}
        except asyncio.CancelledError:
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            event_bus.unsubscribe(job_id, queue)
            raise

    return EventSourceResponse(generator())


@router.get("/bulk/{job_id}/dashboard")
async def bulk_dashboard(job_id: UUID) -> BulkDashboard:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")

    papers: list[BulkDashboardPaper] = []
    for audit_id in job.audit_ids:
        audit = audit_store.get(audit_id)
        if not audit:
            continue
        resolvable = audit.coverage.tier_1 + audit.coverage.tier_2 + audit.coverage.tier_3
        first_author = audit.paper_authors[0] if audit.paper_authors else None
        papers.append(
            BulkDashboardPaper(
                audit_id=str(audit.id),
                title=audit.paper_title,
                first_author=first_author,
                status=audit.status,
                coverage_percent=audit.coverage.coverage_percent,
                confirmed_failure_rate=audit.failures.confirmed_failure_rate,
                risk_level=audit.risk_level.value,
                resolvable_citations=resolvable,
                type_1=audit.failures.type_1,
                type_2=audit.failures.type_2,
                type_5=audit.failures.type_5,
                type_6=audit.failures.type_6,
                type_7=audit.failures.type_7,
                retraction=audit.failures.retraction,
                version_mismatch=audit.failures.version_mismatch,
            )
        )

    papers.sort(key=lambda row: row.confirmed_failure_rate, reverse=True)
    pending = sum(1 for row in papers if row.status in {"queued", "running"})
    return BulkDashboard(
        job=job,
        papers=papers,
        pending_papers=pending,
        note="Ranked by confirmed failure rate among resolvable citations, not unresolvable count.",
    )


@router.get("/bulk/{job_id}/events/log.txt")
async def export_bulk_event_log(job_id: UUID) -> StreamingResponse:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")
    try:
        events = event_bus.history(job_id)
    except EventHistoryLoadError as exc:
        raise HTTPException(
            status_code=503,
            detail="Event history temporarily unavailable",
        ) from exc
    lines = []
    for event in events:
        lines.append(f"{event.get('ts', '')} [{event.get('type', '')}] {event.get('message', '')}")
    return StreamingResponse(iter(["\n".join(lines)]), media_type="text/plain")


@router.get("/bulk/{job_id}/dashboard.json")
async def export_bulk_dashboard_json(job_id: UUID) -> JSONResponse:
    payload = await bulk_dashboard(job_id)
    return JSONResponse(content=payload.model_dump(mode="json"))


@router.get("/audits/{audit_id}/events/log.txt")
async def export_event_log(audit_id: UUID) -> StreamingResponse:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    try:
        events = event_bus.history(audit_id)
    except EventHistoryLoadError as exc:
        raise HTTPException(
            status_code=503,
            detail="Event history temporarily unavailable",
        ) from exc
    lines = []
    for event in events:
        lines.append(f"{event.get('ts', '')} [{event.get('type', '')}] {event.get('message', '')}")
    return StreamingResponse(iter(["\n".join(lines)]), media_type="text/plain")


@router.get("/audits/{audit_id}/events/history")
async def audit_events_history(audit_id: UUID) -> list[dict[str, object]]:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    try:
        return event_bus.history(audit_id)
    except EventHistoryLoadError as exc:
        raise HTTPException(
            status_code=503,
            detail="Event history temporarily unavailable",
        ) from exc


@router.get("/audits/{audit_id}/events")
async def stream_events(audit_id: UUID) -> EventSourceResponse:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")

    async def generator():
        queue = await event_bus.subscribe(audit_id)
        redis_task = asyncio.create_task(event_bus.listen_redis(audit_id, queue))
        try:
            while True:
                event = await queue.get()
                yield {"event": event["type"], "data": json.dumps(event, default=str)}
        except asyncio.CancelledError:
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            event_bus.unsubscribe(audit_id, queue)
            raise

    return EventSourceResponse(generator())


@router.patch("/audits/{audit_id}/citations/{citation_id}/intent")
async def update_intent(audit_id: UUID, citation_id: str, body: IntentUpdate) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    previous = record.intent.value
    record.intent = CitationIntent(body.intent)
    record.intent_user_override = True
    if record.intent == CitationIntent.EVIDENTIARY:
        context = record.inline_markers[0].context_window if record.inline_markers else ""
        if context and not record.extracted_claim:
            claim = await deepseek_client.extract_claim(context)
            record.extracted_claim = claim or extract_claim(context)
        await refresh_evidence_passage(record)
        await run_claim_alignment_async(record)
    else:
        record.nli_verdict = NliVerdict.SKIPPED
        record.claim_alignment_verdict = None
        record.claim_pending_review = False
        from app.pipeline.verdicts import _color_for_success

        record.verdict_color = _color_for_success(record)
    correction_store.record(
        str(audit_id),
        citation_id,
        record.index,
        "intent",
        previous,
        body.intent,
    )
    finalize_scores(audit)
    audit_store.save(audit)
    event_bus.emit(audit_id, "user", "Intent reclassified", citation_index=record.index, intent=body.intent)
    return record


@router.patch("/audits/{audit_id}/citations/{citation_id}/claim")
async def update_claim(audit_id: UUID, citation_id: str, body: ClaimUpdate) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    original = record.extracted_claim
    record.claim_user_corrected = body.claim
    record.claim_pending_review = False
    correction_store.record(
        str(audit_id),
        citation_id,
        record.index,
        "claim",
        original,
        body.claim,
    )
    await _rerun_claim_alignment(record)
    finalize_scores(audit)
    audit_store.save(audit)
    event_bus.emit(
        audit_id,
        "nli",
        "Claim alignment rerun after user correction",
        citation_index=record.index,
        verdict=record.claim_alignment_verdict,
    )
    return record


async def _rerun_claim_alignment(record: CitationRecord) -> None:
    if record.intent != CitationIntent.EVIDENTIARY:
        record.nli_verdict = NliVerdict.SKIPPED
        return
    if not record.extracted_claim and not record.claim_user_corrected:
        raise HTTPException(status_code=400, detail="No claim available for NLI")
    record.claim_pending_review = False
    await refresh_evidence_passage(record)
    await run_claim_alignment_async(record)


@router.post("/audits/{audit_id}/citations/{citation_id}/approve-claim")
async def approve_claim(audit_id: UUID, citation_id: str) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    if not record.extracted_claim and not record.claim_user_corrected:
        raise HTTPException(status_code=400, detail="No claim to approve")
    await _rerun_claim_alignment(record)
    finalize_scores(audit)
    audit_store.save(audit)
    event_bus.emit(
        audit_id,
        "nli",
        "NLI run after claim approval",
        citation_index=record.index,
        verdict=record.claim_alignment_verdict,
    )
    return record



@router.post("/audits/{audit_id}/citations/{citation_id}/rerun-nli")
async def rerun_nli(audit_id: UUID, citation_id: str) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    await _rerun_claim_alignment(record)
    finalize_scores(audit)
    audit_store.save(audit)
    event_bus.emit(
        audit_id,
        "nli",
        "NLI rerun (claim alignment only)",
        citation_index=record.index,
        verdict=record.claim_alignment_verdict,
    )
    return record


@router.post("/audits/{audit_id}/citations/{citation_id}/rerun")
async def rerun_citation(audit_id: UUID, citation_id: str) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    record.status = "resolving"
    record.verdict_color = "resolving"
    await resolve_record(audit_id, record)
    record.status = "complete"
    if record.intent == CitationIntent.EVIDENTIARY and not record.claim_pending_review:
        await refresh_evidence_passage(record)
        await run_claim_alignment_async(record)
    finalize_scores(audit)
    audit_store.save(audit)
    event_bus.emit(audit_id, "verdict", "Citation rerun complete", citation_index=record.index)
    return record


@router.get("/audits/{audit_id}/report.txt")
async def export_text_report(audit_id: UUID) -> StreamingResponse:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return StreamingResponse(iter([render_text_report(audit)]), media_type="text/plain")


@router.get("/audits/{audit_id}/report.json")
async def export_json_report(audit_id: UUID) -> JSONResponse:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return JSONResponse(content=json.loads(render_json_report(audit)))


@router.get("/audits/{audit_id}/report.pdf")
async def export_pdf_report(audit_id: UUID) -> StreamingResponse:
    from app.api.reports import render_pdf_bytes

    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    pdf_bytes = render_pdf_bytes(audit)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="papyrus-audit-{audit_id}.pdf"'},
    )


def _get_citation(audit: AuditRun, citation_id: str) -> CitationRecord:
    for citation in audit.citations:
        if citation.id == citation_id:
            return citation
    raise HTTPException(status_code=404, detail="Citation not found")


