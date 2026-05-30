import { coverageSegments } from "../lib/coverageSegments";
import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function CoverageBar({ audit }: Props) {
  const total = audit.coverage.total || 1;
  const segments = coverageSegments(audit);

  return (
    <div className="space-y-2">
      <div className="flex h-3 overflow-hidden rounded-full border border-white/10">
        {segments.map((segment) => (
          <div
            key={segment.label}
            className={segment.color}
            style={{ width: `${(segment.value / total) * 100}%` }}
            title={`${segment.label}: ${segment.value}`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-stone-500">
        {segments.map((segment) => (
          <span key={segment.label}>
            {segment.label} {segment.value}
          </span>
        ))}
      </div>
      <p className="text-xs text-[var(--papyrus-muted)]">
        Coverage confidence:{" "}
        <span className="font-audit uppercase text-stone-300">
          {audit.coverage.coverage_confidence ?? "medium"}
        </span>
        <span className="ml-2 text-stone-400">
          · Risk uses confirmed failures only (not unresolvable citations).
        </span>
        {audit.coverage.tier_4 > 0 && (
          <span className="ml-2">
            · {audit.coverage.tier_4} unresolvable — may reflect database limits, not citation failure.
          </span>
        )}
      </p>
    </div>
  );
}
