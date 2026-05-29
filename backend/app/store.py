from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from app.config import get_settings
from app.domain.models import AuditRun


class AuditStore:
    def __init__(self) -> None:
        self._audits: dict[UUID, AuditRun] = {}

    def _path(self, audit_id: UUID) -> Path:
        settings = get_settings()
        directory = Path(settings.audit_data_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{audit_id}.json"

    def create(self, audit: AuditRun) -> AuditRun:
        self._audits[audit.id] = audit
        return audit

    def get(self, audit_id: UUID) -> AuditRun | None:
        if audit_id in self._audits:
            return self._audits[audit_id]
        path = self._path(audit_id)
        if not path.exists():
            return None
        audit = AuditRun.model_validate_json(path.read_text(encoding="utf-8"))
        self._audits[audit_id] = audit
        return audit

    def save(self, audit: AuditRun) -> None:
        self._audits[audit.id] = audit
        self._path(audit.id).write_text(
            json.dumps(audit.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

    def list(self) -> list[AuditRun]:
        settings = get_settings()
        directory = Path(settings.audit_data_dir)
        if directory.exists():
            for path in directory.glob("*.json"):
                audit_id = UUID(path.stem)
                if audit_id not in self._audits:
                    self.get(audit_id)
        return sorted(self._audits.values(), key=lambda item: item.created_at, reverse=True)


audit_store = AuditStore()
