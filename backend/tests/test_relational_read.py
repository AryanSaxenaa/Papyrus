from app.services.relational_audit import hydrate_audit_from_relational, load_audit_events


def test_load_audit_events_without_engine():
    assert load_audit_events("00000000-0000-0000-0000-000000000000") == []


def test_hydrate_without_engine():
    assert hydrate_audit_from_relational("00000000-0000-0000-0000-000000000000") is None
