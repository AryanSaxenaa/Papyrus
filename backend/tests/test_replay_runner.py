from __future__ import annotations

import pytest

from app.services.events import event_bus
from app.services.replay.runner import replay_audit_events


@pytest.mark.asyncio
async def test_replay_emits_events_quickly(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    monkeypatch.setenv("REPLAY_SPEEDUP", "100000")
    monkeypatch.setenv("PAPYRUS_MODE", "replay")
    fixture = tmp_path / "data" / "fixtures" / "demo-a"
    fixture.mkdir(parents=True)
    (fixture / "events.jsonl").write_text(
        '{"t_rel_ms": 0, "type": "system", "message": "start"}\n'
        '{"t_rel_ms": 2000, "type": "serpapi.call", "message": "done"}\n',
        encoding="utf-8",
    )
    from app.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()

    async def _no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("app.services.replay.runner.asyncio.sleep", _no_sleep)

    audit_id = "replay-test-audit-unique"
    await replay_audit_events(audit_id, "demo-a")
    history = event_bus.history(audit_id)
    assert len(history) >= 2
    assert any(e.get("replayed") for e in history)
