from __future__ import annotations

import pytest

from app.config import Settings


def test_json_persistence_has_no_db_engine(monkeypatch):
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    assert get_engine() is None
    settings = get_settings()
    assert settings.persistence_backend == "json"


@pytest.mark.asyncio
async def test_replay_mode_skips_rate_limits(monkeypatch):
    monkeypatch.setenv("PAPYRUS_MODE", "replay")
    from app.config import get_settings
    from app.services.rate_limits import rate_limit_service

    get_settings.cache_clear()
    await rate_limit_service.wait("arxiv")


def test_serpapi_inactive_without_key_in_live(monkeypatch):
    monkeypatch.setenv("PAPYRUS_MODE", "live")
    monkeypatch.setenv("SERPAPI_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = Settings(serpapi_enabled=True, serpapi_api_key=None, papyrus_mode="live")
    assert settings.serpapi_active() is False
