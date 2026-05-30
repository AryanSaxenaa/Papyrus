from __future__ import annotations

from app.services.citations_index import sync_citation_index
from app.services.relational_audit import sync_relational_audit
from app.store import audit_store


def reindex_all_audits() -> dict[str, int]:
    indexed = 0
    relational = 0
    for audit in audit_store.list():
        if audit.status != "complete":
            continue
        sync_citation_index(audit)
        sync_relational_audit(audit)
        indexed += 1
        relational += 1
    return {"audits_indexed": indexed, "relational_synced": relational}
