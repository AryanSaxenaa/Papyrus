from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config import get_settings
from app.domain.models import SerpApiReceipt
from app.services.serpapi.budget import serpapi_budget, serpapi_cache
from app.services.serpapi.ledger import serpapi_ledger
from app.services.serpapi.redaction import build_serpapi_url, redact_params, sha256_bytes
from app.services.transport import Transport, get_default_transport


class SerpApiError(Exception):
    def __init__(self, message: str, *, http_status: int = 500, retryable: bool = False) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.retryable = retryable


class SerpApiClient:
    def __init__(self, transport: Transport | None = None) -> None:
        self._transport = transport or get_default_transport()
        self._settings = get_settings()

    async def search(
        self,
        engine: str,
        params: dict[str, Any],
        *,
        audit_id: str | None = None,
        citation_id: str | None = None,
    ) -> tuple[dict[str, Any], SerpApiReceipt]:
        allowed, reason = serpapi_budget.allow(audit_id, engine)
        if not allowed:
            raise SerpApiError(f"SerpApi budget refused call: {reason}", http_status=429)

        settings = self._settings
        if settings.papyrus_mode != "replay" and not settings.serpapi_api_key:
            raise SerpApiError("SerpApi API key not configured", http_status=401)

        api_key = settings.serpapi_api_key or "replay"

        query_params = dict(params)
        if self._settings.serpapi_no_cache:
            query_params["no_cache"] = "true"

        cached = serpapi_cache.get(engine, query_params)
        if cached is not None:
            receipt = self._build_receipt(
                engine=engine,
                params=query_params,
                body=cached,
                http_status=200,
                credits=0,
                cache_hit=True,
                latency_ms=0,
                raw_key=f"cache:{engine}",
            )
            serpapi_ledger.append(
                audit_id=audit_id,
                citation_id=citation_id,
                engine=engine,
                params=query_params,
                search_metadata_id=(cached.get("search_metadata") or {}).get("id"),
                json_endpoint=(cached.get("search_metadata") or {}).get("json_endpoint"),
                http_status=200,
                credits=0,
                cache_hit=True,
                latency_ms=0,
                raw_key=receipt.raw_ref,
                sha256_raw=receipt.sha256_raw,
            )
            return cached, receipt

        url = build_serpapi_url(engine, query_params, api_key or "replay")
        started = time.perf_counter()
        last_error: SerpApiError | None = None
        for attempt in range(2):
            response = await self._transport.request("GET", url)
            latency_ms = int((time.perf_counter() - started) * 1000)
            if response.status_code == 401:
                raise SerpApiError("Unauthorized SerpApi key", http_status=401)
            if response.status_code == 429:
                message = response.content.decode("utf-8", errors="ignore").lower()
                if "hour" in message or "rate" in message:
                    serpapi_budget._resume_at = time.time() + 3600  # noqa: SLF001
                raise SerpApiError("SerpApi rate limited", http_status=429)
            if response.status_code >= 500 and attempt == 0:
                last_error = SerpApiError("SerpApi server error", http_status=response.status_code, retryable=True)
                continue
            if response.status_code >= 400:
                raise SerpApiError(
                    f"SerpApi error {response.status_code}",
                    http_status=response.status_code,
                )
            body = json.loads(response.content.decode("utf-8"))
            credits = 1
            raw_key = serpapi_cache.set(engine, query_params, body)
            serpapi_budget.record_spend(audit_id, credits)
            receipt = self._build_receipt(
                engine=engine,
                params=query_params,
                body=body,
                http_status=response.status_code,
                credits=credits,
                cache_hit=False,
                latency_ms=latency_ms,
                raw_key=raw_key,
            )
            serpapi_ledger.append(
                audit_id=audit_id,
                citation_id=citation_id,
                engine=engine,
                params=query_params,
                search_metadata_id=(body.get("search_metadata") or {}).get("id"),
                json_endpoint=(body.get("search_metadata") or {}).get("json_endpoint"),
                http_status=response.status_code,
                credits=credits,
                cache_hit=False,
                latency_ms=latency_ms,
                raw_key=receipt.raw_ref,
                sha256_raw=receipt.sha256_raw,
            )
            return body, receipt
        if last_error:
            raise last_error
        raise SerpApiError("SerpApi request failed")

    def _build_receipt(
        self,
        *,
        engine: str,
        params: dict[str, Any],
        body: dict[str, Any],
        http_status: int,
        credits: int,
        cache_hit: bool,
        latency_ms: int,
        raw_key: str,
    ) -> SerpApiReceipt:
        meta = body.get("search_metadata") or {}
        created_raw = meta.get("created_at")
        created_at = datetime.now(timezone.utc)
        if isinstance(created_raw, str):
            try:
                created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                pass
        raw_bytes = json.dumps(body).encode("utf-8")
        return SerpApiReceipt(
            call_id=str(uuid4()),
            engine=engine,  # type: ignore[arg-type]
            params=redact_params(params),
            search_metadata_id=meta.get("id"),
            json_endpoint=meta.get("json_endpoint"),
            http_status=http_status,
            credits=credits,
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            created_at=created_at,
            raw_ref=raw_key,
            sha256_raw=sha256_bytes(raw_bytes),
        )


serpapi_client = SerpApiClient()
