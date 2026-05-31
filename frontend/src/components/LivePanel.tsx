import { useMemo, useState } from "react";
import { apiUrl } from "../lib/api";
import type { AuditRun, CitationRecord, StreamEvent } from "../types";
import { citationCardClass, citationFill } from "../lib/verdictColors";
import { verdictBadgeLabel } from "../lib/verdictLabel";

type Props = {
  events: StreamEvent[];
  audit: AuditRun | null;
  citations?: CitationRecord[];
  onSelect?: (citation: CitationRecord) => void;
  auditId?: string;
};

const EVENT_TYPES = ["all", "crossref", "nli", "claim", "verdict", "version", "bulk", "error"] as const;

export function LivePanel({ events, audit, citations, onSelect, auditId }: Props) {
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

  const running = audit && audit.status !== "complete" && audit.status !== "failed";

  const resolvedCitations = useMemo(() => {
    if (!citations) return [];
    return citations
      .filter((c) => c.verdict_color !== "pending")
      .slice(-24);
  }, [citations]);

  return (
    <div className="grid min-h-0 grid-cols-1 gap-4 lg:grid-cols-[1fr_auto]">
      <div className="flex min-h-0 flex-col">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-zinc-500">
            {running ? "Pipeline events stream while the audit runs." : "Resolution events from this audit."}
          </p>
          <div className="flex flex-wrap items-center gap-1">
            {auditId && (
              <a
                className="papyrus-link py-1 font-audit text-xs"
                href={apiUrl(`/api/audits/${auditId}/events/log.txt`)}
                download
              >
                Download log
              </a>
            )}
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="papyrus-input py-1 font-audit text-xs"
              aria-label="Event type"
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
              className="papyrus-input w-36 py-1 font-audit text-xs"
              aria-label="Filter events"
            />
          </div>
        </div>
        <div className="mt-2 max-h-64 min-h-[8rem] space-y-1.5 overflow-y-auto papyrus-scroll-hidden font-audit text-xs leading-relaxed">
          {filteredEvents.map((event, index) => (
            <div key={`${event.ts}-${index}`} className="border-b border-zinc-100 pb-1.5">
              <span className="text-zinc-400">{event.ts.slice(11, 19)}</span>{" "}
              {typeof event.citation_index === "number" && (
                <span className="text-zinc-500">#{event.citation_index} </span>
              )}
              <span className="font-medium text-[#2d6a4f]">{event.type}</span>{" "}
              <span className="text-zinc-700">{event.message}</span>
            </div>
          ))}
          {!filteredEvents.length && (
            <p className="text-zinc-400">
              {search
                ? "No events match this filter."
                : "Events will appear here once analysis starts."}
            </p>
          )}
        </div>
      </div>

      <div className="w-56 shrink-0 lg:border-l lg:border-zinc-200 lg:pl-4">
        <p className="mb-2 font-audit text-[10px] uppercase tracking-wide text-zinc-400">
          Live citations
        </p>
        <div className="space-y-1.5 max-h-64 overflow-y-auto papyrus-scroll-hidden">
          {resolvedCitations.length > 0 ? (
            resolvedCitations.map((citation) => (
              <button
                key={citation.id}
                type="button"
                onClick={() => onSelect?.(citation)}
                className={`${citationCardClass(citation)} relative w-full text-left text-[10px] leading-tight transition hover:scale-[1.02]`}
                style={{ backgroundColor: citationFill(citation) }}
              >
                {citation.quantitative_claim && (
                  <span
                    className="absolute right-1 top-1 rounded bg-white/25 px-0.5 font-audit text-[7px] font-bold text-white"
                    title="Quantitative claim"
                  >
                    #±
                  </span>
                )}
                <span className="font-audit opacity-80">#{citation.index}</span>{" "}
                <span className="font-semibold">{citation.bibliography.authors[0] ?? "?"}</span>
                <span className="ml-1 opacity-70">{citation.bibliography.year ?? "—"}</span>
                <span className="ml-auto block font-audit text-[8px] uppercase tracking-wide opacity-90">
                  {verdictBadgeLabel(citation)}
                </span>
              </button>
            ))
          ) : (
            <p className="text-xs text-zinc-400">Waiting for citations to resolve...</p>
          )}
        </div>
      </div>
    </div>
  );
}
