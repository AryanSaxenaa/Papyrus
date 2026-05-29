import hashlib
import json
from typing import Any

import redis.asyncio as redis

from app.config import get_settings


class CacheService:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    def _key(self, prefix: str, value: str) -> str:
        digest = hashlib.sha256(value.encode()).hexdigest()[:24]
        return f"{prefix}:{digest}"

    async def get_json(self, prefix: str, value: str) -> Any | None:
        if not self._client:
            return None
        raw = await self._client.get(self._key(prefix, value))
        return json.loads(raw) if raw else None

    async def set_json(self, prefix: str, value: str, payload: Any) -> None:
        if not self._client:
            return
        settings = get_settings()
        await self._client.setex(
            self._key(prefix, value),
            settings.cache_ttl_seconds,
            json.dumps(payload),
        )


cache_service = CacheService()
