"""Background audit runners (Celery tasks and FastAPI BackgroundTasks)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import UUID

from app.bulk_store import bulk_job_store
from app.services.events import event_bus
from app.storage.files import file_store
from app.store import audit_store


def _claim_audit(audit_id: UUID) -> bool:
    """Mark audit running; return False if another worker already claimed it."""
    audit = audit_store.get(audit_id)
    if audit is None:
        raise ValueError(f"Audit {audit_id} not found")
    if audit.status in {"running", "complete"}:
        return False
    audit.status = "running"
    audit_store.save(audit)
    event_bus.emit(audit_id, "ingestion", "Audit processing started")
    return True


def _storage_not_found_message(storage_key: str, exc: FileNotFoundError) -> str:
    from app.config import get_settings

    settings = get_settings()
    base = f"Uploaded PDF not found for storage key {storage_key!r} ({exc})."
    if settings.file_storage_backend != "gcs":
        return base
    return (
        f"{base} The file may be missing from object storage, or a Celery worker in another "
        f"environment (for example local dev on queue 'audits-development') consumed this task "
        f"while production uses queue {settings.audit_queue_name()!r}."
    )


async def run_pdf_audit(audit_id: UUID, storage_key: str) -> None:
    from app.pipeline.orchestrator import audit_orchestrator

    try:
        if not _claim_audit(audit_id):
            return
        with file_store.local_path(storage_key) as pdf_path:
            await audit_orchestrator.run(audit_id, pdf_path)
    except FileNotFoundError as exc:
        _fail_audit(audit_id, RuntimeError(_storage_not_found_message(storage_key, exc)))
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)


async def run_doi_audit(audit_id: UUID, doi: str) -> None:
    from app.pipeline.orchestrator import audit_orchestrator

    try:
        if not _claim_audit(audit_id):
            return
        await audit_orchestrator.run_doi(audit_id, doi)
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)


async def run_url_audit(audit_id: UUID, url: str, storage_key: str) -> None:
    from app.pipeline.orchestrator import audit_orchestrator
    from app.services.url_fetch import url_fetch_service

    temp_path: Path | None = None
    try:
        if not _claim_audit(audit_id):
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as handle:
            temp_path = Path(handle.name)
        await url_fetch_service.download_pdf(url, temp_path)
        file_store.write_bytes(storage_key, temp_path.read_bytes())
        with file_store.local_path(storage_key) as pdf_path:
            await audit_orchestrator.run_from_url(audit_id, url, pdf_path)
    except Exception as exc:  # noqa: BLE001
        _fail_audit(audit_id, exc)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


async def run_bulk_job(job_id: UUID, storage_key: str) -> None:
    from app.pipeline.bulk import process_bulk_zip

    try:
        with file_store.local_path(storage_key) as zip_path:
            await process_bulk_zip(job_id, zip_path)
    except Exception as exc:  # noqa: BLE001
        job = bulk_job_store.get(job_id)
        if job and job.status not in {"complete", "failed"}:
            job.status = "failed"
            job.error = str(exc)
            bulk_job_store.save(job)
        event_bus.emit(job_id, "error", f"Bulk job failed: {exc}")


def _fail_audit(audit_id: UUID, exc: Exception) -> None:
    audit = audit_store.get(audit_id)
    if audit is None:
        from app.domain.models import AuditRun

        audit = AuditRun(id=audit_id)
        audit_store.create(audit)
    audit.status = "failed"
    audit.error = str(exc)
    audit_store.save(audit)
    event_bus.emit(audit_id, "error", f"Audit failed: {exc}")
