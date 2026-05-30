import { lazy, Suspense, useState } from "react";
import { CoverageBar } from "../CoverageBar";
import { CoverageSummary } from "../CoverageSummary";
import { HeatmapLegend } from "../HeatmapLegend";
import { DEMO_AUDIT } from "../../data/demoAudit";
import type { HeatmapFilter } from "../../types";

const CitationHeatmap = lazy(() =>
  import("../CitationHeatmap").then((m) => ({ default: m.CitationHeatmap })),
);

type Props = {
  /** Hide heatmap section (e.g. compact hero). */
  showHeatmap?: boolean;
  className?: string;
};

/**
 * Renders the same audit dashboard blocks as `/app` using the bundled demo audit fixture.
 */
export function DemoAuditPreview({ showHeatmap = true, className = "" }: Props) {
  const audit = DEMO_AUDIT;
  const [filter, setFilter] = useState<HeatmapFilter>("all");

  const filtered = audit.citations.filter((citation) => {
    if (filter === "all") return true;
    if (filter === "supported") return citation.verdict_color === "supported";
    if (filter === "contradictions") return citation.hallucination_type === "type_7";
    if (filter === "cannot_assess") return citation.verdict_color === "cannot_assess";
    if (filter === "unresolvable") {
      return citation.verdict_color === "unresolvable" || citation.evidence_tier === "tier_4";
    }
    if (filter === "retracted") {
      return citation.hallucination_type === "retraction" || citation.verdict_color === "retraction";
    }
    if (filter === "failures") {
      return (
        citation.verdict_color === "failure" ||
        citation.verdict_color === "retraction" ||
        (citation.hallucination_type?.startsWith("type_") ?? false)
      );
    }
    return true;
  });

  const tier2Plus = audit.coverage.tier_1 + audit.coverage.tier_2;

  return (
    <div className={`text-left ${className}`}>
      <p className="papyrus-eyebrow">Current audit</p>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-serif-display text-[15px] font-bold leading-snug text-[#0a3d2e] sm:text-base">
            {audit.paper_title}
          </h3>
          <p className="mt-1 font-audit text-[10px] text-zinc-400">
            Status: {audit.status} · Pipeline {audit.pipeline_version}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <p className="font-audit text-2xl font-semibold text-[#0a3d2e] sm:text-3xl">
            {audit.coverage.coverage_percent}%
          </p>
          <p className="text-[10px] text-zinc-500">
            Coverage ({tier2Plus} of {audit.coverage.total} at Tier 2+)
          </p>
          <p className="mt-1 font-audit text-[11px] font-semibold uppercase text-amber-700">
            {audit.risk_level} risk
            <span className="ml-1 text-[10px] font-normal normal-case text-zinc-500">
              ({audit.risk_confidence} confidence)
            </span>
          </p>
        </div>
      </div>

      <div className="mt-3">
        <CoverageBar audit={audit} />
      </div>
      <CoverageSummary audit={audit} filter={filter} onFilter={setFilter} />

      {showHeatmap && (
        <div className="mt-4 border-t border-zinc-100 pt-4">
          <p className="papyrus-section-title text-[11px]">Citation heatmap</p>
          <HeatmapLegend />
          <div className="mt-2 max-h-[220px] overflow-hidden">
            <Suspense
              fallback={
                <p className="py-8 text-center font-audit text-xs text-zinc-400">
                  Loading heatmap…
                </p>
              }
            >
              <CitationHeatmap
                citations={filtered.length > 0 ? filtered : audit.citations}
                onSelect={() => undefined}
              />
            </Suspense>
          </div>
        </div>
      )}
    </div>
  );
}
