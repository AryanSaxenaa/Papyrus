import type { StreamEvent } from "../types";

/** SSE event names emitted by the Papyrus API (see backend event_bus.emit types). */
export const SSE_EVENT_TYPES = [
  "ingestion",
  "grobid",
  "intent",
  "crossref",
  "semantic_scholar",
  "openalex",
  "arxiv",
  "europe_pmc",
  "unpaywall",
  "apify",
  "fulltext",
  "firecrawl",
  "title_drift",
  "journal",
  "version",
  "exa",
  "claim",
  "verdict",
  "user",
  "summary",
  "bulk",
  "error",
] as const;

function parseEventData(data: string): StreamEvent | null {
  try {
    return JSON.parse(data) as StreamEvent;
  } catch {
    return null;
  }
}

/**
 * Subscribe to audit/bulk SSE streams. Backend uses named events (not default `message`),
 * so we register listeners for each type plus `message` as fallback.
 */
export function connectAuditEventSource(
  url: string,
  onEvent: (event: StreamEvent) => void,
): EventSource {
  const source = new EventSource(url);

  const push = (raw: MessageEvent) => {
    if (!raw.data) return;
    const parsed = parseEventData(raw.data);
    if (parsed) onEvent(parsed);
  };

  source.onmessage = push;
  for (const type of SSE_EVENT_TYPES) {
    source.addEventListener(type, push);
  }

  return source;
}
