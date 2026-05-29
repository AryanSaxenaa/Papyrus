"""Celery worker entrypoint for bulk PDF jobs (v1 stub)."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("papyrus", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"app.worker.run_bulk_audit": {"queue": "audits"}}


@celery_app.task(name="app.worker.run_bulk_audit")
def run_bulk_audit(audit_id: str, pdf_path: str) -> str:
    # Bulk queue wiring lands in a follow-up PR; synchronous API path is live today.
    return audit_id
