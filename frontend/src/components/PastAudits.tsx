import { useCallback, useEffect, useState, type MouseEvent } from "react";
import type { AuditSummary } from "../types";

type Props = {
  onSelect: (auditId: string) => void;
  refreshKey?: number;
  activeAuditId?: string | null;
  onDeleted?: (auditId: string) => void;
  embedded?: boolean;
};

export function PastAudits({
  onSelect,
  refreshKey = 0,
  activeAuditId,
  onDeleted,
  embedded = false,
}: Props) {
  const [summaries, setSummaries] = useState<AuditSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(() => {
    void fetch("/api/audits/summaries")
      .then((response) => (response.ok ? response.json() : []))
      .then((data) => setSummaries((data as AuditSummary[]).slice(0, 20)))
      .catch((err: unknown) => {
        console.warn("Failed to load audit summaries", err);
        setSummaries([]);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const onDelete = async (auditId: string, event: MouseEvent) => {
    event.stopPropagation();
    if (!window.confirm("Delete this audit and its indexed records?")) return;
    setDeletingId(auditId);
    try {
      const response = await fetch(`/api/audits/${auditId}`, { method: "DELETE" });
      if (response.ok || response.status === 204) {
        setSummaries((rows) => rows.filter((row) => row.id !== auditId));
        onDeleted?.(auditId);
      }
    } finally {
      setDeletingId(null);
    }
  };

  if (!summaries.length) return null;

  return (
    <div className={embedded ? "w-full" : "papyrus-card"}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`flex items-center gap-1.5 text-sm font-semibold text-zinc-800 hover:text-[#1a3d32] transition-colors ${
          embedded ? "w-full" : ""
        }`}
      >
        <span className="font-audit text-xs">{open ? "▾" : "▸"}</span>
        Past audits
        <span className="font-audit text-xs text-zinc-400">({summaries.length})</span>
      </button>

      {open && (
        <ul className="mt-3 max-h-48 space-y-1 overflow-y-auto papyrus-scroll-hidden">
          {summaries.map((row) => (
            <li key={row.id}>
              <div
                className={`flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 transition-colors ${
                  activeAuditId === row.id
                    ? "bg-[#ecfdf3] ring-1 ring-[#bbf7d0]"
                    : "hover:bg-zinc-50"
                }`}
              >
                <button
                  type="button"
                  onClick={() => onSelect(row.id)}
                  className="min-w-0 flex-1 text-left"
                >
                  <span className="block truncate text-sm text-zinc-800">
                    {row.paper_title ?? row.id.slice(0, 8)}
                  </span>
                  <span className="font-audit text-xs text-zinc-400">
                    {row.coverage_percent}% · {row.risk_level} · {row.status}
                  </span>
                </button>
                <button
                  type="button"
                  disabled={deletingId === row.id}
                  onClick={(event) => void onDelete(row.id, event)}
                  className="shrink-0 rounded border border-red-200 px-2 py-0.5 font-audit text-[10px] uppercase text-red-500 hover:bg-red-50 hover:border-red-300 transition-colors disabled:opacity-40"
                  title="Delete audit"
                >
                  {deletingId === row.id ? "..." : "Del"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
