import type { AuditRun, HeatmapFilter } from "../types";

const CHIPS: Array<{ key: HeatmapFilter; label: string; count: (audit: AuditRun) => number }> = [
  {
    key: "supported",
    label: "Supported",
    count: (a) => a.failures.supported ?? 0,
  },
  {
    key: "contradictions",
    label: "Contradicted",
    count: (a) => a.failures.type_7 ?? 0,
  },
  {
    key: "cannot_assess",
    label: "Cannot assess",
    count: (a) => a.failures.cannot_assess ?? 0,
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
  },
  {
    key: "retracted",
    label: "Retracted",
    count: (a) => a.failures.retraction ?? 0,
  },
];

type Props = {
  audit: AuditRun;
  filter: HeatmapFilter;
  onFilter: (filter: HeatmapFilter) => void;
};

export function CoverageSummary({ audit, filter, onFilter }: Props) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {CHIPS.map((chip) => (
        <button
          key={chip.key}
          type="button"
          onClick={() => onFilter(chip.key)}
          className={`rounded-full border px-3 py-1 font-audit text-xs transition ${
            filter === chip.key
              ? "border-emerald-600/60 bg-emerald-950/50 text-emerald-100"
              : "border-white/10 bg-black/20 text-stone-300 hover:bg-white/5"
          }`}
        >
          {chip.label}
          <span className="ml-1 opacity-70">{chip.count(audit)}</span>
        </button>
      ))}
    </div>
  );
}
