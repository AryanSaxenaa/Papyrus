"""Enqueue audits and bulk jobs on Celery when a worker is available."""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks

from app.config import get_settings

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 30.0
_cached_available: bool | None = None
_cached_at: float = 0.0


def reset_celery_availability_cache() -> None:
    global _cached_available, _cached_at
    _cached_available = None
    _cached_at = 0.0


async def redis_reachable() -> bool:
    try:
        from app.services.cache import cache_service

        return await cache_service.ping()
    except (AttributeError, OSError, RuntimeError) as exc:
        logger.debug("Redis ping failed: %s", exc)
        return False


def worker_consumes_audit_queue(active_queues: dict | None, queue_name: str) -> bool:
    """True when at least one live worker is bound to the configured audit queue."""
    if not active_queues:
        return False
    for queues in active_queues.values():
        for queue in queues or []:
            if isinstance(queue, dict) and queue.get("name") == queue_name:
                return True
    return False


def worker_consumes_audits_queue(active_queues: dict | None) -> bool:
    """Backward-compatible alias for tests."""
    return worker_consumes_audit_queue(active_queues, get_settings().audit_queue_name())


async def celery_worker_available() -> bool:
    global _cached_available, _cached_at

    now = time.monotonic()
    if _cached_available is not None and (now - _cached_at) < _CACHE_TTL_SECONDS:
        return _cached_available

    settings = get_settings()
    if not settings.celery_background_enabled():
        _cached_available = False
        _cached_at = now
        return False

    if not await redis_reachable():
        logger.info("Background queue: Redis unreachable — using in-process BackgroundTasks")
        _cached_available = False
        _cached_at = now
        return False

    try:
        from app.worker import celery_app

        inspect = celery_app.control.inspect(timeout=5.0)
        stats = inspect.stats() if inspect else None
        active_queues = inspect.active_queues() if inspect else None
        queue_name = settings.audit_queue_name()
        available = bool(stats) and worker_consumes_audit_queue(active_queues, queue_name)
        if not available:
            logger.info(
                "Background queue: no worker on %s (stats=%s, active_queues=%s) — using BackgroundTasks",
                queue_name,
                bool(stats),
                active_queues,
            )
        _cached_available = available
        _cached_at = now
        return available
    except Exception as exc:
        logger.info("Background queue: Celery inspect failed (%s) — using BackgroundTasks", exc)
        _cached_available = False
        _cached_at = now
        return False


async def _enqueue_celery(task_name: str, *args: Any) -> bool:
    if not await celery_worker_available():
        return False
    try:
        from app.worker import celery_app

        queue_name = get_settings().audit_queue_name()
        celery_app.send_task(task_name, args=args, queue=queue_name)
        return True
    except Exception as exc:
        logger.warning("Celery enqueue failed (%s)", exc)
        return False


async def enqueue_pdf_audit(
    audit_id: UUID,
    storage_key: str,
    background: BackgroundTasks,
) -> str:
    from app.services.events import event_bus

    if await _enqueue_celery("app.worker.run_pdf_audit", str(audit_id), storage_key):
        event_bus.emit(
            audit_id,
            "system",
            f"Audit dispatched to Celery ({get_settings().audit_queue_name()} queue)",
        )
        return "celery"
    from app.services.audit_jobs import run_pdf_audit

    settings = get_settings()
    note = (
        " in-process (BackgroundTasks; slower — start a Celery worker on "
        f"{settings.audit_queue_name()} for production throughput)"
        if settings.app_env == "production"
        else " in-process (BackgroundTasks)"
    )
    event_bus.emit(audit_id, "system", f"Audit dispatched{note}")
    background.add_task(run_pdf_audit, audit_id, storage_key)
    return "background"


async def enqueue_doi_audit(
    audit_id: UUID,
    doi: str,
    background: BackgroundTasks,
) -> str:
    if await _enqueue_celery("app.worker.run_doi_audit", str(audit_id), doi):
        return "celery"
    from app.services.audit_jobs import run_doi_audit

    background.add_task(run_doi_audit, audit_id, doi)
    return "background"


async def enqueue_url_audit(
    audit_id: UUID,
    url: str,
    storage_key: str,
    background: BackgroundTasks,
) -> str:
    if await _enqueue_celery("app.worker.run_url_audit", str(audit_id), url, storage_key):
        return "celery"
    from app.services.audit_jobs import run_url_audit

    background.add_task(run_url_audit, audit_id, url, storage_key)
    return "background"


async def enqueue_bulk_zip(
    job_id: UUID,
    storage_key: str,
    background: BackgroundTasks,
) -> str:
    if await _enqueue_celery("app.worker.run_bulk_audit", str(job_id), storage_key):
        return "celery"
    from app.services.audit_jobs import run_bulk_job

    background.add_task(run_bulk_job, job_id, storage_key)
    return "background"
