from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from app.services.rate_limits import rate_limit_service

RetryableGet = Callable[[], Awaitable[httpx.Response]]


async def get_with_throttle(
    source: str,
    request: RetryableGet,
    *,
    retry_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504}),
    max_attempts: int = 4,
) -> httpx.Response:
    last: httpx.Response | None = None
    for attempt in range(max_attempts):
        await rate_limit_service.wait(source)
        last = await request()
        if last.status_code not in retry_statuses:
            return last
        if attempt < max_attempts - 1:
            await asyncio.sleep(min(2**attempt, 8))
    assert last is not None
    return last
