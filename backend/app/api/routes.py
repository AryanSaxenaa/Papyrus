from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.domain.models import AuditRun, CitationRecord
from app.pipeline.orchestrator import audit_orchestrator
from app.services.events import event_bus
from app.store import audit_store

router = APIRouter()


class IntentUpdate(BaseModel):
    intent: str


class ClaimUpdate(BaseModel):
    claim: str


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
    settings = get_settings()
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported in v1")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    audit = AuditRun()
    destination = upload_dir / f"{audit.id}.pdf"
    with destination.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    audit_store.create(audit)
    background.add_task(_run_audit, audit.id, destination)
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
    record = _get_citation(audit_id, citation_id)
    from app.domain.enums import CitationIntent

    record.intent = CitationIntent(body.intent)
    record.intent_user_override = True
    audit_store.save(audit_store.get(audit_id))  # type: ignore[arg-type]
    return record


@router.patch("/audits/{audit_id}/citations/{citation_id}/claim")
async def update_claim(audit_id: UUID, citation_id: str, body: ClaimUpdate) -> CitationRecord:
    record = _get_citation(audit_id, citation_id)
    record.claim_user_corrected = body.claim
    from app.pipeline.verdicts import run_claim_alignment_stub

    run_claim_alignment_stub(record)
    audit_store.save(audit_store.get(audit_id))  # type: ignore[arg-type]
    return record


@router.get("/audits/{audit_id}/report.txt")
async def export_report(audit_id: UUID) -> StreamingResponse:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    text = _render_report(audit)
    return StreamingResponse(iter([text]), media_type="text/plain")


def _get_citation(audit_id: UUID, citation_id: str) -> CitationRecord:
    audit = audit_store.get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    for citation in audit.citations:
        if citation.id == citation_id:
            return citation
    raise HTTPException(status_code=404, detail="Citation not found")


async def _run_audit(audit_id: UUID, pdf_path: Path) -> None:
    try:
        await audit_orchestrator.run(audit_id, pdf_path)
    except Exception as exc:  # noqa: BLE001
        audit = audit_store.get(audit_id)
        if audit:
            audit.status = "failed"
            audit.error = str(exc)
            audit_store.save(audit)
        event_bus.emit(audit_id, "error", f"Audit failed: {exc}")


def _render_report(audit: AuditRun) -> str:
    title = (audit.paper_title or "Untitled")[:80]
    lines = [
        "═══════════════════════════════════════════════════════════════",
        " PAPYRUS — CITATION INTEGRITY AUDIT",
        f" Paper: {title}",
        f" Analyzed: {audit.completed_at or audit.created_at}  |  Pipeline version: {audit.pipeline_version}",
        "═══════════════════════════════════════════════════════════════",
        "",
        " CITATION VERIFICATION COVERAGE",
        " ────────────────────────────────────────────────────────────",
        f" Total citations extracted:                              {audit.coverage.total:>3}",
        f" Resolved (Tier 1 — full text):                          {audit.coverage.tier_1:>3}",
        f" Resolved (Tier 2 — abstract only):                      {audit.coverage.tier_2:>3}",
        f" Resolved (Tier 3 — metadata only):                      {audit.coverage.tier_3:>3}",
        f" Unresolvable (outside indexed sources):                 {audit.coverage.tier_4:>3}",
        " ────────────────────────────────────────────────────────────",
        f" Coverage score:                                        {audit.coverage.coverage_percent:>3}%",
        "",
        f" RISK ASSESSMENT:                                     {audit.risk_level.value.upper()}",
        f" Confirmed failure rate (resolved only):                {audit.failures.confirmed_failure_rate}%",
        "",
        " This is a citation integrity audit.",
        " Papyrus does not determine authorship or AI involvement.",
        "═══════════════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)
