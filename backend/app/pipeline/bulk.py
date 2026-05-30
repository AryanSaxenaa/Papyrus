from __future__ import annotations

import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.domain.models import AuditRun, BulkAuditJob
from app.bulk_store import bulk_job_store
from app.pipeline.orchestrator import audit_orchestrator
from app.services.events import event_bus
from app.store import audit_store


async def process_bulk_zip(job_id: UUID, zip_path: Path) -> BulkAuditJob:
    job = bulk_job_store.get(job_id)
    if not job:
        raise ValueError("Bulk job not found")

    job.status = "running"
    bulk_job_store.save(job)
    event_bus.emit(job_id, "bulk", "Bulk job started", job_id=str(job_id))

    extract_dir = Path(tempfile.mkdtemp(prefix="papyrus-bulk-"))
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        pdf_files = sorted(extract_dir.rglob("*.pdf"))
        job.total = len(pdf_files)
        bulk_job_store.save(job)

        for pdf_file in pdf_files:
            audit = AuditRun(bulk_job_id=job_id, paper_title=pdf_file.stem)
            audit_store.create(audit)
            job.audit_ids.append(audit.id)
            bulk_job_store.save(job)

            try:
                await audit_orchestrator.run(audit.id, pdf_file)
                job.completed += 1
            except Exception as exc:  # noqa: BLE001
                job.failed += 1
                failed = audit_store.get(audit.id)
                if failed:
                    failed.status = "failed"
                    failed.error = str(exc)
                    audit_store.save(failed)
                event_bus.emit(job_id, "bulk", f"Paper failed: {pdf_file.name}", error=str(exc))

            bulk_job_store.save(job)
            event_bus.emit(
                job_id,
                "bulk",
                "Paper finished",
                completed=job.completed,
                failed=job.failed,
                total=job.total,
            )

        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        bulk_job_store.save(job)
        event_bus.emit(job_id, "bulk", "Bulk job complete", completed=job.completed, failed=job.failed)
        return job
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = str(exc)
        bulk_job_store.save(job)
        event_bus.emit(job_id, "error", f"Bulk job failed: {exc}")
        raise
    finally:
        zip_path.unlink(missing_ok=True)
