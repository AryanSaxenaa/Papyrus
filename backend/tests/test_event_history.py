from app.services.events import EventBus, _merge_event_history


def test_merge_event_history_combines_api_and_worker_events() -> None:
    api_events = [
        {"ts": "2026-05-31T19:21:11+00:00", "type": "system", "message": "Audit dispatched"},
    ]
    worker_events = [
        {"ts": "2026-05-31T19:21:12+00:00", "type": "ingestion", "message": "Audit processing started"},
        {"ts": "2026-05-31T19:22:00+00:00", "type": "crossref", "message": "CrossRef DOI lookup"},
    ]
    merged = _merge_event_history(api_events, worker_events)
    assert len(merged) == 3
    assert merged[0]["type"] == "system"
    assert merged[-1]["type"] == "crossref"


def test_event_bus_history_merges_memory_with_database(monkeypatch) -> None:
    bus = EventBus()
    audit_id = "0606b5a0-0ca7-4d02-8ca7-be14520d3794"
    bus.emit(audit_id, "system", "Audit dispatched to Celery (audits queue)")

    def fake_load(aid: str) -> list[dict]:
        assert aid == audit_id
        return [
            {
                "ts": "2026-05-31T19:21:12+00:00",
                "type": "ingestion",
                "message": "Audit processing started",
            },
        ]

    monkeypatch.setattr(
        "app.services.relational_audit.load_audit_events",
        fake_load,
    )
    history = bus.history(audit_id)
    assert len(history) == 3
    types = {event["type"] for event in history}
    assert types == {"system", "ingestion", "crossref"}


def test_event_bus_history_includes_redis_log(monkeypatch) -> None:
    bus = EventBus()
    audit_id = "de279a3d-e277-4231-a75f-ff5bbecdf782"
    bus.emit(audit_id, "system", "Audit dispatched")

    monkeypatch.setattr(
        "app.services.relational_audit.load_audit_events",
        lambda _aid: [],
    )
    monkeypatch.setattr(
        "app.services.cache.cache_service.load_audit_events_sync",
        lambda _aid: [
            '{"ts":"2026-05-31T19:44:10+00:00","type":"ingestion","message":"Audit processing started"}',
            '{"ts":"2026-05-31T19:45:00+00:00","type":"crossref","message":"CrossRef DOI lookup"}',
        ],
    )
    history = bus.history(audit_id)
    assert len(history) == 3
    assert {e["type"] for e in history} == {"system", "ingestion", "crossref"}
