import { DownloadFeatureIcon, ShieldFeatureIcon, SparklesIcon } from "./AppIcons";

const FEATURES = [
  {
    title: "Comprehensive audit",
    body: "Checks citations, DOIs, metadata, and evidential support.",
    Icon: ShieldFeatureIcon,
  },
  {
    title: "Resolution trails",
    body: "See how every issue is classified and resolved.",
    Icon: SparklesIcon,
  },
  {
    title: "Exportable reports",
    body: "Download heatmaps, logs, and audit reports instantly.",
    Icon: DownloadFeatureIcon,
  },
];

export function AppFeaturesCard() {
  return (
    <div className="min-w-0 rounded-xl border border-zinc-100 bg-[#f6f6f7] p-4 sm:p-5">
      <ul className="space-y-4">
        {FEATURES.map(({ title, body, Icon }) => (
          <li key={title} className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-[#1a3d32] shadow-sm">
              <Icon className="h-4 w-4 shrink-0" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-bold text-zinc-900">{title}</p>
              <p className="mt-0.5 text-[12px] leading-relaxed text-zinc-500">{body}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
