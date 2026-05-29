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
from app.domain.models import AuditRun, CitationRecord
from app.pipeline.orchestrator import audit_orchestrator
from app.pipeline.scoring import finalize_scores
from app.pipeline.verdicts import run_claim_alignment_stub
from app.services.events import event_bus
from app.store import audit_store

router = APIRouter()


class IntentUpdate(BaseModel):
    intent: str


class ClaimUpdate(BaseModel):
    claim: str


class DoiAuditRequest(BaseModel):
    doi: str = Field(..., min_length=4, examples=["10.1038/s41586-021-03819-2"])


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
    run_claim_alignment_stub(record)
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


def _fail_audit(audit_id: UUID, exc: Exception) -> None:
    audit = audit_store.get(audit_id)
    if audit:
        audit.status = "failed"
        audit.error = str(exc)
        audit_store.save(audit)
    event_bus.emit(audit_id, "error", f"Audit failed: {exc}")
