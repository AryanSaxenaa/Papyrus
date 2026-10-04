import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
export default function EvalPage() {
  const [report, setReport] = useState<string | null>(null);

  useEffect(() => {
    fetch("/eval/report.json")
      .then((r) => (r.ok ? r.text() : null))
      .then(setReport)
      .catch(() => setReport(null));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link to="/app" className="text-sm text-sky-700 hover:underline">← App</Link>
      <h1 className="mt-4 font-serif-display text-2xl font-bold text-zinc-900">Evaluation</h1>
      <p className="mt-2 text-sm text-zinc-600">
        Metrics are generated offline from labelled fixtures. See <code>docs/EVAL.md</code>.
      </p>
      <pre className="mt-6 overflow-auto rounded-lg border border-zinc-200 bg-zinc-50 p-4 font-audit text-xs">
        {report ?? "No eval/report.json bundled yet. Run: make eval"}
      </pre>
    </div>
  );
}
