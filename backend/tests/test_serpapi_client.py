from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import asyncio

import pytest

from app.services.serpapi.client import SerpApiClient, SerpApiError
from app.services.transport import Transport, TransportResponse


class MockTransport:
    def __init__(self, responses: list[TransportResponse]) -> None:
        self._responses = responses
        self.calls = 0

    async def request(self, method, url, *, params=None, json_body=None, headers=None):
        self.calls += 1
        if not self._responses:
            raise RuntimeError("no responses")
        return self._responses.pop(0)


@pytest.fixture
def scholar_body():
    path = Path(__file__).parent / "fixtures" / "serpapi" / "google_scholar_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_serpapi_success(monkeypatch, scholar_body, tmp_path):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings

    get_settings.cache_clear()

    transport = MockTransport(
        [
            TransportResponse(
                status_code=200,
                content=json.dumps(scholar_body).encode("utf-8"),
                headers={},
            )
        ]
    )
    client = SerpApiClient(transport=transport)
    body, receipt = await client.search(
        "google_scholar",
        {"q": f"deep learning {uuid4()}"},
        audit_id="a1",
    )
    assert body["organic_results"]
    assert receipt.credits in (0, 1)
    assert "api_key" not in json.dumps(receipt.params)


@pytest.mark.asyncio
async def test_serpapi_budget_cap(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    monkeypatch.setenv("SERPAPI_MAX_CREDITS_PER_AUDIT", "0")
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings

    get_settings.cache_clear()
    client = SerpApiClient(transport=MockTransport([]))
    with pytest.raises(SerpApiError):
        await client.search("google_scholar", {"q": "x"}, audit_id="audit-1")
