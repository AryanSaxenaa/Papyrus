from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.demo_guard import require_live_audit_access


def test_demo_guard_allows_replay(monkeypatch):
    monkeypatch.setenv("PAPYRUS_MODE", "replay")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "true")
    from app.config import get_settings

    get_settings.cache_clear()
    require_live_audit_access(x_access_code=None)


def test_demo_guard_blocks_without_code(monkeypatch):
    monkeypatch.setenv("PAPYRUS_MODE", "live")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "true")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "secret-code")
    from app.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(HTTPException) as exc:
        require_live_audit_access(x_access_code="wrong")
    assert exc.value.status_code == 403


def test_demo_guard_accepts_code(monkeypatch):
    monkeypatch.setenv("PAPYRUS_MODE", "live")
    monkeypatch.setenv("PUBLIC_DEMO_MODE", "true")
    monkeypatch.setenv("LIVE_ACCESS_CODE", "secret-code")
    from app.config import get_settings

    get_settings.cache_clear()
    require_live_audit_access(x_access_code="secret-code")
