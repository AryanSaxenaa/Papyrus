import { useMemo } from "react";
import type { CitationRecord } from "../types";
import { buildAnatomySegments, collectAnatomyMarkers } from "../lib/anatomyMarkers";
import { citationFill, citationMarkerRingClass } from "../lib/verdictColors";

type Props = {
  text: string;
  citations: CitationRecord[];
  onSelectCitation: (citation: CitationRecord) => void;
};

export function PaperAnatomy({ text, citations, onSelectCitation }: Props) {
  const segments = useMemo(() => {
    const markers = collectAnatomyMarkers(citations);
    return buildAnatomySegments(text, markers);
  }, [text, citations]);

  if (!segments.length) {
    return (
      <p className="text-sm text-[var(--papyrus-muted)]">
        No inline citation markers matched the extracted text. Try PDF overlay or check that Grobid found in-text
        citations.
      </p>
    );
  }

  return (
    <div className="text-sm leading-relaxed text-zinc-700">
      {segments.map((segment, index) => {
        if (segment.kind === "text") {
          return <span key={`${index}-text`}>{segment.text}</span>;
        }
        const { citation } = segment;
        const color = citationFill(citation);
        return (
          <button
            key={`${index}-cite-${citation.index}`}
            type="button"
            onClick={() => onSelectCitation(citation)}
            className={`mx-0.5 inline rounded px-1 font-audit text-xs font-semibold text-white transition hover:opacity-90 ${citationMarkerRingClass(citation)}`}
            style={{ background: color }}
            title={`Citation #${citation.index}: ${citation.bibliography.title ?? "Reference"}`}
            data-citation-index={citation.index}
          >
            {segment.text}
          </button>
        );
      })}
    </div>
  );
}
