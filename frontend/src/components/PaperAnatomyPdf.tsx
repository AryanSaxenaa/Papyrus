import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import type { CitationRecord } from "../types";
import { citationFill, isRetraction } from "../lib/verdictColors";

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type Props = {
  auditId: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
  onUnavailable?: () => void;
};

export function PaperAnatomyPdf({ auditId, citations, onSelectCitation, onUnavailable }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const byIndex = new Map(citations.map((c) => [c.index, c]));

    async function render() {
      const container = containerRef.current;
      if (!container) return;

      setLoading(true);
      setError(null);
      container.innerHTML = "";

      try {
        const pdf = await pdfjsLib.getDocument(`/api/audits/${auditId}/paper.pdf`).promise;
        const scale = 1.15;
        const markerPattern = /\[(\d+)\]/g;

        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
          if (cancelled) return;
          const page = await pdf.getPage(pageNumber);
          const viewport = page.getViewport({ scale });
          const pageWrap = document.createElement("div");
          pageWrap.className = "relative mb-4";
          pageWrap.style.width = `${viewport.width}px`;
          pageWrap.style.height = `${viewport.height}px`;

          const canvas = document.createElement("canvas");
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          const context = canvas.getContext("2d");
          if (!context) continue;
          await page.render({ canvasContext: context, viewport }).promise;
          pageWrap.appendChild(canvas);

          const textContent = await page.getTextContent();
          for (const item of textContent.items) {
            if (!("str" in item) || typeof item.str !== "string") continue;
            let match: RegExpExecArray | null;
            markerPattern.lastIndex = 0;
            while ((match = markerPattern.exec(item.str)) !== null) {
              const citationIndex = Number(match[1]);
              const citation = byIndex.get(citationIndex);
              if (!citation) continue;
              const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
              const x = tx[4];
              const y = viewport.height - tx[5] - 12;

              const button = document.createElement("button");
              button.type = "button";
              button.textContent = match[0];
              button.title = `Citation #${citation.index}`;
              button.className = `absolute z-10 rounded px-1 font-audit text-[10px] font-bold text-white ${
                isRetraction(citation) ? "ring-1 ring-amber-400" : ""
              }`;
              button.style.left = `${x}px`;
              button.style.top = `${y}px`;
              button.style.backgroundColor = citationFill(citation);
              button.onclick = () => onSelectCitation(citation);
              pageWrap.appendChild(button);
            }
          }
          if (!cancelled) container.appendChild(pageWrap);
        }

        if (!cancelled) setLoading(false);
      } catch {
        if (!cancelled) {
          setError("Source PDF unavailable.");
          setLoading(false);
          onUnavailable?.();
        }
      }
    }

    void render();
    return () => {
      cancelled = true;
    };
  }, [auditId, citations, onSelectCitation, onUnavailable]);

  return (
    <div className="max-h-[28rem] overflow-auto rounded border border-white/10 bg-stone-950/40 p-2">
      {loading && (
        <p className="mb-2 text-sm text-[var(--papyrus-muted)]">Loading PDF with citation overlays…</p>
      )}
      {error && <p className="mb-2 text-sm text-amber-200">{error}</p>}
      <div
        ref={containerRef}
        className={`mx-auto w-fit ${loading && !error ? "opacity-0" : ""}`}
        aria-hidden={loading && !error}
      />
    </div>
  );
}
