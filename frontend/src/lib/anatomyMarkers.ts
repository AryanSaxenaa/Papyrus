import type { CitationRecord } from "../types";

export type AnatomyMarker = {
  marker: string;
  citation: CitationRecord;
};

export type AnatomySegment =
  | { kind: "text"; text: string }
  | { kind: "cite"; text: string; citation: CitationRecord };

export function canShowPaperAnatomy(status: string): boolean {
  return status !== "queued";
}

/** Grobid inline markers plus bracket-index fallback for numeric citation styles. */
export function collectAnatomyMarkers(citations: CitationRecord[]): AnatomyMarker[] {
  const seen = new Set<string>();
  const markers: AnatomyMarker[] = [];

  const add = (raw: string, citation: CitationRecord) => {
    const marker = raw.trim();
    if (!marker) return;
    const key = `${citation.index}\0${marker}`;
    if (seen.has(key)) return;
    seen.add(key);
    markers.push({ marker, citation });
  };

  for (const citation of citations) {
    for (const inline of citation.inline_markers ?? []) {
      add(inline.marker, citation);
    }
    add(`[${citation.index}]`, citation);
  }

  return markers.sort((a, b) => b.marker.length - a.marker.length);
}

export function buildAnatomySegments(text: string, markers: AnatomyMarker[]): AnatomySegment[] {
  if (!text) return [];
  if (!markers.length) return [{ kind: "text", text }];

  const segments: AnatomySegment[] = [];
  let pos = 0;

  while (pos < text.length) {
    let matchAt = -1;
    let matched: AnatomyMarker | null = null;

    for (const candidate of markers) {
      const index = text.indexOf(candidate.marker, pos);
      if (index === -1) continue;
      if (
        matchAt === -1
        || index < matchAt
        || (index === matchAt && candidate.marker.length > (matched?.marker.length ?? 0))
      ) {
        matchAt = index;
        matched = candidate;
      }
    }

    if (!matched || matchAt === -1) {
      segments.push({ kind: "text", text: text.slice(pos) });
      break;
    }

    if (matchAt > pos) {
      segments.push({ kind: "text", text: text.slice(pos, matchAt) });
    }
    segments.push({ kind: "cite", text: matched.marker, citation: matched.citation });
    pos = matchAt + matched.marker.length;
  }

  return segments;
}

/** First matching marker within a PDF text run, if any. */
export function findMarkerInString(
  value: string,
  markers: AnatomyMarker[],
): { marker: AnatomyMarker; start: number; end: number } | null {
  let best: { marker: AnatomyMarker; start: number; end: number } | null = null;

  for (const candidate of markers) {
    const start = value.indexOf(candidate.marker);
    if (start === -1) continue;
    const end = start + candidate.marker.length;
    if (
      !best
      || start < best.start
      || (start === best.start && candidate.marker.length > best.marker.marker.length)
    ) {
      best = { marker: candidate, start, end };
    }
  }

  return best;
}
