import type { CitationRecord } from "../types";

export const VERDICT_FILL: Record<string, string> = {
  supported: "#1a4d3e",
  failure: "#6b1f2a",
  retraction: "#6b1f2a",
  cannot_assess: "#3d4f5c",
  neutral: "#4a524e",
  unresolvable: "#3a403d",
  resolving: "#8b6914",
  pending: "#2a312e",
  amber: "#8b6914",
};

export const COVERAGE_FILL: Record<string, string> = {
  "bg-emerald-600": "#059669",
  "bg-emerald-900": "#064e3b",
  "bg-slate-600": "#475569",
  "bg-stone-600": "#57534e",
  "bg-red-900": "#7f1d1d",
};

export function citationFill(citation: CitationRecord): string {
  if (citation.hallucination_type === "retraction" || citation.verdict_color === "retraction") {
    return VERDICT_FILL.retraction;
  }
  return VERDICT_FILL[citation.verdict_color] ?? VERDICT_FILL.pending;
}
