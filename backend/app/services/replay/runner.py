from __future__ import annotations

import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.services.events import event_bus


def replay_fixture_dir(replay_set: str | None = None) -> Path:
    settings = get_settings()
    name = replay_set or settings.replay_set
    return Path(settings.audit_data_dir) / "fixtures" / name


def load_events_manifest(replay_set: str | None = None) -> list[dict]:
    path = replay_fixture_dir(replay_set) / "events.jsonl"
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


async def replay_audit_events(audit_id: UUID | str, replay_set: str | None = None) -> None:
    """Re-emit recorded events with compressed timing (replay mode only)."""
    settings = get_settings()
    events = load_events_manifest(replay_set)
    if not events:
        return
    speedup = max(1, settings.replay_speedup)
    audit_key = str(audit_id)
    start_ms = float(events[0].get("t_rel_ms", 0))
    for event in events:
        rel_ms = float(event.get("t_rel_ms", 0))
        delay_s = max(0.0, (rel_ms - start_ms) / 1000.0 / speedup)
        if delay_s > 0:
            await asyncio.sleep(delay_s)
        payload = {k: v for k, v in event.items() if k not in {"t_rel_ms"}}
        payload["replayed"] = True
        event_bus.emit(
            audit_key,
            payload.get("type", "system"),
            payload.get("message", ""),
            **{k: v for k, v in payload.items() if k not in {"type", "message", "ts"}},
        )
