from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.services.serpapi.ledger import serpapi_ledger
from app.services.serpapi.redaction import cache_key, sha256_bytes


class SerpApiCache:
    def __init__(self) -> None:
        settings = get_settings()
        self._root = Path(settings.audit_data_dir) / ".serpapi_cache"
        self._root.mkdir(parents=True, exist_ok=True)
        self._ttl = timedelta(hours=settings.serpapi_cache_ttl_hours)

    def _path(self, key: str) -> Path:
        return self._root / f"{key}.json"

    def get(self, engine: str, params: dict[str, Any]) -> dict[str, Any] | None:
        key = cache_key(engine, params)
        path = self._path(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        stored_at = datetime.fromisoformat(payload["stored_at"])
        if datetime.now(timezone.utc) - stored_at > self._ttl:
            return None
        return payload["body"]

    def set(self, engine: str, params: dict[str, Any], body: dict[str, Any]) -> str:
        key = cache_key(engine, params)
        path = self._path(key)
        path.write_text(
            json.dumps({"stored_at": datetime.now(timezone.utc).isoformat(), "body": body}),
            encoding="utf-8",
        )
        return key


class SerpApiBudget:
    def __init__(self) -> None:
        self._audit_spent: dict[str, int] = {}
        self._hourly: list[float] = []
        self._resume_at: float | None = None

    def preview(self, num_calls: int) -> dict[str, Any]:
        settings = get_settings()
        return {
            "estimated_credits": num_calls,
            "monthly_spent": serpapi_ledger.total_credits(),
            "monthly_cap": settings.serpapi_monthly_hard_cap,
            "per_audit_cap": settings.serpapi_max_credits_per_audit,
        }

    def allow(self, audit_id: str | None, engine: str) -> tuple[bool, str | None]:
        settings = get_settings()
        if not settings.serpapi_enabled:
            return False, "disabled"
        now = time.time()
        if self._resume_at and now < self._resume_at:
            return False, "hourly_rate_limited"
        if serpapi_ledger.total_credits() >= settings.serpapi_monthly_hard_cap:
            return False, "monthly_cap"
        if audit_id:
            spent = self._audit_spent.get(audit_id, 0)
            if spent >= settings.serpapi_max_credits_per_audit:
                return False, "audit_cap"
        self._prune_hourly(now)
        if len(self._hourly) >= settings.serpapi_max_per_hour:
            self._resume_at = now + 3600
            return False, "hourly_rate_limited"
        return True, None

    def record_spend(self, audit_id: str | None, credits: int) -> None:
        if audit_id:
            self._audit_spent[audit_id] = self._audit_spent.get(audit_id, 0) + credits
        if credits > 0:
            self._hourly.append(time.time())

    def _prune_hourly(self, now: float) -> None:
        cutoff = now - 3600
        self._hourly = [t for t in self._hourly if t >= cutoff]


serpapi_cache = SerpApiCache()
serpapi_budget = SerpApiBudget()
