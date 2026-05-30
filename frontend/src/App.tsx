import { useCallback, useEffect, useMemo, useState } from "react";
import type { AuditRun, BulkDashboard, CitationRecord, HeatmapFilter, StreamEvent } from "./types";

const verdictClass: Record<string, string> = {
  supported: "bg-[var(--papyrus-green)]",
  failure: "bg-[var(--papyrus-crimson)]",
  retraction: "bg-[var(--papyrus-crimson)] ring-2 ring-amber-400",
  cannot_assess: "bg-[var(--papyrus-steel)]",
  neutral: "bg-[var(--papyrus-grey)]",
  unresolvable: "bg-[#4a524e]",
  resolving: "bg-[var(--papyrus-amber)] animate-pulse",
  pending: "bg-[#2a312e]",
  amber: "bg-[var(--papyrus-amber)]",
};

const INTENT_OPTIONS = ["evidentiary", "methodological", "contrastive", "background"];

function highlightCitations(text: string, citations: CitationRecord[]) {
  const colors: Record<string, string> = {
    supported: "#1f6b4a",
    failure: "#8b1e2f",
    retraction: "#8b1e2f",
    cannot_assess: "#3d5a73",
    neutral: "#5c6460",
    unresolvable: "#4a524e",
    resolving: "#b8860b",
    pending: "#2a312e",
    amber: "#b8860b",
  };
  let html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  for (const citation of citations) {
    for (const marker of [citation.bibliography.doi, `[${citation.index}]`]) {
      if (!marker) continue;
      const color = colors[citation.verdict_color] ?? colors.pending;
      html = html.replaceAll(
        marker,
        `<mark style="background:${color};color:#fff;border-radius:2px;padding:0 2px">${marker}</mark>`,
      );
    }
  }
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export default function App() {
  const [audit, setAudit] = useState<AuditRun | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [selected, setSelected] = useState<CitationRecord | null>(null);
  const [uploading, setUploading] = useState(false);
  const [doiInput, setDoiInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [bulkStatus, setBulkStatus] = useState<string | null>(null);
  const [bulkDashboard, setBulkDashboard] = useState<BulkDashboard | null>(null);
  const [showAnatomy, setShowAnatomy] = useState(false);
  const [filter, setFilter] = useState<HeatmapFilter>("all");
  const [claimDraft, setClaimDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  const refreshAudit = useCallback(async (id: string) => {
    const response = await fetch(`/api/audits/${id}`);
    if (!response.ok) return;
    const next = (await response.json()) as AuditRun;
    setAudit(next);
    if (selected) {
      const updated = next.citations.find((c) => c.id === selected.id);
      if (updated) setSelected(updated);
    }
  }, [selected]);

  useEffect(() => {
    if (!audit?.id || audit.status === "complete" || audit.status === "failed") return;
    const timer = window.setInterval(() => refreshAudit(audit.id), 2500);
    return () => window.clearInterval(timer);
  }, [audit?.id, audit?.status, refreshAudit]);

  useEffect(() => {
    if (!audit?.id) return;
    const source = new EventSource(`/api/audits/${audit.id}/events`);
    source.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as StreamEvent;
        setEvents((prev) => [...prev, payload]);
      } catch {
        // ignore malformed chunks
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [audit?.id]);

  useEffect(() => {
    if (!selected) return;
    setClaimDraft(selected.claim_user_corrected ?? selected.extracted_claim ?? "");
  }, [selected]);

  const startAudit = async (response: Response) => {
    if (!response.ok) throw new Error(await response.text());
    const created = (await response.json()) as AuditRun;
    setAudit(created);
  };

  const onUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      const body = new FormData();
      body.append("file", file);
      await startAudit(await fetch("/api/audits", { method: "POST", body }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onAuditUrl = async () => {
    if (!urlInput.trim()) return;
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      await startAudit(
        await fetch("/api/audits/url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: urlInput.trim() }),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "URL audit failed");
    } finally {
      setUploading(false);
    }
  };

  const onBulkUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setBulkStatus(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/audits/bulk", { method: "POST", body });
      if (!response.ok) throw new Error(await response.text());
      const job = (await response.json()) as { id: string; total: number };
      setBulkStatus(`Bulk job ${job.id} queued (${job.total} papers)`);
      const poll = window.setInterval(async () => {
        const statusRes = await fetch(`/api/bulk/${job.id}`);
        if (!statusRes.ok) return;
        const status = (await statusRes.json()) as {
          status: string;
          completed: number;
          failed: number;
          total: number;
        };
        setBulkStatus(
          `Bulk: ${status.completed}/${status.total} complete, ${status.failed} failed (${status.status})`,
        );
        if (status.status === "complete" || status.status === "failed") {
          window.clearInterval(poll);
          setUploading(false);
          const dashRes = await fetch(`/api/bulk/${job.id}/dashboard`);
          if (dashRes.ok) setBulkDashboard((await dashRes.json()) as BulkDashboard);
        }
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk upload failed");
      setUploading(false);
    }
  };

  const onVerifyDoi = async () => {
    if (!doiInput.trim()) return;
    setUploading(true);
    setError(null);
    setEvents([]);
    setSelected(null);
    try {
      await startAudit(
        await fetch("/api/audits/doi", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doi: doiInput.trim() }),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "DOI verification failed");
    } finally {
      setUploading(false);
    }
  };

  const saveIntent = async (intent: string) => {
    if (!audit || !selected) return;
    const response = await fetch(`/api/audits/${audit.id}/citations/${selected.id}/intent`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent }),
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const saveClaim = async () => {
    if (!audit || !selected || !claimDraft.trim()) return;
    const response = await fetch(`/api/audits/${audit.id}/citations/${selected.id}/claim`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ claim: claimDraft.trim() }),
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const filteredCitations = useMemo(() => {
    const citations = audit?.citations ?? [];
    if (filter === "all") return citations;
    if (filter === "failures") {
      return citations.filter(
        (c) => c.verdict_color === "failure" || c.hallucination_type.includes("type_"),
      );
    }
    if (filter === "unresolvable") return citations.filter((c) => c.verdict_color === "unresolvable");
    return citations.filter(
      (c) => c.hallucination_type === "retraction" || c.verdict_color === "retraction",
    );
  }, [audit?.citations, filter]);

  const coverageBar = useMemo(() => {
    if (!audit) return null;
    const { coverage } = audit;
    const total = coverage.total || 1;
    const segments = [
      { label: "Tier 1", value: coverage.tier_1, color: "bg-emerald-700" },
      { label: "Tier 2", value: coverage.tier_2, color: "bg-emerald-900" },
      { label: "Tier 3", value: coverage.tier_3, color: "bg-slate-600" },
      { label: "Unresolvable", value: coverage.tier_4, color: "bg-stone-600" },
    ];
    return (
      <div className="flex h-3 overflow-hidden rounded-full border border-white/10">
        {segments.map((segment) => (
          <div
            key={segment.label}
            className={segment.color}
            style={{ width: `${(segment.value / total) * 100}%` }}
            title={`${segment.label}: ${segment.value}`}
          />
        ))}
      </div>
    );
  }, [audit]);

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-[var(--papyrus-panel)] px-6 py-5">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-audit text-xs uppercase tracking-[0.2em] text-[var(--papyrus-muted)]">
              Citation integrity audit
            </p>
            <h1 className="text-3xl font-semibold tracking-tight">Papyrus</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--papyrus-muted)]">
              Verifies whether references exist and whether evidentiary citations are supported.
              Does not detect AI authorship.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={doiInput}
              onChange={(e) => setDoiInput(e.target.value)}
              placeholder="10.1038/..."
              className="rounded-md border border-white/15 bg-black/30 px-3 py-2 font-audit text-sm"
            />
            <input
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://arxiv.org/abs/..."
              className="rounded-md border border-white/15 bg-black/30 px-3 py-2 font-audit text-sm min-w-[200px]"
            />
            <button
              type="button"
              disabled={uploading}
              onClick={() => void onAuditUrl()}
              className="rounded-md border border-stone-600 bg-stone-900/60 px-4 py-2 text-sm font-semibold hover:bg-stone-800/80"
            >
              Audit URL
            </button>
            <button
              type="button"
              disabled={uploading}
              onClick={() => void onVerifyDoi()}
              className="rounded-md border border-stone-600 bg-stone-900/60 px-4 py-2 text-sm font-semibold hover:bg-stone-800/80"
            >
              Verify DOI
            </button>
            <label className="cursor-pointer rounded-md border border-amber-800/60 bg-amber-950/30 px-4 py-2 text-sm font-semibold hover:bg-amber-900/40">
              Bulk ZIP
              <input
                type="file"
                accept="application/zip"
                className="hidden"
                disabled={uploading}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void onBulkUpload(file);
                }}
              />
            </label>
            <label className="cursor-pointer rounded-md border border-emerald-700/60 bg-emerald-950/40 px-4 py-2 text-sm font-semibold hover:bg-emerald-900/50">
              {uploading ? "Working…" : "Upload PDF"}
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                disabled={uploading}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void onUpload(file);
                }}
              />
            </label>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-4">
          {error && (
            <p className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          )}
          {bulkStatus && (
            <p className="rounded-md border border-amber-800/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
              {bulkStatus}
            </p>
          )}

          {bulkDashboard && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
                Bulk analysis dashboard
              </h3>
              <p className="mt-1 text-xs text-[var(--papyrus-muted)]">{bulkDashboard.note}</p>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-[var(--papyrus-muted)]">
                    <tr>
                      <th className="py-1 pr-3">Paper</th>
                      <th className="py-1 pr-3">Coverage</th>
                      <th className="py-1 pr-3">Failure rate</th>
                      <th className="py-1">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkDashboard.papers.map((paper) => (
                      <tr
                        key={paper.audit_id}
                        className="cursor-pointer border-t border-white/5 hover:bg-white/5"
                        onClick={() => {
                          void fetch(`/api/audits/${paper.audit_id}`)
                            .then((response) => response.json())
                            .then((data) => setAudit(data as AuditRun));
                        }}
                      >
                        <td className="py-2 pr-3">{paper.title ?? paper.audit_id.slice(0, 8)}</td>
                        <td className="py-2 pr-3 font-audit">{paper.coverage_percent}%</td>
                        <td className="py-2 pr-3 font-audit">{paper.confirmed_failure_rate}%</td>
                        <td className="py-2 font-audit uppercase">{paper.risk_level}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {audit && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{audit.paper_title ?? "Analyzing document…"}</h2>
                  <p className="font-audit text-xs text-[var(--papyrus-muted)]">
                    Status: {audit.status} · Pipeline {audit.pipeline_version}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-audit text-3xl font-semibold text-emerald-300">
                    {audit.coverage.coverage_percent}%
                  </p>
                  <p className="text-xs text-[var(--papyrus-muted)]">Coverage</p>
                  <p className="mt-2 font-audit text-sm uppercase text-amber-300">{audit.risk_level} risk</p>
                </div>
              </div>
              <div className="mt-4">{coverageBar}</div>
              {audit.status === "complete" && (
                <div className="mt-3 flex gap-3 text-sm">
                  <a className="text-emerald-300 underline" href={`/api/audits/${audit.id}/report.txt`}>
                    Export TXT
                  </a>
                  <a className="text-emerald-300 underline" href={`/api/audits/${audit.id}/report.json`}>
                    Export JSON
                  </a>
                  <a className="text-emerald-300 underline" href={`/api/audits/${audit.id}/report.pdf`}>
                    Export PDF
                  </a>
                </div>
              )}
            </div>
          )}

          <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
                Citation heatmap
              </h3>
              <div className="flex flex-wrap gap-1 text-xs">
                {(["all", "failures", "unresolvable", "retracted"] as HeatmapFilter[]).map((key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setFilter(key)}
                    className={`rounded px-2 py-1 ${filter === key ? "bg-emerald-900/70" : "bg-black/30"}`}
                  >
                    {key}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
              {filteredCitations.map((citation) => (
                <button
                  key={citation.id}
                  type="button"
                  onClick={() => setSelected(citation)}
                  className={`rounded-md border border-white/10 p-2 text-left transition hover:scale-[1.02] ${
                    verdictClass[citation.verdict_color] ?? verdictClass.pending
                  }`}
                >
                  <p className="font-audit text-xs opacity-80">#{citation.index}</p>
                  <p className="truncate text-sm font-semibold">
                    {citation.bibliography.authors[0] ?? "Unknown"}
                  </p>
                  <p className="text-xs opacity-80">{citation.bibliography.year ?? "—"}</p>
                </button>
              ))}
              {!filteredCitations.length && (
                <p className="col-span-full text-sm text-[var(--papyrus-muted)]">
                  No citations match this filter.
                </p>
              )}
            </div>
          </div>

          {audit?.paper_text && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <button
                type="button"
                className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]"
                onClick={() => setShowAnatomy((value) => !value)}
              >
                Paper anatomy view {showAnatomy ? "▾" : "▸"}
              </button>
              {showAnatomy && (
                <div className="mt-3 max-h-64 overflow-y-auto text-sm leading-relaxed text-stone-200">
                  {highlightCitations(audit.paper_text, audit.citations)}
                </div>
              )}
            </div>
          )}

          {selected && audit && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
                Citation #{selected.index}
              </h3>
              <p className="mt-2 text-sm">{selected.bibliography.title ?? selected.bibliography.raw.slice(0, 240)}</p>

              <label className="mt-3 block text-xs text-[var(--papyrus-muted)]">
                Intent
                <select
                  className="mt-1 w-full rounded border border-white/15 bg-black/30 px-2 py-1 font-audit text-sm"
                  value={selected.intent}
                  onChange={(e) => void saveIntent(e.target.value)}
                >
                  {INTENT_OPTIONS.map((intent) => (
                    <option key={intent} value={intent}>
                      {intent}
                    </option>
                  ))}
                </select>
              </label>

              <label className="mt-3 block text-xs text-[var(--papyrus-muted)]">
                Extracted claim
                <textarea
                  className="mt-1 w-full rounded border border-white/15 bg-black/30 px-2 py-1 font-audit text-sm"
                  rows={3}
                  value={claimDraft}
                  onChange={(e) => setClaimDraft(e.target.value)}
                />
              </label>
              <button
                type="button"
                onClick={() => void saveClaim()}
                className="mt-2 rounded border border-emerald-700/50 px-3 py-1 text-xs font-semibold text-emerald-200"
              >
                Rerun alignment
              </button>

              {selected.evidence_passage && (
                <p className="mt-3 rounded border border-white/10 bg-black/20 p-2 text-xs leading-relaxed">
                  {selected.evidence_passage.slice(0, 500)}
                </p>
              )}

              {selected.exa_signal && (
                <p className="mt-2 text-xs text-stone-300">{selected.exa_signal}</p>
              )}

              {selected.source_verify_url && (
                <a
                  href={selected.source_verify_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-sm text-emerald-300 underline"
                >
                  Verify source
                </a>
              )}

              {selected.quantitative_caveat && (
                <p className="mt-3 rounded border border-amber-700/40 bg-amber-950/30 p-2 text-xs text-amber-100">
                  {selected.quantitative_caveat}
                </p>
              )}
            </div>
          )}
        </section>

        <section className="rounded-xl border border-white/10 bg-[#0c100e] p-4">
          <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
            Live resolution panel
          </h3>
          <div className="mt-3 max-h-[70vh] space-y-2 overflow-y-auto font-audit text-xs leading-relaxed">
            {events.map((event, index) => (
              <div key={`${event.ts}-${index}`} className="border-b border-white/5 pb-2">
                <span className="text-[var(--papyrus-muted)]">{event.ts.slice(11, 19)}</span>{" "}
                <span className="text-emerald-300">{event.type}</span> {event.message}
              </div>
            ))}
            {!events.length && (
              <p className="text-[var(--papyrus-muted)]">Resolution events will stream here during analysis.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
