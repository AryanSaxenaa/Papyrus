from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import AuditRecord
from app.db.session import get_engine
from app.domain.models import AuditRun


class AuditStore:
    def __init__(self) -> None:
        self._audits: dict[UUID, AuditRun] = {}

    def _path(self, audit_id: UUID) -> Path:
        settings = get_settings()
        directory = Path(settings.audit_data_dir)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{audit_id}.json"

    def _use_postgres(self) -> bool:
        return get_settings().persistence_backend in {"postgres", "both"}

    def _use_json(self) -> bool:
        return get_settings().persistence_backend in {"json", "both"}

    def create(self, audit: AuditRun) -> AuditRun:
        self._audits[audit.id] = audit
        return audit

    def get(self, audit_id: UUID) -> AuditRun | None:
        if audit_id in self._audits:
            return self._audits[audit_id]

        if self._use_postgres():
            audit = self._get_postgres(audit_id)
            if audit:
                self._audits[audit_id] = audit
                return audit

        if self._use_json():
            path = self._path(audit_id)
            if path.exists():
                audit = AuditRun.model_validate_json(path.read_text(encoding="utf-8"))
                self._audits[audit_id] = audit
                return audit
        return None

    def save(self, audit: AuditRun) -> None:
        self._audits[audit.id] = audit
        payload = json.dumps(audit.model_dump(mode="json"), indent=2)
        if self._use_json():
            self._path(audit.id).write_text(payload, encoding="utf-8")
        if self._use_postgres():
            self._save_postgres(audit, payload)

    def list(self) -> list[AuditRun]:
        if self._use_postgres():
            engine = get_engine()
            if engine is not None:
                with Session(engine) as session:
                    rows = session.scalars(select(AuditRecord)).all()
                    for row in rows:
                        audit_id = UUID(row.id)
                        if audit_id not in self._audits:
                            self._audits[audit_id] = AuditRun.model_validate_json(row.payload)

        if self._use_json():
            directory = Path(get_settings().audit_data_dir)
            if directory.exists():
                for path in directory.glob("*.json"):
                    audit_id = UUID(path.stem)
                    if audit_id not in self._audits:
                        self.get(audit_id)

        return sorted(self._audits.values(), key=lambda item: item.created_at, reverse=True)

    def _get_postgres(self, audit_id: UUID) -> AuditRun | None:
        engine = get_engine()
        if engine is None:
            return None
        with Session(engine) as session:
            row = session.get(AuditRecord, str(audit_id))
            if not row:
                return None
            return AuditRun.model_validate_json(row.payload)

    def _save_postgres(self, audit: AuditRun, payload: str) -> None:
        engine = get_engine()
        if engine is None:
            return
        with Session(engine) as session:
            row = session.get(AuditRecord, str(audit.id))
            if row is None:
                row = AuditRecord(id=str(audit.id), payload=payload)
                session.add(row)
            else:
                row.payload = payload
            session.commit()


audit_store = AuditStore()
