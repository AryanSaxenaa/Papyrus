from __future__ import annotations

import pytest

from app.services.transport import ReplayTransport, request_fingerprint


@pytest.mark.asyncio
async def test_replay_transport_unknown_request_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path))
    transport = ReplayTransport(tmp_path)
    with pytest.raises(FileNotFoundError, match="No replay cassette"):
        await transport.request("GET", "https://serpapi.com/search.json", params={"q": "test"})


def test_request_fingerprint_stable():
    a = request_fingerprint("GET", "https://example.com?api_key=secret", {"q": "x"})
    b = request_fingerprint("GET", "https://example.com?api_key=other", {"q": "x"})
    assert a == b
