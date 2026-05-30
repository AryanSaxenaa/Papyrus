const items = [
  { label: "Supported", className: "bg-[var(--papyrus-green)]" },
  { label: "Failure", className: "bg-[var(--papyrus-crimson)]" },
  { label: "Cannot assess", className: "bg-[var(--papyrus-steel)]" },
  { label: "Unresolvable", className: "bg-[#4a524e]" },
  { label: "Resolving", className: "bg-[var(--papyrus-amber)]" },
  { label: "Pending", className: "bg-[#2a312e]" },
];

export function HeatmapLegend() {
  return (
    <div className="mt-2 flex flex-wrap gap-3 text-[10px] uppercase tracking-wide text-[var(--papyrus-muted)]">
      {items.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-1.5">
          <span className={`h-2.5 w-2.5 rounded-sm ${item.className}`} />
          {item.label}
        </span>
      ))}
    </div>
  );
}
