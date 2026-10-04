type Props = {
  mode: string;
  monthlySpent?: number;
  monthlyCap?: number;
  perAuditCap?: number;
  enabled?: boolean;
};

export function CreditsMeter({ mode, monthlySpent = 0, monthlyCap = 240, perAuditCap = 40, enabled }: Props) {
  if (mode === "replay") {
    return (
      <p className="font-audit text-[11px] text-zinc-500">SerpApi: replay mode — no credits spent</p>
    );
  }
  if (!enabled) {
    return <p className="font-audit text-[11px] text-zinc-500">SerpApi witness disabled</p>;
  }
  const remaining = Math.max(0, monthlyCap - monthlySpent);
  const pct = monthlyCap > 0 ? Math.min(100, (monthlySpent / monthlyCap) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between font-audit text-[10px] text-zinc-500">
        <span>SerpApi credits (month)</span>
        <span>{monthlySpent} / {monthlyCap} · per-audit cap {perAuditCap}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-zinc-200">
        <div
          className="h-full rounded-full bg-sky-600 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="font-audit text-[10px] text-zinc-400">{remaining} remaining this month (ledger)</p>
    </div>
  );
}
