import type { CitationRecord } from "../types";

export function verdictBadgeLabel(citation: CitationRecord): string {
  if (citation.hallucination_type === "retraction" || citation.verdict_color === "retraction") {
    return "RETRACTED";
  }
  if (citation.claim_alignment_verdict === "supported" || citation.verdict_color === "supported") {
    return "SUPPORTED";
  }
  if (
    citation.claim_alignment_verdict === "claim_contradiction" ||
    citation.hallucination_type === "type_7_claim_contradiction"
  ) {
    return "CONTRADICTED";
  }
  if (citation.verdict_color === "unresolvable") {
    return "UNRESOLVED";
  }
  if (citation.verdict_color === "cannot_assess" || citation.claim_alignment_verdict === "cannot_determine") {
    return "CANNOT ASSESS";
  }
  if (citation.verdict_color === "failure" || citation.hallucination_type.startsWith("type_")) {
    return "FAILURE";
  }
  if (citation.verdict_color === "resolving") {
    return "RESOLVING";
  }
  if (citation.intent !== "evidentiary") {
    return citation.intent.slice(0, 4).toUpperCase();
  }
  return "PENDING";
}
