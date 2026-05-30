import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { coverageSegments } from "../lib/coverageSegments";
import { COVERAGE_FILL } from "../lib/verdictColors";
import type { AuditRun } from "../types";

type Props = {
  audit: AuditRun;
};

export function CoverageBar({ audit }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const total = audit.coverage.total || 1;
  const segments = coverageSegments(audit);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const width = svgEl.clientWidth || 480;
    const height = 10;
    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`).attr("role", "img").attr("aria-label", "Coverage bar");

    const scale = d3.scaleLinear().domain([0, total]).range([0, width]);
    let x = 0;
    for (const segment of segments) {
      const segmentWidth = scale(segment.value);
      if (segmentWidth <= 0) continue;
      svg
        .append("rect")
        .attr("x", x)
        .attr("y", 0)
        .attr("width", segmentWidth)
        .attr("height", height)
        .attr("rx", 3)
        .attr("fill", COVERAGE_FILL[segment.color] ?? "#78716c");
      x += segmentWidth;
    }
  }, [audit.id, segments, total]);

  return (
    <div className="space-y-2">
      <svg ref={svgRef} className="h-2.5 w-full rounded-full overflow-hidden" />
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-zinc-400">
        {segments.map((segment) => (
          <span key={segment.label}>
            {segment.label} {segment.value}
          </span>
        ))}
      </div>
      <p className="text-xs text-zinc-500">
        Coverage confidence:{" "}
        <span className="font-audit uppercase text-zinc-700 font-medium">
          {audit.coverage.coverage_confidence ?? "medium"}
        </span>
        <span className="ml-2 text-zinc-400">
          · Risk uses confirmed failures only (not unresolvable citations).
        </span>
        {audit.coverage.tier_4 > 0 && (
          <span className="ml-2 text-zinc-400">
            · {audit.coverage.tier_4} unresolvable - may reflect database limits, not citation
            failure.
          </span>
        )}
      </p>
    </div>
  );
}
