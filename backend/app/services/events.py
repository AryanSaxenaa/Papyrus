import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


class EventBus:
    """In-memory SSE event bus keyed by audit id."""

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._history: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def emit(self, audit_id: UUID | str, event_type: str, message: str, **extra: Any) -> dict[str, Any]:
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "message": message,
            **extra,
        }
        key = str(audit_id)
        self._history[key].append(event)
        for queue in self._queues[key]:
            queue.put_nowait(event)
        return event

    def history(self, audit_id: UUID | str) -> list[dict[str, Any]]:
        return list(self._history[str(audit_id)])

    async def subscribe(self, audit_id: UUID | str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        key = str(audit_id)
        for past in self._history[key]:
            await queue.put(past)
        self._queues[key].append(queue)
        return queue

    def unsubscribe(self, audit_id: UUID | str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        key = str(audit_id)
        if queue in self._queues[key]:
            self._queues[key].remove(queue)


event_bus = EventBus()
