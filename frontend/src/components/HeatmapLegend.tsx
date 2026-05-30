const items = [
  { label: "Supported", color: "#166534" },
  { label: "Failure", color: "#991b1b" },
  { label: "Retraction", color: "#991b1b", ring: true },
  { label: "Cannot assess", color: "#1e3a8a" },
  { label: "Unresolvable", color: "#52525b" },
  { label: "Resolving", color: "#b45309" },
  { label: "Pending", color: "#a1a1aa" },
];

export function HeatmapLegend() {
  return (
    <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-zinc-500">
      {items.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-1.5">
          <span
            className={`h-2.5 w-2.5 rounded-sm ${item.ring ? "ring-1 ring-amber-400" : ""}`}
            style={{ backgroundColor: item.color }}
          />
          {item.label}
        </span>
      ))}
      <span className="text-zinc-400 normal-case">
        Unresolvable (grey) is separate from confirmed failure (red).
      </span>
    </div>
  );
}
