from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx

from app.config import get_settings
from app.services.serpapi.redaction import redact_url, sha256_bytes


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    content: bytes
    headers: dict[str, str]


class Transport(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TransportResponse: ...


class LiveTransport:
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TransportResponse:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(method, url, params=params, json=json_body, headers=headers)
            return TransportResponse(
                status_code=response.status_code,
                content=response.content,
                headers=dict(response.headers),
            )


def request_fingerprint(method: str, url: str, params: dict[str, Any] | None = None) -> str:
    from app.services.serpapi.redaction import cache_key

    return cache_key(method.upper(), {"url": redact_url(url), "params": params or {}})


class RecordTransport:
    def __init__(self, inner: Transport, record_dir: Path) -> None:
        self._inner = inner
        self._record_dir = record_dir
        self._record_dir.mkdir(parents=True, exist_ok=True)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TransportResponse:
        response = await self._inner.request(
            method, url, params=params, json_body=json_body, headers=headers
        )
        fp = request_fingerprint(method, url, params)
        path = self._record_dir / f"{fp}.json"
        path.write_bytes(
            json.dumps(
                {
                    "method": method,
                    "url": redact_url(url),
                    "params": params or {},
                    "status_code": response.status_code,
                    "content_b64": response.content.hex(),
                }
            ).encode("utf-8")
        )
        return response


class ReplayTransport:
    def __init__(self, fixture_dir: Path) -> None:
        self._fixture_dir = fixture_dir

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> TransportResponse:
        fp = request_fingerprint(method, url, params)
        path = self._fixture_dir / f"{fp}.json"
        if not path.exists():
            raise FileNotFoundError(f"No replay cassette for fingerprint {fp}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        content = bytes.fromhex(payload["content_b64"])
        return TransportResponse(
            status_code=int(payload["status_code"]),
            content=content,
            headers={},
        )


def get_default_transport() -> Transport:
    settings = get_settings()
    if settings.papyrus_mode == "replay":
        fixture_root = Path(settings.audit_data_dir) / "fixtures" / settings.replay_set
        return ReplayTransport(fixture_root)
    if settings.papyrus_mode == "record":
        raw_dir = Path(settings.audit_data_dir) / "fixtures" / "_raw" / settings.replay_set
        return RecordTransport(LiveTransport(), raw_dir)
    return LiveTransport()
