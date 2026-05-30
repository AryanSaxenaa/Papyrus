import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import type { VersionMismatchInfo } from "../types";

type Props = {
  info: VersionMismatchInfo;
};

type TimelineNode = {
  id: string;
  label: string;
  date: Date | null;
  title: string | null;
  abstract: string | null;
};

function parseDate(raw: string | null | undefined): Date | null {
  if (!raw) return null;
  const parsed = Date.parse(raw);
  return Number.isNaN(parsed) ? null : new Date(parsed);
}

export function VersionMismatchTimeline({ info }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  const nodes = useMemo(() => {
    const entries: TimelineNode[] = [];
    if (info.preprint) {
      entries.push({
        id: "preprint",
        label: info.preprint.label,
        date: parseDate(info.preprint.date),
        title: info.preprint.title ?? null,
        abstract: info.preprint.abstract ?? null,
      });
    }
    info.revisions.forEach((revision, index) => {
      entries.push({
        id: `revision-${index}`,
        label: revision.label,
        date: parseDate(revision.date),
        title: revision.title ?? null,
        abstract: revision.abstract ?? null,
      });
    });
    if (info.published) {
      entries.push({
        id: "published",
        label: info.published.label,
        date: parseDate(info.published.date),
        title: info.published.title ?? null,
        abstract: info.published.abstract ?? null,
      });
    }
    return entries;
  }, [info]);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || !nodes.length) return;

    const width = svgEl.clientWidth || 520;
    const height = 72;
    const margin = { top: 28, right: 16, bottom: 8, left: 16 };
    const innerWidth = width - margin.left - margin.right;

    const svg = d3.select(svgEl);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const dated = nodes.filter((node) => node.date);
    const xScale =
      dated.length >= 2
        ? d3
            .scaleTime()
            .domain(d3.extent(dated, (node) => node.date!) as [Date, Date])
            .range([0, innerWidth])
        : d3.scalePoint<string>().domain(nodes.map((node) => node.id)).range([0, innerWidth]).padding(0.2);

    g.append("line")
      .attr("x1", 0)
      .attr("x2", innerWidth)
      .attr("y1", 0)
      .attr("y2", 0)
      .attr("stroke", "#d97706")
      .attr("stroke-width", 1.5)
      .attr("opacity", 0.5);

    nodes.forEach((node) => {
      const x =
        node.date && dated.length >= 2
          ? (xScale as d3.ScaleTime<number, number>)(node.date)
          : (xScale as d3.ScalePoint<string>)(node.id) ?? 0;

      g.append("circle")
        .attr("cx", x)
        .attr("cy", 0)
        .attr("r", node.id === "published" ? 6 : 5)
        .attr("fill", node.id === "published" ? "#f59e0b" : "#d97706");

      g.append("text")
        .attr("x", x)
        .attr("y", -12)
        .attr("text-anchor", "middle")
        .attr("fill", "#92400e")
        .attr("font-size", 10)
        .text(node.label);

      if (node.date) {
        g.append("text")
          .attr("x", x)
          .attr("y", 16)
          .attr("text-anchor", "middle")
          .attr("fill", "#71717a")
          .attr("font-size", 9)
          .text(d3.timeFormat("%Y-%m-%d")(node.date));
      }
    });
  }, [nodes]);

  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Version timeline</p>
      <svg ref={svgRef} className="h-[72px] w-full" />
      {info.material_difference && (
        <p className="text-xs text-amber-700">
          Material difference detected between preprint and published versions.
        </p>
      )}
      {info.material_difference && info.preprint?.abstract && info.published?.abstract && (
        <div className="grid gap-2 md:grid-cols-2">
          <AbstractBlock label="Preprint abstract" text={info.preprint.abstract} />
          <AbstractBlock label="Published abstract" text={info.published.abstract} />
        </div>
      )}
      {nodes.map((node) => (
        <div key={node.id} className="border-l-2 border-amber-300 pl-3">
          <p className="font-audit text-xs text-amber-700">{node.label}</p>
          {node.title && <p className="mt-1 text-xs font-semibold text-zinc-800">{node.title}</p>}
          {node.abstract && (
            <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
              {node.abstract.slice(0, 280)}...
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

function AbstractBlock({ label, text }: { label: string; text: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-2">
      <p className="font-audit text-[10px] uppercase text-amber-700">{label}</p>
      <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">{text.slice(0, 400)}...</p>
    </div>
  );
}
