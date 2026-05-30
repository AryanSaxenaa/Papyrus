import { useState } from "react";
import { PaperAnatomy } from "./PaperAnatomy";
import { PaperAnatomyPdf } from "./PaperAnatomyPdf";
import type { CitationRecord } from "../types";

type Props = {
  auditId: string;
  text?: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
};

export function PaperAnatomyView({ auditId, text = "", citations, onSelectCitation }: Props) {
  const hasText = text.trim().length > 0;
  const [mode, setMode] = useState<"pdf" | "text">("pdf");

  return (
    <div className="space-y-3">
      <div className="papyrus-segmented font-audit" role="tablist" aria-label="Anatomy view">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "pdf"}
          data-active={mode === "pdf"}
          className="papyrus-segment"
          onClick={() => setMode("pdf")}
        >
          PDF overlay
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "text"}
          data-active={mode === "text"}
          className="papyrus-segment disabled:cursor-not-allowed disabled:opacity-50"
          onClick={() => setMode("text")}
          disabled={!hasText}
        >
          Text view
        </button>
      </div>
      {mode === "pdf" ? (
        <PaperAnatomyPdf
          auditId={auditId}
          citations={citations}
          onSelectCitation={onSelectCitation}
          onUnavailable={() => {
            if (hasText) setMode("text");
          }}
        />
      ) : hasText ? (
        <div className="max-h-64 overflow-y-auto rounded-xl border border-zinc-200 bg-zinc-50/80 p-4 papyrus-scroll-hidden">
          <PaperAnatomy text={text} citations={citations} onSelectCitation={onSelectCitation} />
        </div>
      ) : (
        <p className="text-sm text-zinc-500">Extracted text is not available yet.</p>
      )}
    </div>
  );
}
