import type { AuditRun, CitationRecord } from "../types";

export type CoverageSegment = {
  label: string;
  value: number;
  color: string;
};

function isConfirmedFailure(citation: CitationRecord): boolean {
  if (citation.verdict_color === "unresolvable" || citation.evidence_tier === "tier_4") {
    return false;
  }
  return (
    citation.verdict_color === "failure" ||
    citation.verdict_color === "retraction" ||
    (citation.hallucination_type?.startsWith("type_") ?? false) ||
    citation.claim_alignment_verdict === "claim_contradiction" ||
    citation.claim_alignment_verdict === "not_addressed"
  );
}

/** Partition citations into spec-aligned bar segments (mutually exclusive). */
export function coverageSegments(audit: AuditRun): CoverageSegment[] {
  let tier1 = 0;
  let tier2 = 0;
  let tier3 = 0;
  let unresolvable = 0;
  let failures = 0;

  for (const citation of audit.citations) {
    if (citation.verdict_color === "unresolvable" || citation.evidence_tier === "tier_4") {
      unresolvable += 1;
      continue;
    }
    if (isConfirmedFailure(citation)) {
      failures += 1;
      continue;
    }
    if (citation.evidence_tier === "tier_1") tier1 += 1;
    else if (citation.evidence_tier === "tier_2") tier2 += 1;
    else if (citation.evidence_tier === "tier_3") tier3 += 1;
    else unresolvable += 1;
  }

  return [
    { label: "Tier 1", value: tier1, color: "bg-emerald-600" },
    { label: "Tier 2", value: tier2, color: "bg-emerald-900" },
    { label: "Cannot assess", value: tier3, color: "bg-sky-700" },
    { label: "Unresolvable", value: unresolvable, color: "bg-stone-600" },
    { label: "Confirmed failure", value: failures, color: "bg-red-900" },
  ].filter((segment) => segment.value > 0);
}
