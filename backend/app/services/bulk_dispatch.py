"""Bulk job queue: prefer Celery when Redis + worker are reachable; else BackgroundTasks."""

from __future__ import annotations

import logging
import time
from pathlib import Path
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


async def celery_worker_available() -> bool:
    """True when Celery is enabled, Redis pings, and at least one worker responds."""
    global _cached_available, _cached_at

    now = time.monotonic()
    if _cached_available is not None and (now - _cached_at) < _CACHE_TTL_SECONDS:
        return _cached_available

    settings = get_settings()
    if not settings.use_celery_bulk:
        _cached_available = False
        _cached_at = now
        return False

    if not await redis_reachable():
        logger.info("Bulk queue: Redis unreachable — using in-process BackgroundTasks")
        _cached_available = False
        _cached_at = now
        return False

    try:
        from app.worker import celery_app

        inspect = celery_app.control.inspect(timeout=1.0)
        stats = inspect.stats() if inspect else None
        available = bool(stats)
        if not available:
            logger.info("Bulk queue: no Celery workers — using in-process BackgroundTasks")
        _cached_available = available
        _cached_at = now
        return available
    except Exception as exc:
        logger.info("Bulk queue: Celery inspect failed (%s) — using BackgroundTasks", exc)
        _cached_available = False
        _cached_at = now
        return False


async def enqueue_bulk_zip(
    job_id: UUID,
    zip_path: Path,
    background: BackgroundTasks,
    background_runner,
) -> str:
    """
    Enqueue bulk ZIP processing. Returns ``celery`` or ``background``.
    ``background_runner`` is an async callable ``(job_id, zip_path) -> None``.
    """
    if await celery_worker_available():
        try:
            from app.worker import run_bulk_audit

            run_bulk_audit.delay(str(job_id), str(zip_path))
            return "celery"
        except Exception as exc:
            logger.warning("Celery enqueue failed (%s); falling back to BackgroundTasks", exc)

    background.add_task(background_runner, job_id, zip_path)
    return "background"
