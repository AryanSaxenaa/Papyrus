import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { verdictBadgeLabel } from "../lib/verdictLabel";
import { citationCardClass, citationFill } from "../lib/verdictColors";
import type { CitationRecord } from "../types";

type Props = {
  citations: CitationRecord[];
  selectedId?: string | null;
  onSelect: (citation: CitationRecord) => void;
};

export function CitationHeatmap({ citations, selectedId, onSelect }: Props) {
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const grid = gridRef.current;
    if (!grid) return;
    d3.select(grid)
      .selectAll<HTMLButtonElement, CitationRecord>("button[data-citation-id]")
      .data(citations, (d) => d.id)
      .transition()
      .duration(500)
      .style("background-color", (d) => citationFill(d));
  }, [citations]);

  return (
    <div
      ref={gridRef}
      className="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2"
    >
      {citations.map((citation) => (
        <button
          key={citation.id}
          type="button"
          data-citation-id={citation.id}
          id={`heatmap-citation-${citation.id}`}
          onClick={() => onSelect(citation)}
          className={`${citationCardClass(citation)} transition hover:scale-[1.02] ${
            selectedId === citation.id ? "ring-2 ring-[#86efac]" : ""
          }`}
          style={{ backgroundColor: citationFill(citation) }}
        >
          <p className="font-audit text-xs opacity-80">#{citation.index}</p>
          <p className="truncate text-sm font-semibold">
            {citation.bibliography.authors[0] ?? "Unknown"}
          </p>
          <p className="text-xs opacity-80">{citation.bibliography.year ?? "—"}</p>
          <p className="mt-1 font-audit text-[9px] font-semibold uppercase tracking-wide opacity-90">
            {verdictBadgeLabel(citation)}
          </p>
        </button>
      ))}
    </div>
  );
}
