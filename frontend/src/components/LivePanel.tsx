import { useMemo, useState } from "react";
import type { AuditRun, CitationRecord, StreamEvent } from "../types";

const verdictClass: Record<string, string> = {
  supported: "border-emerald-800/50 bg-emerald-950/30",
  failure: "border-red-900/50 bg-red-950/30",
  cannot_assess: "border-slate-700/50 bg-slate-900/40",
  resolving: "border-amber-700/50 bg-amber-950/30",
  pending: "border-white/10 bg-black/20",
};

type Props = {
  events: StreamEvent[];
  audit: AuditRun | null;
};

const EVENT_TYPES = ["all", "crossref", "nli", "claim", "verdict", "version", "circular", "bulk", "error"] as const;

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

  const resolving = useMemo(() => {
    const citations = audit?.citations ?? [];
    return citations.filter(
      (c) => c.status === "resolving" || c.verdict_color === "resolving" || c.status === "pending",
    );
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

      <div className="flex min-h-0 flex-col">
        <h4 className="font-audit text-xs uppercase tracking-wide text-[var(--papyrus-muted)]">Resolving stack</h4>
        <div className="mt-2 min-h-0 flex-1 space-y-2 overflow-y-auto">
          {resolving.map((citation, index) => (
            <ResolvingCard key={citation.id} citation={citation} delayMs={index * 120} />
          ))}
          {!resolving.length && (
            <p className="text-xs text-[var(--papyrus-muted)]">No citations actively resolving.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ResolvingCard({ citation, delayMs }: { citation: CitationRecord; delayMs: number }) {
  return (
    <div
      className={`animate-[fadeSlide_0.45s_ease-out_both] rounded-md border p-2 ${verdictClass[citation.verdict_color] ?? verdictClass.pending}`}
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <p className="font-audit text-xs text-[var(--papyrus-muted)]">#{citation.index}</p>
      <p className="truncate text-sm font-semibold">
        {citation.bibliography.authors[0] ?? "Unknown"} · {citation.bibliography.year ?? "—"}
      </p>
      <p className="mt-1 truncate text-xs opacity-80">{citation.bibliography.title ?? citation.bibliography.raw}</p>
    </div>
  );
}
