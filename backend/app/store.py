from __future__ import annotations

from uuid import UUID

from app.domain.models import AuditRun


class AuditStore:
    def __init__(self) -> None:
        self._audits: dict[UUID, AuditRun] = {}

    def create(self, audit: AuditRun) -> AuditRun:
        self._audits[audit.id] = audit
        return audit

    def get(self, audit_id: UUID) -> AuditRun | None:
        return self._audits.get(audit_id)

    def save(self, audit: AuditRun) -> None:
        self._audits[audit.id] = audit

    def list(self) -> list[AuditRun]:
        return sorted(self._audits.values(), key=lambda item: item.created_at, reverse=True)


audit_store = AuditStore()
