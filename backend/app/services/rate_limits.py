from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import get_settings
from app.services.cache import cache_service

logger = logging.getLogger(__name__)

# Daily budgets (telemetry / admin dashboard — not per-second caps).
BUDGETS = {
    "crossref": 5000,
    "semantic_scholar": 1000,
    "openalex": 10000,
    "exa": 500,
    "firecrawl": 200,
    "apify": 300,
    "europe_pmc": 5000,
    "unpaywall": 10000,
    "arxiv": 5000,
}


@dataclass(frozen=True)
class ThrottlePolicy:
    """Per-second spacing and max in-flight requests (polite-pool style)."""

    min_interval_s: float
    max_concurrent: int


# CrossRef polite pool (Dec 2025): ~10 single-record req/s, concurrency 3.
# arXiv: max one request every 3 seconds (export.arxiv.org usage terms).
THROTTLE: dict[str, ThrottlePolicy] = {
    "crossref": ThrottlePolicy(min_interval_s=0.12, max_concurrent=3),
    "semantic_scholar": ThrottlePolicy(min_interval_s=1.0, max_concurrent=2),
    "openalex": ThrottlePolicy(min_interval_s=0.05, max_concurrent=5),
    "europe_pmc": ThrottlePolicy(min_interval_s=0.05, max_concurrent=3),
    "unpaywall": ThrottlePolicy(min_interval_s=0.05, max_concurrent=5),
    "arxiv": ThrottlePolicy(min_interval_s=3.0, max_concurrent=1),
}


class RateLimitService:
    def __init__(self) -> None:
        self._fallback_counters: dict[str, dict[str, int]] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._last_request_at: dict[str, float] = {}

    def _day_key(self, source: str) -> str:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"ratelimit:{source}:{day}"

    def _lock(self, source: str) -> asyncio.Lock:
        if source not in self._locks:
            self._locks[source] = asyncio.Lock()
        return self._locks[source]

    def _semaphore(self, source: str) -> asyncio.Semaphore:
        if source not in self._semaphores:
            policy = THROTTLE.get(source, ThrottlePolicy(0.0, 10))
            self._semaphores[source] = asyncio.Semaphore(policy.max_concurrent)
        return self._semaphores[source]

    async def wait(self, source: str) -> None:
        """Space out HTTP calls to respect upstream per-second / concurrency limits."""
        if get_settings().papyrus_mode == "replay":
            return
        policy = THROTTLE.get(source)
        if not policy:
            return
        async with self._semaphore(source):
            async with self._lock(source):
                now = time.monotonic()
                last = self._last_request_at.get(source, 0.0)
                delay = policy.min_interval_s - (now - last)
                if delay > 0:
                    await asyncio.sleep(delay)
                self._last_request_at[source] = time.monotonic()

    async def record(self, source: str) -> None:
        if get_settings().papyrus_mode == "replay":
            return
        key = self._day_key(source)
        try:
            current = await cache_service.get_json("counter", key) or {"count": 0}
            current["count"] = int(current.get("count", 0)) + 1
            await cache_service.set_json("counter", key, current)
        except Exception as exc:
            logger.warning("Rate limit record: Redis unavailable (%s); using in-memory counter", exc)
            if key not in self._fallback_counters:
                self._fallback_counters[key] = {"count": 0}
            self._fallback_counters[key]["count"] += 1

    async def snapshot(self) -> dict[str, dict[str, int | float]]:
        results: dict[str, dict[str, int | float]] = {}
        for source, budget in BUDGETS.items():
            key = self._day_key(source)
            current = await cache_service.get_json("counter", key) or {"count": 0}
            count = int(current.get("count", 0))
            results[source] = {
                "used_today": count,
                "daily_budget": budget,
                "remaining": max(0, budget - count),
                "utilization_percent": round((count / budget) * 100, 1) if budget else 0.0,
            }
        return results

    async def meta(self) -> dict[str, str]:
        settings = get_settings()
        return {
            "redis_configured": str(bool(settings.redis_url)),
            "day_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

    async def allow(self, source: str) -> bool:
        budget = BUDGETS.get(source, 1000)
        key = self._day_key(source)
        try:
            current = await cache_service.get_json("counter", key) or {"count": 0}
            count = int(current.get("count", 0))
        except Exception as exc:
            logger.debug("Rate limit allow: Redis unavailable (%s); using in-memory counter", exc)
            count = self._fallback_counters.get(key, {"count": 0}).get("count", 0)
        return count < budget


rate_limit_service = RateLimitService()
