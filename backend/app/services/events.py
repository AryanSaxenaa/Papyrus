import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from app.domain.models import AuditStreamEvent

AuditEventPayload = dict[str, object]


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[AuditEventPayload]]] = defaultdict(list)
        self._history: dict[str, list[AuditEventPayload]] = defaultdict(list)

    def emit(
        self,
        audit_id: UUID | str,
        event_type: str,
        message: str,
        **extra: object,
    ) -> AuditEventPayload:
        event = AuditStreamEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            type=event_type,
            message=message,
            **extra,
        ).model_dump(mode="json", exclude_none=True)
        key = str(audit_id)
        self._history[key].append(event)
        for queue in self._queues[key]:
            queue.put_nowait(event)
        try:
            from app.services.relational_audit import persist_audit_event

            persist_audit_event(key, event)
        except Exception as exc:
            # Log database persistence errors but don't fail event emission
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist audit event: {exc}")
        return event

    def history(self, audit_id: UUID | str) -> list[AuditEventPayload]:
        key = str(audit_id)
        mem = self._history[key]
        if mem:
            return list(mem)
        try:
            from app.services.relational_audit import load_audit_events

            loaded = load_audit_events(key)
            if loaded:
                self._history[key] = list(loaded)
                return list(loaded)
        except Exception as exc:
            # Log database loading errors but don't fail event history retrieval
            import logging
            logging.getLogger(__name__).warning(f"Failed to load audit event history: {exc}")
        return []

    async def subscribe(self, audit_id: UUID | str) -> asyncio.Queue[AuditEventPayload]:
        queue: asyncio.Queue[AuditEventPayload] = asyncio.Queue()
        key = str(audit_id)
        for past in self.history(audit_id):
            await queue.put(past)
        self._queues[key].append(queue)
        return queue

    def unsubscribe(self, audit_id: UUID | str, queue: asyncio.Queue[AuditEventPayload]) -> None:
        key = str(audit_id)
        if queue in self._queues[key]:
            self._queues[key].remove(queue)


event_bus = EventBus()
