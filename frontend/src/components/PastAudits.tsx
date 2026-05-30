import { useCallback, useEffect, useState, type MouseEvent } from "react";



type Summary = {

  id: string;

  paper_title?: string | null;

  status: string;

  coverage_percent: number;

  failure_rate: number;

  risk_level: string;

  citation_count: number;

};



type Props = {

  onSelect: (auditId: string) => void;

  refreshKey?: number;

  activeAuditId?: string | null;

  onDeleted?: (auditId: string) => void;

};



export function PastAudits({ onSelect, refreshKey = 0, activeAuditId, onDeleted }: Props) {

  const [summaries, setSummaries] = useState<Summary[]>([]);

  const [open, setOpen] = useState(false);

  const [deletingId, setDeletingId] = useState<string | null>(null);



  const load = useCallback(() => {

    void fetch("/api/audits/summaries")

      .then((response) => (response.ok ? response.json() : []))

      .then((data) => setSummaries((data as Summary[]).slice(0, 20)))

      .catch(() => setSummaries([]));

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

    <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">

      <button

        type="button"

        onClick={() => setOpen((value) => !value)}

        className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]"

      >

        Past audits {open ? "▾" : "▸"} ({summaries.length})

      </button>

      {open && (

        <ul className="mt-3 max-h-48 space-y-1 overflow-y-auto text-sm">

          {summaries.map((row) => (

            <li key={row.id}>

              <div

                className={`flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 ${

                  activeAuditId === row.id ? "bg-emerald-950/40 ring-1 ring-emerald-800/50" : "hover:bg-white/5"

                }`}

              >

                <button

                  type="button"

                  onClick={() => onSelect(row.id)}

                  className="min-w-0 flex-1 text-left"

                >

                  <span className="block truncate">{row.paper_title ?? row.id.slice(0, 8)}</span>

                  <span className="font-audit text-xs text-stone-400">

                    {row.coverage_percent}% · {row.risk_level} · {row.status}

                  </span>

                </button>

                <button

                  type="button"

                  disabled={deletingId === row.id}

                  onClick={(event) => void onDelete(row.id, event)}

                  className="shrink-0 rounded border border-red-900/50 px-2 py-0.5 font-audit text-[10px] uppercase text-red-300 hover:bg-red-950/40 disabled:opacity-40"

                  title="Delete audit"

                >

                  {deletingId === row.id ? "…" : "Del"}

                </button>

              </div>

            </li>

          ))}

        </ul>

      )}

    </div>

  );

}

