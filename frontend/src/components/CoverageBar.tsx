import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function CoverageBar({ audit }: Props) {
  const { coverage, citations } = audit;
  const total = coverage.total || 1;
  const failures = citations.filter(
    (c) =>
      c.verdict_color === "failure" ||
      c.verdict_color === "retraction" ||
      c.hallucination_type.includes("type_"),
  ).length;

  const segments = [
    { label: "Tier 1", value: coverage.tier_1, color: "bg-emerald-700" },
    { label: "Tier 2", value: coverage.tier_2, color: "bg-emerald-900" },
    { label: "Tier 3", value: coverage.tier_3, color: "bg-slate-600" },
    { label: "Unresolvable", value: coverage.tier_4, color: "bg-stone-600" },
  ].filter((segment) => segment.value > 0);

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
      <p className="text-xs text-[var(--papyrus-muted)]">
        Coverage confidence:{" "}
        <span className="font-audit uppercase text-stone-300">
          {audit.coverage.coverage_confidence ?? "medium"}
        </span>
        {failures > 0 && (
          <span className="ml-2 text-red-300/90">· {failures} confirmed failures (resolved citations)</span>
        )}
        {coverage.tier_4 > 0 && (
          <span className="ml-2">
            · {coverage.tier_4} unresolvable — may reflect database limits, not citation failure.
          </span>
        )}
      </p>
    </div>
  );
}
