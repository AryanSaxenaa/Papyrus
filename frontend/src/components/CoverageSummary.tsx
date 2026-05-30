import type { AuditRun, HeatmapFilter } from "../types";

const CHIPS: Array<{
  key: HeatmapFilter;
  label: string;
  count: (audit: AuditRun) => number;
  category: "neutral" | "indicator" | "failure";
}> = [
  {
    key: "all",
    label: "All",
    count: (a) => a.citations.length,
    category: "neutral",
  },
  {
    key: "supported",
    label: "Supported",
    count: (a) => a.failures.supported ?? 0,
    category: "neutral",
  },
  {
    key: "contradictions",
    label: "Contradicted",
    count: (a) => a.failures.type_7 ?? 0,
    category: "failure",
  },
  {
    key: "cannot_assess",
    label: "Cannot assess",
    count: (a) => a.failures.cannot_assess ?? 0,
    category: "indicator",
  },
  {
    key: "unresolvable",
    label: "Unresolvable",
    count: (a) => a.coverage.tier_4 ?? 0,
    category: "neutral",
  },
  {
    key: "failures",
    label: "Confirmed failure",
    count: (a) => {
      const f = a.failures;
      return (
        (f.type_1 ?? 0) +
        (f.type_2 ?? 0) +
        (f.type_5 ?? 0) +
        (f.type_6 ?? 0) +
        (f.type_7 ?? 0) +
        (f.retraction ?? 0) +
        (f.version_mismatch ?? 0) +
        (f.not_supported ?? 0)
      );
    },
    category: "failure",
  },
  {
    key: "retracted",
    label: "Retracted",
    count: (a) => a.failures.retraction ?? 0,
    category: "failure",
  },
];

type Props = {
  audit: AuditRun;
  filter: HeatmapFilter;
  onFilter: (filter: HeatmapFilter) => void;
};

export function CoverageSummary({ audit, filter, onFilter }: Props) {
  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-2">
        {CHIPS.map((chip) => (
          <button
            key={chip.key}
            type="button"
            onClick={() => onFilter(filter === chip.key && chip.key !== "all" ? "all" : chip.key)}
            className={`rounded-full border px-3 py-1 font-audit text-xs transition-colors ${
              filter === chip.key
                ? chip.category === "indicator"
                  ? "border-[#bfdbfe] bg-[#eff6ff] font-semibold text-[#1e3a8a]"
                  : chip.category === "failure"
                    ? "border-[#fecaca] bg-[#fef2f2] font-semibold text-[#991b1b]"
                    : "border-[#bbf7d0] bg-[#ecfdf3] font-semibold text-[#0a3d2e]"
                : "border-zinc-300 bg-white text-zinc-600 hover:bg-zinc-50 hover:border-zinc-400"
            }`}
          >
            {chip.label}
            <span className="ml-1 opacity-70">{chip.count(audit)}</span>
          </button>
        ))}
      </div>
      {(audit.failures.cannot_assess ?? 0) > 0 && (
        <p className="mt-1.5 text-[10px] leading-relaxed text-zinc-400">
          Cannot assess = metadata-only resolution; these are{" "}
          <span className="font-semibold text-zinc-500">not counted as failures</span> in risk
          assessment.
        </p>
      )}
    </div>
  );
}
