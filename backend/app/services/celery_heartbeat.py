"""Redis heartbeat so the API can detect Cloud Run Celery workers without control.inspect()."""

from __future__ import annotations

import logging
import ssl
import threading
import time

from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)

HEARTBEAT_PREFIX = "papyrus:celery:heartbeat"
HEARTBEAT_TTL_SECONDS = 90
HEARTBEAT_INTERVAL_SECONDS = 30


def heartbeat_key(queue_name: str) -> str:
    return f"{HEARTBEAT_PREFIX}:{queue_name}"


def _sync_redis_client():
    import redis as sync_redis

    settings = get_settings()
    if not settings.redis_url:
        return None
    kwargs: dict = {"decode_responses": True}
    if settings.redis_url.startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
    return sync_redis.from_url(settings.redis_url, **kwargs)


def write_heartbeat_sync(queue_name: str) -> None:
    client = _sync_redis_client()
    if client is None:
        return
    try:
        client.setex(heartbeat_key(queue_name), HEARTBEAT_TTL_SECONDS, "1")
    except (RedisError, OSError) as exc:
        logger.debug("Celery heartbeat write failed: %s", exc)
    finally:
        client.close()


def heartbeat_present_sync(queue_name: str) -> bool:
    client = _sync_redis_client()
    if client is None:
        return False
    try:
        return bool(client.exists(heartbeat_key(queue_name)))
    except (RedisError, OSError) as exc:
        logger.debug("Celery heartbeat read failed: %s", exc)
        return False
    finally:
        client.close()


async def heartbeat_present(queue_name: str) -> bool:
    from app.services.cache import cache_service

    if not cache_service._client:
        return heartbeat_present_sync(queue_name)
    if not await cache_service.ping():
        return False
    try:
        return bool(await cache_service._client.exists(heartbeat_key(queue_name)))
    except (RedisError, OSError) as exc:
        logger.debug("Celery heartbeat async read failed: %s", exc)
        return heartbeat_present_sync(queue_name)


_stop_event: threading.Event | None = None
_heartbeat_thread: threading.Thread | None = None


def _heartbeat_loop(queue_name: str, stop: threading.Event) -> None:
    while not stop.is_set():
        write_heartbeat_sync(queue_name)
        stop.wait(HEARTBEAT_INTERVAL_SECONDS)


def start_heartbeat_thread(queue_name: str) -> None:
    global _stop_event, _heartbeat_thread
    stop_previous_heartbeat()
    _stop_event = threading.Event()
    _heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(queue_name, _stop_event),
        name="celery-heartbeat",
        daemon=True,
    )
    _heartbeat_thread.start()
    write_heartbeat_sync(queue_name)


def stop_previous_heartbeat() -> None:
    global _stop_event, _heartbeat_thread
    if _stop_event is not None:
        _stop_event.set()
    if _heartbeat_thread is not None:
        _heartbeat_thread.join(timeout=2.0)
    _stop_event = None
    _heartbeat_thread = None
