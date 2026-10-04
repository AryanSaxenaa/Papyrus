type Props = {
  replaySet?: string;
};

export function ReplayBanner({ replaySet }: Props) {
  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950"
      role="status"
    >
      <p className="font-medium">Replay of a recorded audit</p>
      <p className="mt-1 text-xs text-amber-900/90">
        Provider responses are served from fixtures ({replaySet ?? "demo-a"}). No API keys, Postgres,
        Redis, or Celery are required. Timing is compressed for demo.
      </p>
    </div>
  );
}
