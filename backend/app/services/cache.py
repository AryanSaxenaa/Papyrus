import hashlib
import json

import redis.asyncio as redis

from app.config import get_settings
from app.domain.json_types import JsonValue


class CacheService:
    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        settings = get_settings()
        self._client = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    def _key(self, prefix: str, value: str) -> str:
        digest = hashlib.sha256(value.encode()).hexdigest()[:24]
        return f"{prefix}:{digest}"

    async def get_json(self, prefix: str, value: str) -> JsonValue | None:
        if not self._client:
            return None
        raw = await self._client.get(self._key(prefix, value))
        return json.loads(raw) if raw else None

    async def set_json(self, prefix: str, value: str, payload: JsonValue) -> None:
        if not self._client:
            return
        settings = get_settings()
        await self._client.setex(
            self._key(prefix, value),
            settings.cache_ttl_seconds,
            json.dumps(payload),
        )


cache_service = CacheService()
