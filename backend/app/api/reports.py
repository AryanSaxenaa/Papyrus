from __future__ import annotations

import json

from app.domain.models import AuditRun
from app.pipeline.limitations import build_limitations


def render_text_report(audit: AuditRun) -> str:
    title = (audit.paper_title or "Untitled")[:80]
    total = audit.coverage.total or 1
    pct = lambda count: round((count / total) * 100, 1)

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
        f" Resolved (Tier 1 — full text):                         {audit.coverage.tier_1:>3}   ({pct(audit.coverage.tier_1)}%)",
        f" Resolved (Tier 2 — abstract only):                      {audit.coverage.tier_2:>3}   ({pct(audit.coverage.tier_2)}%)",
        f" Resolved (Tier 3 — metadata only):                      {audit.coverage.tier_3:>3}   ({pct(audit.coverage.tier_3)}%)",
        f" Unresolvable (outside indexed sources):                {audit.coverage.tier_4:>3}   ({pct(audit.coverage.tier_4)}%)",
        " ────────────────────────────────────────────────────────────",
        f" Coverage score:                                        {audit.coverage.coverage_percent:>3}%",
        f" Coverage confidence:                      {audit.coverage.coverage_confidence.value.upper()}",
    ]
    if audit.coverage.tier_4:
        lines.append(
            f" Note: {audit.coverage.tier_4} citations outside indexed sources."
            " Field-specific coverage limitations may apply."
        )
    lines.extend(
        [
            "",
            " CONFIRMED CITATION FAILURES (resolvable citations only)",
            " ────────────────────────────────────────────────────────────",
            f" Verified + claim supported:                            {audit.failures.supported:>3}",
            f" Verified + claim not supported:                         {audit.failures.not_supported:>3}",
            f" Verified + cannot assess claim [paywalled]:             {audit.failures.cannot_assess:>3}",
            f" Type 1 — DOI 404:                                       {audit.failures.type_1:>3}",
            f" Type 2 — DOI Redirect:                                  {audit.failures.type_2:>3}",
            f" Type 5 — Date Impossible:                               {audit.failures.type_5:>3}",
            f" Type 6 — Title Drift:                                   {audit.failures.type_6:>3}",
            f" Type 7 — Claim Contradiction:                           {audit.failures.type_7:>3}",
            f" Retraction Flag:                                        {audit.failures.retraction:>3}",
            f" Version Mismatch:                                       {audit.failures.version_mismatch:>3}",
            " ────────────────────────────────────────────────────────────",
            f" Confirmed failure rate (of resolved citations):        {audit.failures.confirmed_failure_rate}%",
            f" RISK ASSESSMENT:                                     {audit.risk_level.value.upper()}",
            f" Risk confidence:                                   {audit.risk_confidence.value.upper()}",
            " Basis: Risk derived from confirmed failures only.",
            "",
            " PER-CITATION VERDICTS",
            " ────────────────────────────────────────────────────────────",
        ]
    )
    for citation in audit.citations:
        lines.append(f" [{citation.index}] {citation.bibliography.title or citation.bibliography.raw[:60]}")
        lines.append(
            f"     Intent: {citation.intent.value} | Tier: {citation.evidence_tier.value} | "
            f"Flag: {citation.hallucination_type.value}"
        )
        if citation.title_edit_distance is not None:
            lines.append(f"     Title edit distance: {citation.title_edit_distance}%")
        if citation.extracted_claim:
            lines.append(f"     Claim: {citation.extracted_claim[:160]}")
        if citation.claim_user_corrected:
            lines.append(f"     Claim (user-corrected): {citation.claim_user_corrected[:160]}")
        if citation.claim_alignment_verdict:
            lines.append(f"     Alignment: {citation.claim_alignment_verdict} ({citation.confidence})")
        if citation.evidence_provenance:
            lines.append(f"     Evidence: {citation.evidence_provenance}")
        if citation.evidence_retrieved_at:
            lines.append(f"     Evidence retrieved: {citation.evidence_retrieved_at}")
        if citation.evidence_passage:
            lines.append(f"     Passage: {citation.evidence_passage[:240]}")
        if citation.resolution_attempts:
            lines.append("     Resolution trail:")
            for attempt in citation.resolution_attempts:
                mark = "✓" if attempt.success else "✗"
                lines.append(f"       {mark} {attempt.source.value}: {attempt.summary} ({attempt.query[:60]})")
        if citation.version_mismatch:
            lines.append("     Version timeline:")
            for entry in [citation.version_mismatch.preprint, *citation.version_mismatch.revisions, citation.version_mismatch.published]:
                if entry:
                    lines.append(f"       - {entry.label}: {entry.title or '—'} ({entry.date or '—'})")
        if citation.quantitative_caveat:
            lines.append(f"     Caveat: {citation.quantitative_caveat[:200]}")
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


def render_pdf_bytes(audit: AuditRun) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    text = render_text_report(audit).encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 6, text)
    return bytes(pdf.output())


def render_json_report(audit: AuditRun) -> str:
    payload = {
        "audit": audit.model_dump(mode="json"),
        "limitations": audit.limitations or build_limitations(audit),
        "disclaimer": {
            "scope": "citation_integrity_only",
            "not_ai_detection": True,
            "exa_absence_not_verdict": True,
            "unresolvable_not_failure": True,
        },
    }
    return json.dumps(payload, indent=2, default=str)
