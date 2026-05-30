import type { CitationRecord } from "../types";

type Props = {
  citation: CitationRecord;
  compact?: boolean;
};

export function ResolutionTrail({ citation, compact = false }: Props) {
  if (!citation.resolution_attempts.length) {
    return <p className="text-xs text-zinc-400">No resolution attempts logged.</p>;
  }

  return (
    <ul className={`space-y-1 font-audit ${compact ? "text-[10px]" : "text-xs"}`}>
      {citation.resolution_attempts.map((attempt, index) => (
        <li key={`${attempt.source}-${index}`} className="text-zinc-600">
          <span className={attempt.success ? "text-emerald-600" : "text-zinc-400"}>
            {attempt.success ? "+" : "-"}
          </span>{" "}
          <span className="text-zinc-500">{attempt.source}</span>: {attempt.summary}
          {!compact && attempt.query && (
            <span className="block truncate text-zinc-400">query: {attempt.query}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
