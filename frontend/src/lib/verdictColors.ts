import type { CitationRecord } from "../types";

const VERDICT_FILL: Record<string, string> = {
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

export function isRetraction(citation: CitationRecord): boolean {
  return citation.hallucination_type === "retraction" || citation.verdict_color === "retraction";
}

export function citationFill(citation: CitationRecord): string {
  if (isRetraction(citation)) {
    return VERDICT_FILL.retraction;
  }
  return VERDICT_FILL[citation.verdict_color] ?? VERDICT_FILL.pending;
}

/** Tailwind ring classes for inline citation markers (text + PDF overlay). */
export function citationMarkerRingClass(citation: CitationRecord): string {
  return isRetraction(citation) ? "ring-1 ring-amber-400" : "";
}

export function citationCardClass(citation: CitationRecord): string {
  const base = "rounded-md border p-2 text-left";
  if (isRetraction(citation)) {
    return `${base} border-amber-400 ring-1 ring-amber-400/80`;
  }
  if (citation.verdict_color === "resolving" || citation.status === "resolving") {
    return `${base} border-white/10 animate-pulse`;
  }
  return `${base} border-white/10`;
}
