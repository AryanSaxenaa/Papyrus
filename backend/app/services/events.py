import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from app.domain.models import AuditStreamEvent

AuditEventPayload = dict[str, object]

logger = logging.getLogger(__name__)

_AUDIT_EVENTS_PREFIX = "papyrus:audit-events"


class EventHistoryLoadError(Exception):
    """Audit event history could not be loaded from the relational store."""


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[AuditEventPayload]]] = defaultdict(list)
        self._history: dict[str, list[AuditEventPayload]] = defaultdict(list)

    @staticmethod
    def redis_channel(audit_id: UUID | str) -> str:
        return f"{_AUDIT_EVENTS_PREFIX}:{audit_id}"

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
            logger.warning("Failed to persist audit event for %s: %s", key, exc)
        self._publish_redis(key, event)
        return event

    def _publish_redis(self, audit_id: str, event: AuditEventPayload) -> None:
        try:
            from app.services.cache import cache_service

            payload = json.dumps(event, default=str)
            cache_service.publish_sync(self.redis_channel(audit_id), payload)
            cache_service.append_audit_event_sync(audit_id, payload)
        except Exception as exc:
            logger.debug("audit event redis publish failed: %s", exc)

    def _load_redis_history(self, audit_id: str) -> list[AuditEventPayload]:
        try:
            from app.services.cache import cache_service

            raw_items = cache_service.load_audit_events_sync(audit_id)
            events: list[AuditEventPayload] = []
            for raw in raw_items:
                try:
                    events.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
            return events
        except Exception as exc:
            logger.debug("audit event redis history load failed: %s", exc)
            return []

    async def listen_redis(self, audit_id: UUID | str, queue: asyncio.Queue[AuditEventPayload]) -> None:
        """Forward events published by Celery workers to an API-side SSE queue."""
        from app.services.cache import cache_service

        key = str(audit_id)
        channel = self.redis_channel(audit_id)
        await cache_service.connect()
        if not cache_service._client:
            return
        pubsub = cache_service._client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if not isinstance(data, str):
                    continue
                event: AuditEventPayload = json.loads(data)
                self._history[key].append(event)
                await queue.put(event)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            raise

    def history(self, audit_id: UUID | str) -> list[AuditEventPayload]:
        """Merged in-process + DB history (worker events land in Postgres, not API memory)."""
        key = str(audit_id)
        mem = list(self._history.get(key, []))
        redis_events = self._load_redis_history(key)
        loaded: list[AuditEventPayload] = []
        try:
            from app.services.relational_audit import load_audit_events

            loaded = load_audit_events(key)
        except Exception as exc:
            logger.warning("Failed to load audit event history for %s: %s", key, exc)
            merged = _merge_event_history(mem, redis_events)
            if merged:
                self._history[key] = merged
                return merged
            raise EventHistoryLoadError(str(exc)) from exc
        merged = _merge_event_history(mem, redis_events, loaded)
        if merged:
            self._history[key] = merged
        return merged

    def replay_for_subscribe(self, audit_id: UUID | str) -> list[AuditEventPayload]:
        """Best-effort replay for SSE; does not fail the stream when DB history is unavailable."""
        try:
            return self.history(audit_id)
        except EventHistoryLoadError:
            key = str(audit_id)
            return list(self._history.get(key, []))

    async def subscribe(self, audit_id: UUID | str) -> asyncio.Queue[AuditEventPayload]:
        queue: asyncio.Queue[AuditEventPayload] = asyncio.Queue()
        key = str(audit_id)
        for past in self.replay_for_subscribe(audit_id):
            await queue.put(past)
        self._queues[key].append(queue)
        return queue

    def unsubscribe(self, audit_id: UUID | str, queue: asyncio.Queue[AuditEventPayload]) -> None:
        key = str(audit_id)
        if queue in self._queues[key]:
            self._queues[key].remove(queue)


def _event_identity(event: AuditEventPayload) -> tuple[object, ...]:
    return (event.get("ts"), event.get("type"), event.get("message"))


def _merge_event_history(*parts: list[AuditEventPayload]) -> list[AuditEventPayload]:
    seen: set[tuple[object, ...]] = set()
    merged: list[AuditEventPayload] = []
    for events in parts:
        for event in events:
            key = _event_identity(event)
            if key in seen:
                continue
            seen.add(key)
            merged.append(event)
    merged.sort(key=lambda item: str(item.get("ts") or ""))
    return merged


event_bus = EventBus()
