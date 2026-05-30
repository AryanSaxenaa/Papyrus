import { motion } from "motion/react";
import { DocIcon, ShieldIcon, ChartIcon, LinkIcon } from "./LandingIcons";
import { Stagger, fadeUp } from "./motion";

const STATS = [
  { icon: DocIcon, label: "Source-by-source resolution trails" },
  { icon: ShieldIcon, label: "Retraction & hallucination detection" },
  { icon: ChartIcon, label: "Interactive citation heatmap" },
  { icon: LinkIcon, label: "Export to PDF, JSON & TXT" },
];

export function LandingStatsBar() {
  return (
    <div className="rounded-2xl border border-[#bbf7d0]/60 bg-[#ecfdf3] px-6 py-8 sm:px-10 sm:py-9">
      <Stagger className="grid grid-cols-2 gap-x-6 gap-y-8 md:grid-cols-4 md:divide-x md:divide-[#bbf7d0]/80">
        {STATS.map((stat) => (
          <motion.div
            key={stat.label}
            variants={fadeUp}
            className="flex flex-col items-center px-0 text-center md:px-6"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/80 shadow-sm [&_svg]:h-7 [&_svg]:w-7">
              <stat.icon />
            </div>
            <p className="mt-4 text-sm font-medium leading-snug text-zinc-700">{stat.label}</p>
          </motion.div>
        ))}
      </Stagger>
    </div>
  );
}
