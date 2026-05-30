from __future__ import annotations

from app.domain.models import AuditRun
from app.services.citations_index import sync_citation_index
from app.services.relational_audit import sync_relational_audit


def sync_postgres_audit_indexes(audit: AuditRun) -> None:
    """Update derived Postgres indexes after an audit payload is saved."""
    sync_citation_index(audit)
    sync_relational_audit(audit)
