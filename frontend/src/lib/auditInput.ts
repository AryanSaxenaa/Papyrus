export type AuditInputKind = "doi" | "url";

export function parseAuditReference(raw: string): { kind: AuditInputKind; value: string } | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;

  if (/^https?:\/\//i.test(trimmed)) {
    return { kind: "url", value: trimmed };
  }

  const fromDoiOrg = trimmed.match(/doi\.org\/(10\.\S+)/i);
  if (fromDoiOrg) {
    return { kind: "doi", value: fromDoiOrg[1].replace(/[?#].*$/, "") };
  }

  const doi = trimmed.replace(/^doi:\s*/i, "").trim();
  if (/^10\.\d{4,}\/\S+/i.test(doi)) {
    return { kind: "doi", value: doi.replace(/[?#].*$/, "") };
  }

  return null;
}
