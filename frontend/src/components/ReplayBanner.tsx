type Props = {
  replaySet?: string;
};

export function ReplayBanner({ replaySet }: Props) {
  return (
    <div
      data-testid="replay-banner"
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950"
      role="status"
    >
      <p className="font-medium">Replay of a recorded audit</p>
      <p className="mt-1 text-xs text-amber-900/90">
        Shepherd demo loads a recorded audit of the sample PDF ({replaySet ?? "demo-a"}). Your own live uploads call
        providers directly. This preload does not spend SerpApi credits; event timing is compressed for the tour.
      </p>
    </div>
  );
}
