from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings
from app.services.cache import cache_service

BUDGETS = {
    "crossref": 5000,
    "semantic_scholar": 1000,
    "openalex": 10000,
    "exa": 500,
    "firecrawl": 200,
    "apify": 300,
    "europe_pmc": 5000,
    "unpaywall": 10000,
}


class RateLimitService:
    def _day_key(self, source: str) -> str:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"ratelimit:{source}:{day}"

    async def record(self, source: str) -> None:
        key = self._day_key(source)
        current = await cache_service.get_json("counter", key) or {"count": 0}
        current["count"] = int(current.get("count", 0)) + 1
        await cache_service.set_json("counter", key, current)

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
        current = await cache_service.get_json("counter", key) or {"count": 0}
        return int(current.get("count", 0)) < budget


rate_limit_service = RateLimitService()
