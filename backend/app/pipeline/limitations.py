from __future__ import annotations

from app.domain.models import AuditLimitations, AuditRun


def build_limitations(audit: AuditRun) -> AuditLimitations:
    unresolvable = audit.coverage.tier_4
    return AuditLimitations(
        unresolvable_count=unresolvable,
        field_coverage_note=(
            f"{unresolvable} citation(s) could not be verified by any indexed source. "
            "This may reflect database coverage limitations rather than citation failure, "
            "particularly for older sources, books, and non-English publications."
            if unresolvable
            else None
        ),
    )
