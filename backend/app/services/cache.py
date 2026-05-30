import hashlib
import json
import logging

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)
from app.domain.json_types import JsonValue


class CacheService:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None
        self._healthy: bool = False
        self._last_ping_failure: float = 0.0
        self._ping_retry_interval: float = 30.0

    async def connect(self) -> None:
        settings = get_settings()
        if not settings.redis_url:
            logger.info("No Redis URL configured; cache disabled")
            return
        self._client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
        self._client = None
        self._healthy = False
        self._last_ping_failure = 0.0

    async def ping(self) -> bool:
        if not self._client:
            return False
        if self._healthy:
            return True
        import time
        if self._last_ping_failure and time.monotonic() - self._last_ping_failure < self._ping_retry_interval:
            return False
        try:
            await self._client.ping()
            self._healthy = True
            return True
        except (RedisError, OSError) as exc:
            self._last_ping_failure = time.monotonic()
            logger.debug("Redis ping failed: %s", exc)
            return False

    def _key(self, prefix: str, value: str) -> str:
        digest = hashlib.sha256(value.encode()).hexdigest()[:24]
        return f"{prefix}:{digest}"

    async def get_json(self, prefix: str, value: str) -> JsonValue | None:
        if not self._client or not await self.ping():
            return None
        try:
            raw = await self._client.get(self._key(prefix, value))
            return json.loads(raw) if raw else None
        except (RedisError, OSError) as exc:
            logger.debug("Cache get failed: %s", exc)
            return None

    async def set_json(self, prefix: str, value: str, payload: JsonValue) -> None:
        if not self._client or not await self.ping():
            return
        try:
            settings = get_settings()
            await self._client.setex(
                self._key(prefix, value),
                settings.cache_ttl_seconds,
                json.dumps(payload),
            )
        except (RedisError, OSError) as exc:
            logger.debug("Cache set failed: %s", exc)


cache_service = CacheService()
