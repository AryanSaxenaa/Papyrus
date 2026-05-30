"""Celery worker for bulk PDF jobs (optional — API BackgroundTasks also supported)."""

import asyncio
from pathlib import Path
from uuid import UUID

from celery import Celery

from app.config import get_settings
from app.pipeline.bulk import process_bulk_zip

settings = get_settings()

celery_app = Celery("papyrus", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"app.worker.run_bulk_audit": {"queue": "audits"}}


@celery_app.task(name="app.worker.run_bulk_audit")
def run_bulk_audit(job_id: str, zip_path: str) -> str:
    asyncio.run(process_bulk_zip(UUID(job_id), Path(zip_path)))
    return job_id
