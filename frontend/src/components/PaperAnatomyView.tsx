import { useState } from "react";
import { PaperAnatomy } from "./PaperAnatomy";
import { PaperAnatomyPdf } from "./PaperAnatomyPdf";
import type { CitationRecord } from "../types";

type Props = {
  auditId: string;
  text: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
};

export function PaperAnatomyView({ auditId, text, citations, onSelectCitation }: Props) {
  const [mode, setMode] = useState<"pdf" | "text">("pdf");

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2 font-audit text-xs">
        <button
          type="button"
          onClick={() => setMode("pdf")}
          className={`rounded border px-2 py-1 ${
            mode === "pdf" ? "border-emerald-600/60 bg-emerald-950/40 text-emerald-100" : "border-white/10 text-stone-400"
          }`}
        >
          PDF overlay
        </button>
        <button
          type="button"
          onClick={() => setMode("text")}
          className={`rounded border px-2 py-1 ${
            mode === "text" ? "border-emerald-600/60 bg-emerald-950/40 text-emerald-100" : "border-white/10 text-stone-400"
          }`}
        >
          Text fallback
        </button>
      </div>
      {mode === "pdf" ? (
        <PaperAnatomyPdf
          auditId={auditId}
          citations={citations}
          onSelectCitation={onSelectCitation}
          onUnavailable={() => setMode("text")}
        />
      ) : (
        <div className="max-h-64 overflow-y-auto">
          <PaperAnatomy text={text} citations={citations} onSelectCitation={onSelectCitation} />
        </div>
      )}
    </div>
  );
}
