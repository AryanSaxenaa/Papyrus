from app.services.relational_audit import hydrate_audit_from_relational, load_audit_events


def test_load_audit_events_without_engine(monkeypatch):
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    from app.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    assert load_audit_events("00000000-0000-0000-0000-000000000000") == []


def test_hydrate_without_engine(monkeypatch):
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    monkeypatch.setenv("USE_RELATIONAL_READ", "false")
    from app.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    assert hydrate_audit_from_relational("00000000-0000-0000-0000-000000000000") is None
