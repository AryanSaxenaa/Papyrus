import { useEffect, useState } from "react";



type AuditFailureRow = {

  audit_id: string;

  total: number;

  failures: number;

  failure_rate: number;

};



export function CitationAnalytics() {

  const [rows, setRows] = useState<AuditFailureRow[]>([]);

  const [open, setOpen] = useState(false);



  useEffect(() => {

    void fetch("/api/admin/citations/stats")

      .then((response) => (response.ok ? response.json() : null))

      .then((data) => {

        const ranked = (data?.audits_by_failure_rate ?? []) as AuditFailureRow[];

        setRows(ranked.filter((row) => row.total > 0).slice(0, 8));

      })

      .catch(() => setRows([]));

  }, []);



  if (!rows.length) return null;



  return (

    <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">

      <button

        type="button"

        onClick={() => setOpen((value) => !value)}

        className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]"

      >

        Cross-audit failure rates {open ? "▾" : "▸"}

      </button>

      {open && (

        <ul className="mt-3 space-y-1 font-audit text-xs text-stone-300">

          {rows.map((row) => (

            <li key={row.audit_id} className="flex justify-between gap-2 border-b border-white/5 py-1">

              <span className="truncate text-stone-400">{row.audit_id.slice(0, 8)}</span>

              <span>

                {row.failure_rate}% <span className="text-stone-500">({row.failures}/{row.total})</span>

              </span>

            </li>

          ))}

        </ul>

      )}

      <p className="mt-2 text-[10px] text-[var(--papyrus-muted)]">

        Resolvable citations only; requires Postgres citation index.

      </p>

    </div>

  );

}

