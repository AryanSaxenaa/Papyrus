import { useMemo, useState } from "react";
import type { AuditRun, StreamEvent } from "../types";

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

  const running = audit && audit.status !== "complete" && audit.status !== "failed";

  return (
    <div className="flex min-h-0 flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-zinc-500">
          {running ? "Pipeline events stream while the audit runs." : "Resolution events from this audit."}
        </p>
        <div className="flex flex-wrap gap-1">
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
  );
}
