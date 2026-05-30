from __future__ import annotations

from typing import Any

from app.domain.models import AuditRun


def build_limitations(audit: AuditRun) -> dict[str, Any]:
    unresolvable = audit.coverage.tier_4
    return {
        "not_ai_detection": True,
        "exa_absence_not_verdict": True,
        "unresolvable_count": unresolvable,
        "field_coverage_note": (
            f"{unresolvable} citation(s) could not be verified by any indexed source. "
            "This may reflect database coverage limitations rather than citation failure, "
            "particularly for older sources, books, and non-English publications."
            if unresolvable
            else None
        ),
        "misappropriation_not_detected": (
            "Papyrus does not detect misappropriated citations where a real paper is cited "
            "out of context to support a claim its authors never made."
        ),
        "nli_quantitative_caveat": (
            "NLI may not detect numerical discrepancies or causal vs correlational differences. "
            "Manual verification is recommended for quantitative claims."
        ),
        "out_of_scope": [
            "AI authorship detection",
            "Self-citation manipulation",
            "Research quality beyond reference integrity",
        ],
        "quality_signals": audit.quality_summary,
        "duplicate_doi_count": len((audit.quality_summary or {}).get("duplicate_dois", [])),
        "circular_pair_count": len((audit.quality_summary or {}).get("circular_pairs", [])),
    }
