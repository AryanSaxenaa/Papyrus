import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { CoverageBar } from "./components/CoverageBar";
import { CoverageSummary } from "./components/CoverageSummary";
import { HeatmapLegend } from "./components/HeatmapLegend";
import { LivePanel } from "./components/LivePanel";
import { LimitationsPanel } from "./components/LimitationsPanel";
import { CitationHeatmap } from "./components/CitationHeatmap";
import { HeatmapFilterBar } from "./components/HeatmapFilterBar";
import { PaperAnatomy } from "./components/PaperAnatomy";
import { AdminPanel } from "./components/AdminPanel";
import { PastAudits } from "./components/PastAudits";
import { SideBySideDrawer } from "./components/SideBySideDrawer";
import type { AuditRun, BulkDashboard, CitationRecord, HeatmapFilter, StreamEvent } from "./types";

export default function App() {
  const [audit, setAudit] = useState<AuditRun | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [selected, setSelected] = useState<CitationRecord | null>(null);
  const [uploading, setUploading] = useState(false);
  const [doiInput, setDoiInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [bulkStatus, setBulkStatus] = useState<string | null>(null);
  const [bulkJobId, setBulkJobId] = useState<string | null>(null);
  const [bulkEvents, setBulkEvents] = useState<StreamEvent[]>([]);
  const [bulkDashboard, setBulkDashboard] = useState<BulkDashboard | null>(null);
  const [showAnatomy, setShowAnatomy] = useState(false);
  const [filter, setFilter] = useState<HeatmapFilter>("all");
  const [claimDraft, setClaimDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expandedBulkId, setExpandedBulkId] = useState<string | null>(null);
  const [bulkAuditCache, setBulkAuditCache] = useState<Record<string, AuditRun>>({});
  const [auditsListKey, setAuditsListKey] = useState(0);

  const refreshAudit = useCallback(async (id: string) => {
    const response = await fetch(`/api/audits/${id}`);
    if (!response.ok) return;
    const next = (await response.json()) as AuditRun;
    setAudit(next);
    setEvents([]);
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
    if (!bulkJobId) return;
    const source = new EventSource(`/api/bulk/${bulkJobId}/events`);
    source.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as StreamEvent;
        setBulkEvents((prev) => [...prev.slice(-80), payload]);
      } catch {
        // ignore malformed chunks
      }
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [bulkJobId]);

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
    document.getElementById(`heatmap-citation-${selected.id}`)?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [selected]);

  const startAudit = async (response: Response) => {
    if (!response.ok) throw new Error(await response.text());
    const created = (await response.json()) as AuditRun;
    setAudit(created);
    setAuditsListKey((key) => key + 1);
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
      setBulkJobId(job.id);
      setBulkEvents([]);
      setBulkDashboard(null);
      setBulkStatus(`Bulk job ${job.id} queued (${job.total} papers)`);
      const poll = window.setInterval(async () => {
        const statusRes = await fetch(`/api/bulk/${job.id}`);
        if (!statusRes.ok) return;
        const status = (await statusRes.json()) as {
          status: string;
          completed: number;
          failed: number;
          total: number;
          estimated_seconds_remaining?: number | null;
        };
        const eta =
          status.estimated_seconds_remaining != null
            ? ` · ~${Math.ceil(status.estimated_seconds_remaining / 60)} min left`
            : "";
        setBulkStatus(
          `Bulk: ${status.completed}/${status.total} complete, ${status.failed} failed (${status.status})${eta}`,
        );
        if (status.status === "complete" || status.status === "failed") {
          window.clearInterval(poll);
          setUploading(false);
          setBulkJobId(null);
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

  const approveClaim = async () => {
    if (!audit || !selected) return;
    const response = await fetch(
      `/api/audits/${audit.id}/citations/${selected.id}/approve-claim`,
      { method: "POST" },
    );
    if (response.ok) await refreshAudit(audit.id);
  };

  const rerunCitation = async () => {
    if (!audit || !selected) return;
    const response = await fetch(`/api/audits/${audit.id}/citations/${selected.id}/rerun`, {
      method: "POST",
    });
    if (response.ok) await refreshAudit(audit.id);
  };

  const filteredCitations = useMemo(() => {
    const citations = audit?.citations ?? [];
    if (filter === "all") return citations;
    if (filter === "supported") {
      return citations.filter(
        (c) => c.claim_alignment_verdict === "supported" || c.verdict_color === "supported",
      );
    }
    if (filter === "contradictions") {
      return citations.filter(
        (c) =>
          c.hallucination_type === "type_7_claim_contradiction" ||
          c.claim_alignment_verdict === "claim_contradiction",
      );
    }
    if (filter === "cannot_assess") {
      return citations.filter(
        (c) => c.claim_alignment_verdict === "cannot_determine" || c.verdict_color === "cannot_assess",
      );
    }
    if (filter === "failures") {
      return citations.filter((c) => {
        if (c.verdict_color === "unresolvable" || c.evidence_tier === "tier_4") {
          return false;
        }
        return (
          c.verdict_color === "failure" ||
          (c.hallucination_type.startsWith("type_") && c.hallucination_type !== "retraction") ||
          c.claim_alignment_verdict === "claim_contradiction" ||
          c.claim_alignment_verdict === "not_addressed"
        );
      });
    }
    if (filter === "unresolvable") return citations.filter((c) => c.verdict_color === "unresolvable");
    return citations.filter(
      (c) => c.hallucination_type === "retraction" || c.verdict_color === "retraction",
    );
  }, [audit?.citations, filter]);

  const loadAuditById = async (auditId: string) => {
    const response = await fetch(`/api/audits/${auditId}`);
    if (!response.ok) return;
    setAudit((await response.json()) as AuditRun);
    setEvents([]);
    setSelected(null);
    setAuditsListKey((key) => key + 1);
  };

  const onAuditDeleted = (auditId: string) => {
    if (audit?.id === auditId) {
      setAudit(null);
      setEvents([]);
      setSelected(null);
    }
    setBulkAuditCache((prev) => {
      if (!(auditId in prev)) return prev;
      const next = { ...prev };
      delete next[auditId];
      return next;
    });
    setAuditsListKey((key) => key + 1);
  };

  const openBulkPaper = async (auditId: string) => {
    if (bulkAuditCache[auditId]) {
      setAudit(bulkAuditCache[auditId]);
      setExpandedBulkId(auditId);
      return;
    }
    const response = await fetch(`/api/audits/${auditId}`);
    if (!response.ok) return;
    const data = (await response.json()) as AuditRun;
    setBulkAuditCache((prev) => ({ ...prev, [auditId]: data }));
    setAudit(data);
    setExpandedBulkId(auditId);
    setShowAnatomy(true);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-[var(--papyrus-panel)] px-6 py-5">
        <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-audit text-xs uppercase tracking-[0.2em] text-[var(--papyrus-muted)]">
              Citation integrity audit
            </p>
            <h1 className="font-display text-3xl font-semibold tracking-tight">Papyrus</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--papyrus-muted)]">
              Verifies whether references exist and whether evidentiary citations are supported.
              Does not detect AI authorship.
            </p>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-xs text-emerald-300 underline"
            >
              API reference (OpenAPI)
            </a>
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
          <PastAudits
            refreshKey={auditsListKey}
            activeAuditId={audit?.id ?? null}
            onSelect={(id) => void loadAuditById(id)}
            onDeleted={onAuditDeleted}
          />
          <AdminPanel />

          {error && (
            <p className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          )}
          {bulkStatus && (
            <div className="rounded-md border border-amber-800/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-100">
              <p>{bulkStatus}</p>
              {bulkEvents.length > 0 && (
                <ul className="mt-2 max-h-24 overflow-y-auto font-audit text-[10px] leading-relaxed text-amber-100/80">
                  {bulkEvents.slice(-12).map((event, index) => (
                    <li key={`${event.ts}-${index}`}>
                      {event.ts.slice(11, 19)} {event.type}: {event.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {bulkDashboard && (
            <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
              <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
                Bulk analysis dashboard
              </h3>
              <p className="mt-1 text-xs text-[var(--papyrus-muted)]">{bulkDashboard.note}</p>
              <div className="mt-2 flex flex-wrap gap-3 text-xs">
                <a
                  className="text-emerald-300 underline"
                  href={`/api/bulk/${bulkDashboard.job.id}/dashboard.json`}
                >
                  Export dashboard JSON
                </a>
                <a
                  className="text-emerald-300 underline"
                  href={`/api/bulk/${bulkDashboard.job.id}/events/log.txt`}
                >
                  Bulk event log
                </a>
              </div>
              {(bulkDashboard.pending_papers ?? 0) > 0 && (
                <p className="mt-2 font-audit text-xs text-amber-200">
                  {bulkDashboard.pending_papers} paper(s) still resolving…
                  {bulkDashboard.job.estimated_seconds_remaining != null && (
                    <span className="text-stone-400">
                      {" "}
                      · ~{Math.ceil(bulkDashboard.job.estimated_seconds_remaining / 60)} min remaining
                    </span>
                  )}
                </p>
              )}
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-[var(--papyrus-muted)]">
                    <tr>
                      <th className="py-1 pr-3">Paper</th>
                      <th className="py-1 pr-3">First author</th>
                      <th className="py-1 pr-3">Coverage</th>
                      <th className="py-1 pr-3">Failure rate</th>
                      <th className="py-1 pr-3">T1 / T7 / Ret</th>
                      <th className="py-1">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkDashboard.papers.map((paper) => {
                      const cached = bulkAuditCache[paper.audit_id];
                      const isExpanded = expandedBulkId === paper.audit_id;
                      return (
                        <Fragment key={paper.audit_id}>
                          <tr
                            className="cursor-pointer border-t border-white/5 hover:bg-white/5"
                            onClick={() => void openBulkPaper(paper.audit_id)}
                          >
                            <td className="py-2 pr-3">
                              {paper.title ?? paper.audit_id.slice(0, 8)}
                              {isExpanded && (
                                <span className="ml-2 font-audit text-[10px] text-emerald-400">expanded</span>
                              )}
                            </td>
                            <td className="py-2 pr-3 text-stone-400">
                              {paper.first_author ?? "—"}
                            </td>
                            <td className="py-2 pr-3 font-audit">{paper.coverage_percent}%</td>
                            <td className="py-2 pr-3 font-audit">{paper.confirmed_failure_rate}%</td>
                            <td className="py-2 pr-3 font-audit text-xs text-stone-400">
                              {paper.type_1 ?? 0} / {paper.type_7 ?? 0} / {paper.retraction ?? 0}
                            </td>
                            <td className="py-2 font-audit uppercase">{paper.risk_level}</td>
                          </tr>
                          {isExpanded && cached && (
                            <tr key={`${paper.audit_id}-heat`} className="border-t border-white/5 bg-black/20">
                              <td colSpan={6} className="py-3">
                                <CitationHeatmap
                                  citations={cached.citations}
                                  selectedId={selected?.id}
                                  onSelect={(citation) => {
                                    setSelected(citation);
                                  }}
                                />
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      );
                    })}
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
                  {audit.status === "failed" && audit.error && (
                    <p className="mt-2 rounded border border-red-900/50 bg-red-950/40 px-2 py-1 text-xs text-red-200">
                      {audit.error}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="font-display font-audit text-3xl font-semibold text-emerald-300">
                    {audit.coverage.coverage_percent}%
                  </p>
                  <p className="text-xs text-[var(--papyrus-muted)]">
                    Coverage ({audit.coverage.tier_1 + audit.coverage.tier_2} of {audit.coverage.total} at Tier 2+)
                  </p>
                  <p className="mt-2 font-audit text-sm uppercase text-amber-300">
                    {audit.risk_level} risk
                    {audit.risk_confidence && (
                      <span className="ml-1 text-xs text-stone-400">({audit.risk_confidence} confidence)</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <CoverageBar audit={audit} />
              </div>
              <CoverageSummary audit={audit} filter={filter} onFilter={setFilter} />
              <LimitationsPanel audit={audit} />
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
                  <a className="text-emerald-300 underline" href={`/api/audits/${audit.id}/events/log.txt`}>
                    Event log
                  </a>
                </div>
              )}
            </div>
          )}

          <div className="rounded-xl border border-white/10 bg-[var(--papyrus-panel)] p-4">
            <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
              Citation heatmap
            </h3>
            <HeatmapLegend />
            <HeatmapFilterBar filter={filter} onFilter={setFilter} />
            <div className="mt-3">
              {filteredCitations.length > 0 ? (
                <CitationHeatmap
                  citations={filteredCitations}
                  selectedId={selected?.id}
                  onSelect={setSelected}
                />
              ) : (
                <p className="text-sm text-[var(--papyrus-muted)]">No citations match this filter.</p>
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
                <div className="mt-3 max-h-64 overflow-y-auto">
                  <PaperAnatomy
                    text={audit.paper_text}
                    citations={audit.citations}
                    onSelectCitation={setSelected}
                  />
                </div>
              )}
            </div>
          )}

          {selected && audit && (
            <SideBySideDrawer
              audit={audit}
              citation={selected}
              claimDraft={claimDraft}
              onClaimDraft={setClaimDraft}
              onSaveIntent={(intent) => void saveIntent(intent)}
              onSaveClaim={() => void saveClaim()}
              onApproveClaim={() => void approveClaim()}
              onRerunCitation={() => void rerunCitation()}
              onClose={() => setSelected(null)}
            />
          )}
        </section>

        <section className="rounded-xl border border-white/10 bg-[#0c100e] p-4 min-h-[70vh]">
          <h3 className="font-audit text-sm uppercase tracking-wide text-[var(--papyrus-muted)]">
            Live resolution panel
          </h3>
          <div className="mt-3 h-[calc(70vh-3rem)]">
            <LivePanel events={events} audit={audit} />
          </div>
        </section>
      </main>
    </div>
  );
}
