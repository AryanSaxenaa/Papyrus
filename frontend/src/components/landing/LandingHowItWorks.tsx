import { useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  useMotionValueEvent,
  useReducedMotion,
  useScroll,
} from "motion/react";
import { PaperAnatomyMockup } from "./PaperAnatomyMockup";
import { WorkflowStepIcon } from "./WorkflowStepIcons";

export const WORKFLOW_STEPS = [
  {
    n: 1,
    title: "Extract",
    body: "GROBID parses your PDF and extracts every bibliography entry with surrounding context.",
  },
  {
    n: 2,
    title: "Verify",
    body: "CrossRef, Semantic Scholar, and OpenAlex cross-reference every DOI and metadata field.",
  },
  {
    n: 3,
    title: "Check",
    body: "Retraction flags, title drift, date impossibilities, and claim alignment via NLI on bounded inputs.",
  },
  {
    n: 4,
    title: "Classify",
    body: "Citations are labeled with clear, actionable verdicts.",
  },
  {
    n: 5,
    title: "Report",
    body: "Get a transparent report you can trust and share.",
  },
];

function indexFromScrollProgress(progress: number, count: number) {
  if (count <= 1) return 0;
  const clamped = Math.min(1, Math.max(0, progress));
  return Math.min(count - 1, Math.floor(clamped * count));
}

function StaticHowItWorks({
  active,
  onSelectStep,
}: {
  active: number;
  onSelectStep: (index: number) => void;
}) {
  return (
    <section
      id="how-it-works"
      className="scroll-mt-[var(--lp-nav-h)] bg-white py-16 lg:py-24"
      aria-labelledby="how-it-works-heading"
    >
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#40916c]">
            Verifiable. Transparent. Independent.
          </p>
          <h2
            id="how-it-works-heading"
            className="font-serif-display mt-3 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl lg:text-[2.65rem] lg:leading-[1.15]"
          >
            A citation integrity audit pipeline with receipts.
          </h2>
        </div>
        <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,400px)_1fr] lg:items-start lg:gap-12 xl:gap-16">
          <WorkflowStepList active={active} onSelectStep={onSelectStep} />
          <PaperAnatomyMockup activeStep={active} />
        </div>
      </div>
    </section>
  );
}

function WorkflowStepList({
  active,
  onSelectStep,
}: {
  active: number;
  onSelectStep?: (index: number) => void;
}) {
  return (
    <div className="relative">
      <ol className="workflow-steps-list relative space-y-1" aria-label="How Papyrus works">
        {WORKFLOW_STEPS.map((step, index) => {
          const isActive = active === index;
          const Tag = onSelectStep ? "button" : "div";
          return (
            <li key={step.n}>
              <Tag
                {...(onSelectStep
                  ? {
                      type: "button" as const,
                      onClick: () => onSelectStep(index),
                    }
                  : {})}
                aria-current={isActive ? "step" : undefined}
                className="relative flex w-full gap-4 rounded-2xl px-4 py-4 text-left transition-colors"
              >
                {isActive && (
                  <>
                    <motion.div
                      layoutId="workflow-step-bg"
                      className="absolute inset-0 rounded-2xl bg-[#ecfdf3] ring-1 ring-[#bbf7d0]"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                    <motion.div
                      layoutId="workflow-step-tail"
                      className="absolute -right-1.5 top-1/2 z-20 hidden h-3 w-3 -translate-y-1/2 rotate-45 bg-[#ecfdf3] ring-1 ring-[#bbf7d0] lg:block"
                      style={{ borderRight: 0, borderBottom: 0 }}
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  </>
                )}
                <span className="relative z-10 flex w-11 shrink-0 items-center justify-center sm:w-12">
                  <WorkflowStepIcon index={index} active={isActive} />
                </span>
                <div className="relative z-10 min-w-0">
                  <p
                    className={`text-[15px] font-bold ${
                      isActive ? "text-[#2d6a4f]" : "text-zinc-900"
                    }`}
                  >
                    {step.n}. {step.title}
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-zinc-500">{step.body}</p>
                </div>
              </Tag>
            </li>
          );
        })}
      </ol>
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-white to-transparent"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-8 bg-gradient-to-b from-transparent to-white"
        aria-hidden
      />
    </div>
  );
}

export function LandingHowItWorks() {
  const reduce = useReducedMotion();
  const [active, setActive] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef(0);

  const { scrollYProgress } = useScroll({
    target: triggerRef,
    offset: ["start center", "end center"],
  });

  useMotionValueEvent(scrollYProgress, "change", (progress) => {
    const next = indexFromScrollProgress(progress, WORKFLOW_STEPS.length);
    if (next !== activeRef.current) {
      activeRef.current = next;
      setActive(next);
    }
    setIsVisible(progress > 0 && progress < 1);
  });

  if (reduce) {
    return <StaticHowItWorks active={active} onSelectStep={setActive} />;
  }

  return (
    <>
      <div
        id="how-it-works"
        ref={triggerRef}
        className="scroll-mt-[var(--lp-nav-h)]"
        style={{ height: `${WORKFLOW_STEPS.length * 100}vh` }}
        aria-hidden
      />

      <div style={{ height: "50vh" }} aria-hidden />

      <AnimatePresence>
        {isVisible && (
          <motion.section
            key="how-it-works-pinned"
            className="fixed inset-0 z-20 flex items-center justify-center bg-white"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            aria-labelledby="how-it-works-heading"
          >
            <div
              className="mx-auto flex w-full max-w-6xl flex-col justify-center px-6"
              style={{ transform: "scale(0.8)" }}
            >
              <div className="max-w-2xl">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#40916c]">
                  Verifiable. Transparent. Independent.
                </p>
                <h2
                  id="how-it-works-heading"
                  className="font-serif-display mt-3 text-3xl font-bold tracking-tight text-zinc-900 sm:text-4xl lg:text-[2.65rem] lg:leading-[1.15]"
                >
                  A citation integrity audit pipeline with receipts.
                </h2>
              </div>

              <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,400px)_1fr] lg:items-center lg:gap-12 xl:gap-16">
                <WorkflowStepList active={active} />
                <PaperAnatomyMockup activeStep={active} />
              </div>
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </>
  );
}
