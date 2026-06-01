"""Celery worker for audits and bulk ZIP jobs."""

from __future__ import annotations

import asyncio
import ssl
from uuid import UUID

from celery import Celery

from app.config import get_settings

settings = get_settings()
_audit_queue = settings.audit_queue_name()

celery_app = Celery("papyrus", broker=settings.redis_url, backend=settings.redis_url)

_celery_conf: dict = {
    "task_default_queue": _audit_queue,
    "task_routes": {
        "app.worker.run_pdf_audit": {"queue": _audit_queue},
        "app.worker.run_doi_audit": {"queue": _audit_queue},
        "app.worker.run_url_audit": {"queue": _audit_queue},
        "app.worker.run_bulk_audit": {"queue": _audit_queue},
    },
    "task_track_started": True,
    "worker_prefetch_multiplier": 1,
    "task_acks_late": True,
    "broker_connection_retry_on_startup": True,
}

if settings.redis_url.startswith("rediss://"):
    _ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    _celery_conf["broker_use_ssl"] = _ssl
    _celery_conf["redis_backend_use_ssl"] = _ssl

celery_app.conf.update(**_celery_conf)


def _register_worker_signals() -> None:
    from celery.signals import worker_ready, worker_shutdown

    from app.services.celery_heartbeat import start_heartbeat_thread, stop_previous_heartbeat

    @worker_ready.connect
    def _on_worker_ready(sender=None, **kwargs) -> None:  # noqa: ARG001
        queue = get_settings().audit_queue_name()
        start_heartbeat_thread(queue)

    @worker_shutdown.connect
    def _on_worker_shutdown(sender=None, **kwargs) -> None:  # noqa: ARG001
        stop_previous_heartbeat()


_register_worker_signals()


@celery_app.task(name="app.worker.run_pdf_audit")
def run_pdf_audit(audit_id: str, storage_key: str) -> str:
    from app.services.audit_jobs import run_pdf_audit as _run

    asyncio.run(_run(UUID(audit_id), storage_key))
    return audit_id


@celery_app.task(name="app.worker.run_doi_audit")
def run_doi_audit(audit_id: str, doi: str) -> str:
    from app.services.audit_jobs import run_doi_audit as _run

    asyncio.run(_run(UUID(audit_id), doi))
    return audit_id


@celery_app.task(name="app.worker.run_url_audit")
def run_url_audit(audit_id: str, url: str, storage_key: str) -> str:
    from app.services.audit_jobs import run_url_audit as _run

    asyncio.run(_run(UUID(audit_id), url, storage_key))
    return audit_id


@celery_app.task(name="app.worker.run_bulk_audit")
def run_bulk_audit(job_id: str, storage_key: str) -> str:
    from app.services.audit_jobs import run_bulk_job

    asyncio.run(run_bulk_job(UUID(job_id), storage_key))
    return job_id
