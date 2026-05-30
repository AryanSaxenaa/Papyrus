import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";
import { verdictBadgeLabel } from "../lib/verdictLabel";
import { citationFill } from "../lib/verdictColors";
import type { AuditRun, CitationRecord, StreamEvent } from "../types";

type Props = {
  events: StreamEvent[];
  audit: AuditRun | null;
};

const EVENT_TYPES = ["all", "crossref", "nli", "claim", "verdict", "version", "bulk", "error"] as const;

export function LivePanel({ events, audit }: Props) {
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState<string>("all");

  const filteredEvents = useMemo(() => {
    let list = events;
    if (eventType !== "all") {
      list = list.filter((event) => event.type === eventType);
    }
    const query = search.trim();
    if (!query) return list;
    const asNum = Number(query);
    return list.filter((event) => {
      if (!Number.isNaN(asNum) && event.citation_index === asNum) return true;
      return event.message.toLowerCase().includes(query.toLowerCase()) || event.type.includes(query);
    });
  }, [events, search, eventType]);

  const stackCitations = useMemo(() => {
    const citations = [...(audit?.citations ?? [])].sort((a, b) => a.index - b.index);
    return citations;
  }, [audit?.citations]);

  return (
    <div className="grid h-full gap-4 md:grid-cols-2">
      <div className="flex min-h-0 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className="font-audit text-xs uppercase tracking-wide text-[var(--papyrus-muted)]">Event log</h4>
          <div className="flex flex-wrap gap-1">
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="rounded border border-white/10 bg-black/30 px-2 py-1 font-audit text-xs"
            >
              {EVENT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Citation # or text"
              className="w-32 rounded border border-white/10 bg-black/30 px-2 py-1 font-audit text-xs"
            />
          </div>
        </div>
        <div className="mt-2 min-h-0 flex-1 space-y-2 overflow-y-auto font-audit text-xs leading-relaxed">
          {filteredEvents.map((event, index) => (
            <div key={`${event.ts}-${index}`} className="border-b border-white/5 pb-2">
              <span className="text-[var(--papyrus-muted)]">{event.ts.slice(11, 19)}</span>{" "}
              {typeof event.citation_index === "number" && (
                <span className="text-stone-400">#{event.citation_index} </span>
              )}
              <span className="text-emerald-300">{event.type}</span> {event.message}
            </div>
          ))}
          {!filteredEvents.length && (
            <p className="text-[var(--papyrus-muted)]">
              {search ? "No events match this citation index." : "Resolution events stream here during analysis."}
            </p>
          )}
        </div>
      </div>

      <CitationStack citations={stackCitations} />
    </div>
  );
}

function CitationStack({ citations }: { citations: CitationRecord[] }) {
  const stackRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!stackRef.current) return;
    d3.select(stackRef.current)
      .selectAll<HTMLDivElement, CitationRecord>("div[data-stack-id]")
      .data(citations, (d) => d.id)
      .transition()
      .duration(500)
      .style("background-color", (d) => citationFill(d));
  }, [citations]);

  return (
    <div className="flex min-h-0 flex-col">
      <h4 className="font-audit text-xs uppercase tracking-wide text-[var(--papyrus-muted)]">Citation stack</h4>
      <div ref={stackRef} className="mt-2 min-h-0 flex-1 space-y-2 overflow-y-auto">
        {citations.map((citation, index) => (
          <div
            key={citation.id}
            data-stack-id={citation.id}
            className="animate-[fadeSlide_0.45s_ease-out_both] rounded-md border border-white/10 p-2"
            style={{ animationDelay: `${index * 40}ms`, backgroundColor: citationFill(citation) }}
          >
            <p className="font-audit text-xs text-[var(--papyrus-muted)]">#{citation.index}</p>
            <p className="truncate text-sm font-semibold">
              {citation.bibliography.authors[0] ?? "Unknown"} · {citation.bibliography.year ?? "—"}
            </p>
            <p className="mt-1 truncate text-xs opacity-80">
              {citation.bibliography.title ?? citation.bibliography.raw}
            </p>
            <p className="mt-1 font-audit text-[9px] uppercase opacity-90">{verdictBadgeLabel(citation)}</p>
          </div>
        ))}
        {!citations.length && (
          <p className="text-xs text-[var(--papyrus-muted)]">Citations appear here as the audit runs.</p>
        )}
      </div>
    </div>
  );
}
