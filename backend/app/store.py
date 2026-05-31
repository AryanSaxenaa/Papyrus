from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import AuditRecord, AuditSummaryRecord, CitationIndexRecord
from app.storage.files import audit_json_key, file_store, upload_key
from app.persistence.postgres_sync import sync_postgres_audit_indexes
from app.services.relational_audit import delete_relational_audit
from app.db.session import get_engine
from app.domain.models import AuditRun, AuditSummary


class AuditStore:
    def __init__(self) -> None:
        self._audits: dict[UUID, AuditRun] = {}

    def _json_key(self, audit_id: UUID) -> str:
        return audit_json_key(str(audit_id))

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
            key = self._json_key(audit_id)
            if file_store.exists(key):
                audit = AuditRun.model_validate_json(
                    file_store.read_bytes(key).decode("utf-8")
                )
                self._audits[audit_id] = audit
                return audit
        return None

    def save(self, audit: AuditRun) -> None:
        self._audits[audit.id] = audit
        payload = json.dumps(audit.model_dump(mode="json"), indent=2)
        if self._use_json():
            file_store.write_bytes(self._json_key(audit.id), payload.encode("utf-8"))
        if self._use_postgres():
            self._save_postgres(audit, payload)

    def list_summaries(self) -> list[AuditSummary]:
        engine = get_engine()
        if engine is None:
            return [
                AuditSummary(
                    id=str(a.id),
                    paper_title=a.paper_title,
                    status=a.status,
                    coverage_percent=a.coverage.coverage_percent,
                    failure_rate=a.failures.confirmed_failure_rate,
                    risk_level=a.risk_level.value,
                    citation_count=len(a.citations),
                    created_at=a.created_at.isoformat(),
                )
                for a in self.list()
            ]
        with Session(engine) as session:
            rows = session.scalars(
                select(AuditSummaryRecord).order_by(AuditSummaryRecord.created_at.desc())
            ).all()
            return [
                AuditSummary(
                    id=row.id,
                    paper_title=row.paper_title,
                    status=row.status,
                    coverage_percent=row.coverage_percent,
                    failure_rate=row.failure_rate,
                    risk_level=row.risk_level,
                    citation_count=row.citation_count,
                    created_at=row.created_at.isoformat() if row.created_at else None,
                )
                for row in rows
            ]

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

        if self._use_json() and get_settings().file_storage_backend == "local":
            directory = Path(get_settings().file_storage_root) / "audits"
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
            if row:
                return AuditRun.model_validate_json(row.payload)
        settings = get_settings()
        if settings.use_relational_read:
            from app.services.relational_audit import hydrate_audit_from_relational

            return hydrate_audit_from_relational(str(audit_id))
        return None

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
        self._save_summary(audit)
        sync_postgres_audit_indexes(audit)

    def delete(self, audit_id: UUID) -> bool:
        removed = False
        if audit_id in self._audits:
            del self._audits[audit_id]
            removed = True
        json_key = self._json_key(audit_id)
        if file_store.exists(json_key):
            file_store.delete(json_key)
            removed = True
        pdf_key = upload_key(str(audit_id))
        if file_store.exists(pdf_key):
            file_store.delete(pdf_key)
            removed = True
        engine = get_engine()
        if engine is not None:
            with Session(engine) as session:
                row = session.get(AuditRecord, str(audit_id))
                if row:
                    session.delete(row)
                    removed = True
                summary = session.get(AuditSummaryRecord, str(audit_id))
                if summary:
                    session.delete(summary)
                session.execute(
                    delete(CitationIndexRecord).where(CitationIndexRecord.audit_id == str(audit_id))
                )
                session.commit()
            delete_relational_audit(str(audit_id))
        return removed

    def _save_summary(self, audit: AuditRun) -> None:
        engine = get_engine()
        if engine is None:
            return
        with Session(engine) as session:
            row = session.get(AuditSummaryRecord, str(audit.id))
            if row is None:
                row = AuditSummaryRecord(id=str(audit.id))
                session.add(row)
            row.paper_title = (audit.paper_title or "")[:512] or None
            row.status = audit.status
            row.coverage_percent = audit.coverage.coverage_percent
            row.failure_rate = audit.failures.confirmed_failure_rate
            row.risk_level = audit.risk_level.value
            row.citation_count = len(audit.citations)
            session.commit()


audit_store = AuditStore()
