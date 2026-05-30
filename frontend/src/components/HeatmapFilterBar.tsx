import type { HeatmapFilter } from "../types";

const OPTIONS: Array<{ key: HeatmapFilter; label: string }> = [
  { key: "all", label: "All citations" },
  { key: "failures", label: "Confirmed failures only" },
  { key: "unresolvable", label: "Unresolvable only" },
  { key: "contradictions", label: "Claim contradictions only" },
  { key: "retracted", label: "Retracted only" },
];

type Props = {
  filter: HeatmapFilter;
  onFilter: (filter: HeatmapFilter) => void;
};

export function HeatmapFilterBar({ filter, onFilter }: Props) {
  return (
    <label className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
      <span className="font-audit uppercase tracking-wide">Filter</span>
      <select
        value={filter}
        onChange={(e) => onFilter(e.target.value as HeatmapFilter)}
        className="papyrus-input py-1 font-audit text-xs"
      >
        {OPTIONS.map((option) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
