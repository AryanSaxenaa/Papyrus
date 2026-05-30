import { motion, useReducedMotion } from "motion/react";

export function HeroDecorations() {
  const reduce = useReducedMotion();

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <div
        className="absolute -right-24 top-[8%] h-[min(520px,55vh)] w-[min(520px,55vh)] rounded-full opacity-70 hero-blob-a"
      />
      <div
        className="absolute left-[20%] top-[45%] h-[min(380px,45vh)] w-[min(380px,45vh)] rounded-full opacity-50 hero-blob-b"
      />
      <div
        className="absolute -left-32 bottom-[5%] h-[min(300px,35vh)] w-[min(300px,35vh)] rounded-full opacity-35 hero-blob-c"
      />

      {!reduce && (
        <>
          <motion.div
            className="absolute right-[32%] top-[18%] h-14 w-14 rounded-full border border-[#b7e4c7]/50"
            animate={{ y: [0, -10, 0], scale: [1, 1.04, 1] }}
            transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute left-[6%] top-[28%] h-2 w-2 rounded-full bg-[#95d5b2]/60"
            animate={{ opacity: [0.4, 0.9, 0.4] }}
            transition={{ duration: 4, repeat: Infinity }}
          />
        </>
      )}
    </div>
  );
}
