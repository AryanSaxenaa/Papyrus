import type { CitationRecord } from "../types";

const VERDICT_FILL: Record<string, string> = {
  supported: "#166534",
  failure: "#991b1b",
  retraction: "#991b1b",
  cannot_assess: "#1e3a8a",
  neutral: "#78716c",
  unresolvable: "#52525b",
  resolving: "#b45309",
  pending: "#a1a1aa",
  amber: "#b45309",
};

export const COVERAGE_FILL: Record<string, string> = {
  "bg-emerald-600": "#16a34a",
  "bg-emerald-900": "#166534",
  "bg-sky-700": "#0369a1",
  "bg-stone-600": "#78716c",
  "bg-red-900": "#991b1b",
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
  return isRetraction(citation) ? "ring-1 ring-amber-500" : "";
}

export function citationCardClass(citation: CitationRecord): string {
  const base = "rounded-md border p-2 text-left text-white";
  if (isRetraction(citation)) {
    return `${base} border-amber-400 ring-1 ring-amber-400/80`;
  }
  if (citation.verdict_color === "resolving" || citation.status === "resolving") {
    return `${base} border-white/20 animate-pulse`;
  }
  return `${base} border-white/20`;
}
