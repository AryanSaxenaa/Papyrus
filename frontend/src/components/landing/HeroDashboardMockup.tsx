import { useRef } from "react";
import { motion } from "motion/react";
import { DemoAuditPreview } from "./DemoAuditPreview";
import { useHeroTilt } from "./useHeroTilt";

/** Marketing hero frame around the real audit dashboard components (`DemoAuditPreview`). */

export function HeroDashboardMockup() {
  const ref = useRef<HTMLDivElement>(null);
  const tilt = useHeroTilt();

  return (
    <div ref={ref} className="relative w-full">
      <motion.div
        ref={tilt.ref}
        onMouseMove={tilt.onMove}
        onMouseLeave={tilt.onLeave}
        style={tilt.style}
        className="hero-dashboard-mockup overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-[0_24px_80px_-20px_rgba(15,23,42,0.18)] will-change-transform"
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.12 }}
      >
        <div className="papyrus-card !m-0 !rounded-none !border-0 !shadow-none">
          <div className="max-h-[min(480px,58vh)] overflow-hidden p-4 sm:p-5">
            <DemoAuditPreview showHeatmap />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
