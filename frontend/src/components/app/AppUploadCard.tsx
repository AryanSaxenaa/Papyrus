import { useCallback, useRef, useState, type DragEvent, type ReactNode } from "react";
import { ChevronDown } from "../landing/LandingIcons";
import { LockSmallIcon } from "./AppIcons";
import { parseAuditReference } from "../../lib/auditInput";

type Tab = "pdf" | "doi" | "url";

type Props = {
  uploading: boolean;
  onUploadPdf: (file: File) => void;
  onStartReference: (kind: "doi" | "url", value: string) => void;
  onBulkZip: (file: File) => void;
  moreOptions?: ReactNode;
};

const TABS: Array<{ id: Tab; label: string }> = [
  { id: "pdf", label: "Upload PDF" },
  { id: "doi", label: "DOI" },
  { id: "url", label: "URL" },
];

export function AppUploadCard({
  uploading,
  onUploadPdf,
  onStartReference,
  onBulkZip,
  moreOptions,
}: Props) {
  const [tab, setTab] = useState<Tab>("pdf");
  const [reference, setReference] = useState("");
  const [hint, setHint] = useState<string | null>(null);
  const [moreOpen, setMoreOpen] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onFile = useCallback(
    (file: File | undefined) => {
      if (!file || uploading) return;
      if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        setHint("Please choose a PDF file.");
        return;
      }
      setHint(null);
      onUploadPdf(file);
    },
    [onUploadPdf, uploading],
  );

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragOver(false);
    onFile(event.dataTransfer.files?.[0]);
  };

  const onStart = () => {
    const parsed = parseAuditReference(reference);
    if (!parsed) {
      setHint("Enter a valid DOI (10.xxxx/…) or URL (https://…).");
      return;
    }
    setHint(null);
    onStartReference(parsed.kind, parsed.value);
  };

  return (
    <div className="min-w-0 rounded-xl border border-zinc-100 bg-white p-4 sm:p-5">
      <p className="text-[13px] leading-relaxed text-zinc-600">
        Upload a PDF, or paste a DOI or open-access URL. We verify citations and evidential support —{" "}
        <strong className="font-semibold text-[#1a3d32]">not authorship detection.</strong>
      </p>

      <div
        className="mt-4 flex border-b border-zinc-100"
        role="tablist"
        aria-label="Upload method"
      >
        {TABS.map(({ id, label }) => {
          const active = tab === id;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => {
                setTab(id);
                setHint(null);
              }}
              className={`relative -mb-px shrink-0 px-1 pb-2.5 text-[13px] font-semibold whitespace-nowrap transition-colors first:pl-0 last:pr-0 not-first:ml-6 ${
                active ? "text-[#1a3d32]" : "text-zinc-400 hover:text-zinc-600"
              }`}
            >
              {label}
              {active && (
                <span className="absolute inset-x-0 bottom-0 h-[2px] rounded-full bg-[#40916c]" />
              )}
            </button>
          );
        })}
      </div>

      {tab === "pdf" && (
        <div
          role="tabpanel"
          className="mt-4"
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <div
            className={`flex flex-col items-center justify-center rounded-lg border border-dashed px-4 py-7 transition-colors ${
              dragOver ? "border-[#40916c] bg-[#ecfdf3]/40" : "border-zinc-200 bg-zinc-50/30"
            }`}
          >
            <p className="text-center text-[13px] text-zinc-600">
              Drag & drop your file here <span className="text-zinc-400">or</span>
            </p>
            <button
              type="button"
              disabled={uploading}
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 rounded-lg bg-[#1a3d32] px-4 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-[#153028] disabled:opacity-50"
            >
              {uploading ? "Working…" : "Choose PDF file"}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={uploading}
              onChange={(e) => onFile(e.target.files?.[0])}
            />
            <p className="mt-4 flex items-center gap-1 text-[11px] text-zinc-400">
              <LockSmallIcon className="h-3 w-3 shrink-0" />
              Your data is private and secure. We never train on it.
            </p>
          </div>
        </div>
      )}

      {(tab === "doi" || tab === "url") && (
        <div role="tabpanel" className="mt-4 space-y-3">
          <input
            value={reference}
            onChange={(e) => {
              setReference(e.target.value);
              if (hint) setHint(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                onStart();
              }
            }}
            placeholder={tab === "doi" ? "10.1038/nature12373" : "https://arxiv.org/abs/..."}
            disabled={uploading}
            className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2.5 text-[13px] text-zinc-800 placeholder:text-zinc-400 focus:border-[#40916c] focus:outline-none focus:ring-2 focus:ring-[#bbf7d0]/50"
          />
          <button
            type="button"
            disabled={uploading || !reference.trim()}
            onClick={onStart}
            className="rounded-lg bg-[#1a3d32] px-4 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-[#153028] disabled:opacity-50"
          >
            {uploading ? "Starting…" : "Start audit"}
          </button>
          <p className="flex items-center gap-1 text-[11px] text-zinc-400">
            <LockSmallIcon className="h-3 w-3 shrink-0" />
            Your data is private and secure. We never train on it.
          </p>
        </div>
      )}

      {hint && <p className="mt-2 text-[11px] text-amber-700">{hint}</p>}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-zinc-100 pt-3 text-[11px] text-zinc-400">
        <span>Supported format: PDF up to 200MB</span>
        <button
          type="button"
          onClick={() => setMoreOpen((open) => !open)}
          className="inline-flex items-center gap-0.5 font-medium text-zinc-500 transition-colors hover:text-zinc-800"
          aria-expanded={moreOpen}
        >
          More options
          <ChevronDown className={`h-3 w-3 shrink-0 transition-transform ${moreOpen ? "rotate-180" : ""}`} />
        </button>
      </div>

      {moreOpen && (
        <div className="mt-3 space-y-2 rounded-lg border border-zinc-100 bg-zinc-50/80 p-3">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-amber-200/80 bg-amber-50 px-2.5 py-1.5 text-[12px] font-medium text-amber-900 hover:bg-amber-100 transition-colors">
            Upload bulk ZIP
            <input
              type="file"
              accept="application/zip"
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onBulkZip(file);
              }}
            />
          </label>
          {moreOptions}
        </div>
      )}
    </div>
  );
}
