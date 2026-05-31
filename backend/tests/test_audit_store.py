from uuid import UUID

import pytest

from app.config import get_settings
from app.domain.models import AuditRun
from app.store import AuditStore


@pytest.fixture
def json_audit_store(tmp_path, monkeypatch):
    monkeypatch.setenv("PERSISTENCE_BACKEND", "json")
    monkeypatch.setenv("FILE_STORAGE_BACKEND", "local")
    monkeypatch.setenv("FILE_STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    yield AuditStore()
    get_settings.cache_clear()


def test_create_persists_so_workers_can_reload(json_audit_store: AuditStore) -> None:
    audit = AuditRun()
    json_audit_store.create(audit)

    reloaded = AuditStore().get(audit.id)
    assert reloaded is not None
    assert reloaded.id == audit.id
    assert reloaded.status == "queued"
