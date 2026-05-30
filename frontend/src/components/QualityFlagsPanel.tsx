import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function QualityFlagsPanel({ audit }: Props) {
  const summary = audit.quality_summary;
  if (!summary) return null;

  const duplicates = (summary.duplicate_dois as Array<{ doi: string; citation_indices: number[] }>) ?? [];
  const circular = (summary.circular_pairs as Array<{ citation_a: number; citation_b: number; note?: string }>) ?? [];
  const cycles = (summary.circular_cycles as Array<{ citation_indices: number[]; length?: number }>) ?? [];

  if (!duplicates.length && !circular.length && !cycles.length) return null;

  return (
    <div className="mt-4 rounded-md border border-violet-900/40 bg-violet-950/20 p-3 text-xs text-violet-100">
      <p className="font-audit text-[10px] uppercase tracking-wide text-violet-300">
        Quality signals (not hallucination verdicts)
      </p>
      {duplicates.length > 0 && (
        <ul className="mt-2 space-y-1">
          {duplicates.map((entry) => (
            <li key={entry.doi}>
              Duplicate DOI <span className="font-audit">{entry.doi}</span> at citations{" "}
              {entry.citation_indices.join(", ")}
            </li>
          ))}
        </ul>
      )}
      {circular.length > 0 && (
        <ul className="mt-2 space-y-1">
          {circular.map((pair) => (
            <li key={`${pair.citation_a}-${pair.citation_b}`}>
              Circular signal: #{pair.citation_a} ↔ #{pair.citation_b}
              {pair.note && <span className="block text-violet-200/70">{pair.note}</span>}
            </li>
          ))}
        </ul>
      )}
      {cycles.length > 0 && (
        <ul className="mt-2 space-y-1">
          {cycles.map((cycle) => (
            <li key={cycle.citation_indices.join("-")}>
              Multi-hop cycle ({cycle.length ?? cycle.citation_indices.length} hops): #
              {cycle.citation_indices.join(" → #")}
            </li>
          ))}
        </ul>
      )}
      {!summary.circular_check_enabled && !circular.length && !cycles.length && duplicates.length > 0 && (
        <p className="mt-2 text-violet-200/60">
          Enable <span className="font-audit">ENABLE_CIRCULAR_CHECK=true</span> for reciprocal and multi-hop cycle scanning.
        </p>
      )}
    </div>
  );
}
