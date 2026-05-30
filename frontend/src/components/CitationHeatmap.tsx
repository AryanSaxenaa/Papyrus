import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { verdictBadgeLabel } from "../lib/verdictLabel";
import { citationCardClass, citationFill } from "../lib/verdictColors";
import type { CitationRecord } from "../types";

type Props = {
  citations: CitationRecord[];
  selectedId?: string | null;
  onSelect: (citation: CitationRecord) => void;
};

const CELL = 96;
const CARD_W = CELL - 10;
const CARD_H = CELL - 6;

type LayoutNode = {
  id: string;
  citation: CitationRecord;
  targetX: number;
  targetY: number;
  x: number;
  y: number;
};

export function CitationHeatmap({ citations, selectedId, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  const safeCitations = useMemo(
    () => citations.filter((citation): citation is CitationRecord => Boolean(citation?.id)),
    [citations],
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.width;
      if (next && next > 0) setWidth(next);
    });
    observer.observe(el);
    setWidth(el.clientWidth || 640);
    return () => observer.disconnect();
  }, []);

  const { height, targets } = useMemo(() => {
    const cols = Math.max(1, Math.floor(width / CELL));
    const rows = Math.max(1, Math.ceil(safeCitations.length / cols));
    const map: Record<string, { x: number; y: number }> = {};
    safeCitations.forEach((citation, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      map[citation.id] = {
        x: col * CELL + CELL / 2,
        y: row * CELL + CELL / 2,
      };
    });
    return { height: rows * CELL + 12, targets: map };
  }, [safeCitations, width]);

  useEffect(() => {
    if (!safeCitations.length) {
      setPositions({});
      return;
    }

    const nodes: LayoutNode[] = safeCitations.map((citation) => {
      const target = targets[citation.id] ?? { x: CELL / 2, y: CELL / 2 };
      return {
        id: citation.id,
        citation,
        targetX: target.x,
        targetY: target.y,
        x: target.x + (Math.random() - 0.5) * 12,
        y: target.y + (Math.random() - 0.5) * 12,
      };
    });

    const simulation = d3
      .forceSimulation(nodes)
      .force("x", d3.forceX<LayoutNode>((d) => d.targetX).strength(0.42))
      .force("y", d3.forceY<LayoutNode>((d) => d.targetY).strength(0.42))
      .force("collide", d3.forceCollide<LayoutNode>(CELL * 0.48))
      .alpha(0.85)
      .alphaDecay(0.055);

    let frame = 0;
    simulation.on("tick", () => {
      frame += 1;
      if (frame % 2 !== 0 && simulation.alpha() > 0.12) return;
      setPositions(
        Object.fromEntries(nodes.map((node) => [node.id, { x: node.x, y: node.y }])),
      );
    });

    simulation.on("end", () => {
      setPositions(
        Object.fromEntries(nodes.map((node) => [node.id, { x: node.x, y: node.y }])),
      );
    });

    return () => {
      simulation.stop();
    };
  }, [safeCitations, targets]);

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden rounded-lg border border-zinc-100 bg-zinc-50/50"
      style={{ height, minHeight: CELL }}
      role="list"
      aria-label="Citation integrity heatmap"
    >
      {safeCitations.map((citation) => {
        const pos = positions[citation.id] ?? targets[citation.id] ?? { x: CELL / 2, y: CELL / 2 };
        return (
          <button
            key={citation.id}
            type="button"
            data-citation-id={citation.id}
            id={`heatmap-citation-${citation.id}`}
            onClick={() => onSelect(citation)}
            className={`${citationCardClass(citation)} absolute text-left transition-[box-shadow,transform] hover:scale-[1.03] ${
              selectedId === citation.id ? "z-10 ring-2 ring-[#86efac]" : "z-0"
            }`}
            style={{
              width: CARD_W,
              height: CARD_H,
              left: pos.x,
              top: pos.y,
              transform: "translate(-50%, -50%)",
              backgroundColor: citationFill(citation),
            }}
          >
            {citation.quantitative_claim && (
              <span
                className="absolute right-1 top-1 rounded bg-white/25 px-1 font-audit text-[8px] font-bold leading-tight text-white"
                title="Quantitative claim detected — NLI may not detect numerical discrepancies"
              >
                #±
              </span>
            )}
            <p className="font-audit text-xs opacity-80">#{citation.index}</p>
            <p className="truncate text-sm font-semibold">
              {citation.bibliography.authors[0] ?? "Unknown"}
            </p>
            <p className="text-xs opacity-80">{citation.bibliography.year ?? "—"}</p>
            <p className="mt-1 font-audit text-[9px] font-semibold uppercase tracking-wide opacity-90">
              {verdictBadgeLabel(citation)}
            </p>
          </button>
        );
      })}
    </div>
  );
}
