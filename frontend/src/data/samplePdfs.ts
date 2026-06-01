export type SamplePdf = {
  id: string;
  label: string;
  filename: string;
  description: string;
};

/** Bundled under /samples/ (frontend/public/samples) for audit testing and direct download. */
export const SAMPLE_PDFS: SamplePdf[] = [
  {
    id: "arxiv-2108-12837v1",
    label: "arXiv 2108.12837v1",
    filename: "2108.12837v1.pdf",
    description: "Open-access sample manuscript for end-to-end audit testing.",
  },
];

export function samplePdfUrl(filename: string): string {
  const base = import.meta.env.BASE_URL ?? "/";
  const prefix = base.endsWith("/") ? base : `${base}/`;
  return `${prefix}samples/${encodeURIComponent(filename)}`;
}
