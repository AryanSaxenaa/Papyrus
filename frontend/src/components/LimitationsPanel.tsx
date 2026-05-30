import type { AuditRun } from "../types";

const DEFAULT_LIMITATIONS = {
  misappropriation_not_detected:
    "Papyrus does not detect misappropriated citations where a real paper is cited out of context to support a claim its authors never made.",
  nli_quantitative_caveat:
    "NLI may not detect numerical discrepancies or causal vs correlational differences. Manual verification is recommended for quantitative claims.",
  out_of_scope: [
    "AI authorship detection",
    "Author Ghost (author publication history heuristics)",
    "Journal Phantom via DOAJ",
    "Circular citation analysis (v2)",
    "Self-citation manipulation",
    "Research quality beyond reference integrity",
  ],
};

type Props = {
  audit: AuditRun;
};

export function LimitationsPanel({ audit }: Props) {
  const limitations = audit.limitations;
  const fieldNote =
    limitations?.field_coverage_note ??
    (audit.coverage.tier_4 > 0
      ? `${audit.coverage.tier_4} citation(s) could not be verified by any indexed source. Coverage limitations may reflect field or language bias — not confirmed failures.`
      : null);

  return (
    <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-600">
      <p className="font-audit text-[10px] uppercase tracking-wide text-zinc-400">
        What this audit does not cover
      </p>
      {fieldNote && <p className="mt-2 leading-relaxed">{fieldNote}</p>}
      <p className="mt-2 leading-relaxed">
        {limitations?.misappropriation_not_detected ?? DEFAULT_LIMITATIONS.misappropriation_not_detected}
      </p>
      <p className="mt-2 leading-relaxed text-amber-700">
        {limitations?.nli_quantitative_caveat ?? DEFAULT_LIMITATIONS.nli_quantitative_caveat}
      </p>
      <ul className="mt-2 list-inside list-disc space-y-1 text-zinc-500">
        {(limitations?.out_of_scope ?? DEFAULT_LIMITATIONS.out_of_scope).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
