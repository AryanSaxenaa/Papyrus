import { Link } from "react-router-dom";

export default function MethodPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 prose prose-zinc">
      <Link to="/app" className="text-sm text-sky-700 hover:underline no-underline">← App</Link>
      <h1 className="font-serif-display">Method & limits</h1>
      <p>
        Papyrus checks reference integrity: existence, metadata agreement, and (for evidentiary citations)
        whether retrieved text supports the claim. It does not detect AI authorship.
      </p>
      <h2>Scholar witness (SerpApi)</h2>
      <p>
        Google Scholar results are one witness among many. Silence in Scholar is labelled unknown, not
        failure. Author profile checks are positive-only.
      </p>
      <p>
        Full detail: <code>docs/METHOD.md</code> in the repository.
      </p>
    </div>
  );
}
