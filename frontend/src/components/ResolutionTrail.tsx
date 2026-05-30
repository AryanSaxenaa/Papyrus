import type { CitationRecord } from "../types";

type Props = {
  citation: CitationRecord;
  compact?: boolean;
};

export function ResolutionTrail({ citation, compact = false }: Props) {
  if (!citation.resolution_attempts.length) {
    return <p className="text-xs text-[var(--papyrus-muted)]">No resolution attempts logged.</p>;
  }

  return (
    <ul className={`space-y-1 font-audit ${compact ? "text-[10px]" : "text-xs"}`}>
      {citation.resolution_attempts.map((attempt, index) => (
        <li key={`${attempt.source}-${index}`} className="text-stone-300">
          <span className={attempt.success ? "text-emerald-400" : "text-stone-500"}>
            {attempt.success ? "✓" : "✗"}
          </span>{" "}
          <span className="text-stone-400">{attempt.source}</span>: {attempt.summary}
          {!compact && attempt.query && (
            <span className="block truncate text-stone-500">query: {attempt.query}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
