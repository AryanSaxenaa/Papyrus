from __future__ import annotations

import json

from app.domain.models import AuditRun


def render_text_report(audit: AuditRun) -> str:
    title = (audit.paper_title or "Untitled")[:80]
    lines = [
        "═══════════════════════════════════════════════════════════════",
        " PAPYRUS — CITATION INTEGRITY AUDIT",
        f" Paper: {title}",
        f" Analyzed: {audit.completed_at or audit.created_at}  |  Pipeline version: {audit.pipeline_version}",
        "═══════════════════════════════════════════════════════════════",
        "",
        " CITATION VERIFICATION COVERAGE",
        " ────────────────────────────────────────────────────────────",
        f" Total citations extracted:                              {audit.coverage.total:>3}",
        f" Resolved (Tier 1 — full text):                          {audit.coverage.tier_1:>3}",
        f" Resolved (Tier 2 — abstract only):                      {audit.coverage.tier_2:>3}",
        f" Resolved (Tier 3 — metadata only):                      {audit.coverage.tier_3:>3}",
        f" Unresolvable (outside indexed sources):                 {audit.coverage.tier_4:>3}",
        " ────────────────────────────────────────────────────────────",
        f" Coverage score:                                        {audit.coverage.coverage_percent:>3}%",
        "",
        " CONFIRMED CITATION FAILURES (resolvable citations only)",
        " ────────────────────────────────────────────────────────────",
        f" Type 1 — DOI 404:                                       {audit.failures.type_1:>3}",
        f" Type 2 — DOI Redirect:                                  {audit.failures.type_2:>3}",
        f" Type 5 — Date Impossible:                               {audit.failures.type_5:>3}",
        f" Type 6 — Title Drift:                                   {audit.failures.type_6:>3}",
        f" Type 7 — Claim Contradiction:                           {audit.failures.type_7:>3}",
        f" Retraction Flag:                                        {audit.failures.retraction:>3}",
        " ────────────────────────────────────────────────────────────",
        f" Confirmed failure rate (of resolved citations):        {audit.failures.confirmed_failure_rate}%",
        f" RISK ASSESSMENT:                                     {audit.risk_level.value.upper()}",
        "",
        " PER-CITATION VERDICTS",
        " ────────────────────────────────────────────────────────────",
    ]
    for citation in audit.citations:
        lines.append(f" [{citation.index}] {citation.bibliography.title or citation.bibliography.raw[:60]}")
        lines.append(
            f"     Intent: {citation.intent.value} | Tier: {citation.evidence_tier.value} | "
            f"Flag: {citation.hallucination_type.value}"
        )
        if citation.extracted_claim:
            lines.append(f"     Claim: {citation.extracted_claim[:160]}")
        if citation.claim_alignment_verdict:
            lines.append(f"     Alignment: {citation.claim_alignment_verdict} ({citation.confidence})")
        if citation.exa_signal:
            lines.append(f"     Exa: {citation.exa_signal}")
        if citation.source_verify_url:
            lines.append(f"     Verify: {citation.source_verify_url}")
        lines.append("")
    lines.extend(
        [
            " This is a citation integrity audit.",
            " Papyrus does not determine authorship or AI involvement.",
            "",
            " What this audit does not cover:",
            " - Misappropriated citations (real paper, fabricated intellectual link)",
            " - Research quality, self-citation manipulation, or author misconduct",
            "═══════════════════════════════════════════════════════════════",
        ]
    )
    return "\n".join(lines)


def render_json_report(audit: AuditRun) -> str:
    payload = {
        "audit": audit.model_dump(mode="json"),
        "disclaimer": {
            "scope": "citation_integrity_only",
            "not_ai_detection": True,
            "exa_absence_not_verdict": True,
        },
    }
    return json.dumps(payload, indent=2, default=str)
