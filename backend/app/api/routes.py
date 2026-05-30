from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.api.reports import render_json_report, render_text_report
from app.config import get_settings
from app.domain.enums import CitationIntent
from app.bulk_store import bulk_job_store
from app.domain.models import AuditRun, BulkAuditJob, CitationRecord
from app.pipeline.bulk import process_bulk_zip
from app.pipeline.orchestrator import audit_orchestrator
from app.pipeline.scoring import finalize_scores
from app.pipeline.verdicts import run_claim_alignment_async
from app.services.events import event_bus
from app.services.url_fetch import url_fetch_service
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


@router.get("/audits")
async def list_audits() -> list[AuditRun]:
    return audit_store.list()


@router.get("/audits/{audit_id}")
async def get_audit(audit_id: UUID) -> AuditRun:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.post("/audits", status_code=202)
async def create_audit(background: BackgroundTasks, file: UploadFile) -> AuditRun:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    audit = AuditRun()
    destination = upload_dir / f"{audit.id}.pdf"
    with destination.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    audit_store.create(audit)
    background.add_task(_run_pdf_audit, audit.id, destination)
    return audit


@router.post("/audits/doi", status_code=202)
async def create_doi_audit(background: BackgroundTasks, body: DoiAuditRequest) -> AuditRun:
    audit = AuditRun()
    audit_store.create(audit)
    background.add_task(_run_doi_audit, audit.id, body.doi)
    return audit


@router.post("/audits/url", status_code=202)
async def create_url_audit(background: BackgroundTasks, body: UrlAuditRequest) -> AuditRun:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    audit = AuditRun(source_url=body.url)
    destination = upload_dir / f"{audit.id}.pdf"
    audit_store.create(audit)
    background.add_task(_run_url_audit, audit.id, body.url, destination)
    return audit


@router.post("/audits/bulk", status_code=202)
async def create_bulk_audit(background: BackgroundTasks, file: UploadFile) -> BulkAuditJob:
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Bulk upload requires a ZIP of PDF files")

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / "bulk"
    upload_dir.mkdir(parents=True, exist_ok=True)

    job = BulkAuditJob()
    zip_path = upload_dir / f"{job.id}.zip"
    with zip_path.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    bulk_job_store.create(job)
    background.add_task(_run_bulk_job, job.id, zip_path)
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


@router.get("/bulk/{job_id}/dashboard")
async def bulk_dashboard(job_id: UUID) -> dict:
    job = bulk_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Bulk job not found")

    papers = []
    for audit_id in job.audit_ids:
        audit = audit_store.get(audit_id)
        if not audit:
            continue
        resolvable = audit.coverage.tier_1 + audit.coverage.tier_2 + audit.coverage.tier_3
        papers.append(
            {
                "audit_id": str(audit.id),
                "title": audit.paper_title,
                "status": audit.status,
                "coverage_percent": audit.coverage.coverage_percent,
                "confirmed_failure_rate": audit.failures.confirmed_failure_rate,
                "risk_level": audit.risk_level.value,
                "resolvable_citations": resolvable,
                "type_1": audit.failures.type_1,
                "type_2": audit.failures.type_2,
                "type_7": audit.failures.type_7,
                "retraction": audit.failures.retraction,
            }
        )

    papers.sort(key=lambda row: row["confirmed_failure_rate"], reverse=True)
    return {
        "job": job.model_dump(mode="json"),
        "papers": papers,
        "note": "Ranked by confirmed failure rate among resolvable citations, not unresolvable count.",
    }


@router.get("/audits/{audit_id}/events/log.txt")
async def export_event_log(audit_id: UUID) -> StreamingResponse:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")
    lines = []
    for event in event_bus.history(audit_id):
        lines.append(f"{event.get('ts', '')} [{event.get('type', '')}] {event.get('message', '')}")
    return StreamingResponse(iter(["\n".join(lines)]), media_type="text/plain")


@router.get("/audits/{audit_id}/events")
async def stream_events(audit_id: UUID) -> EventSourceResponse:
    if not audit_store.get(audit_id):
        raise HTTPException(status_code=404, detail="Audit not found")

    async def generator():
        queue = await event_bus.subscribe(audit_id)
        try:
            while True:
                event = await queue.get()
                yield {"event": event["type"], "data": json.dumps(event, default=str)}
        except asyncio.CancelledError:
            event_bus.unsubscribe(audit_id, queue)
            raise

    return EventSourceResponse(generator())


@router.patch("/audits/{audit_id}/citations/{citation_id}/intent")
async def update_intent(audit_id: UUID, citation_id: str, body: IntentUpdate) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    record.intent = CitationIntent(body.intent)
    record.intent_user_override = True
    finalize_scores(audit)
    audit_store.save(audit)
    return record


@router.patch("/audits/{audit_id}/citations/{citation_id}/claim")
async def update_claim(audit_id: UUID, citation_id: str, body: ClaimUpdate) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    record = _get_citation(audit, citation_id)
    record.claim_user_corrected = body.claim
    await run_claim_alignment_async(record)
    finalize_scores(audit)
    audit_store.save(audit)
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


async def _run_pdf_audit(audit_id: UUID, pdf_path: Path) -> None:
    try:
        await audit_orchestrator.run(audit_id, pdf_path)
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)


async def _run_doi_audit(audit_id: UUID, doi: str) -> None:
    try:
        await audit_orchestrator.run_doi(audit_id, doi)
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)


async def _run_url_audit(audit_id: UUID, url: str, destination: Path) -> None:
    try:
        await url_fetch_service.download_pdf(url, destination)
        await audit_orchestrator.run_from_url(audit_id, url, destination)
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)


async def _run_bulk_job(job_id: UUID, zip_path: Path) -> None:
    try:
        await process_bulk_zip(job_id, zip_path)
    except Exception:
        return


def _fail_audit(audit_id: UUID, exc: Exception) -> None:
    audit = audit_store.get(audit_id)
    if audit:
        audit.status = "failed"
        audit.error = str(exc)
        audit_store.save(audit)
    event_bus.emit(audit_id, "error", f"Audit failed: {exc}")
