import { Link } from "react-router-dom";
import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { HeroDashboardMockup } from "./HeroDashboardMockup";
import { CheckIcon, SparkIcon } from "./LandingIcons";
import { MagneticLinkButton, Stagger, fadeUp } from "./motion";

export function LandingHero() {
  const reduce = useReducedMotion();
  const { scrollY } = useScroll();
  const leftY = useTransform(scrollY, [0, 400], [0, reduce ? 0 : 40]);
  const rightY = useTransform(scrollY, [0, 400], [0, reduce ? 0 : -28]);

  return (
    <section className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className="relative z-10 mx-auto flex w-full max-w-[1280px] flex-1 flex-col px-6 pb-10 -mt-3 lg:px-10 lg:pb-12 lg:pt-0">
        <div className="grid flex-1 items-center gap-10 lg:grid-cols-[minmax(0,480px)_minmax(0,1fr)] lg:gap-14 xl:gap-16">
          <motion.div style={{ y: leftY }} className="max-w-[520px]">
            <Stagger stagger={0.07}>
              <motion.p
                variants={fadeUp}
                className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-[#52b788]"
              >
                <SparkIcon className="h-3.5 w-3.5 shrink-0 text-[#52b788]" />
                AI-powered citation audit
              </motion.p>

              <motion.h1
                variants={fadeUp}
                className="mt-5 text-[clamp(1.875rem,5.5vw,3.5rem)] font-bold leading-[1.1] tracking-[-0.03em] text-zinc-900"
              >
                <span className="block sm:whitespace-nowrap">Audit every citation.</span>
                <span className="block sm:whitespace-nowrap">Trust every claim.</span>
              </motion.h1>

              <motion.p
                variants={fadeUp}
                className="mt-5 max-w-[440px] text-[17px] leading-[1.65] text-zinc-500"
              >
                Papyrus uses AI to detect hallucinations, retractions, and mismatches—so you can
                publish with confidence.
              </motion.p>

              <motion.div variants={fadeUp} className="mt-8 flex flex-wrap items-center gap-3">
                <MagneticLinkButton>
                  <Link
                    to="/app"
                    className="inline-block rounded-xl bg-[#1b4332] px-7 py-3.5 text-[15px] font-semibold text-white shadow-sm transition-colors hover:bg-[#163724]"
                  >
                    Start auditing for free
                  </Link>
                </MagneticLinkButton>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center gap-1 rounded-xl border border-zinc-200 bg-white px-7 py-3.5 text-[15px] font-semibold text-zinc-800 shadow-sm transition-colors hover:border-zinc-300 hover:bg-zinc-50"
                >
                  See how it works
                  <span aria-hidden>→</span>
                </a>
              </motion.div>

              <motion.ul variants={fadeUp} className="mt-6 flex flex-wrap gap-x-7 gap-y-2">
                {["Free forever", "No credit card", "Setup in 60 seconds"].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-[14px] text-zinc-600">
                    <CheckIcon />
                    {item}
                  </li>
                ))}
              </motion.ul>
            </Stagger>
          </motion.div>

          <motion.div
            className="relative flex items-center justify-center lg:justify-end"
            style={{ y: rightY }}
          >
            <div className="w-full max-w-[640px]">
              <HeroDashboardMockup />
            </div>
            <div
              className="pointer-events-none absolute bottom-5 right-[-156px] z-10 hidden md:block lg:bottom-5 lg:right-[-156px]"
            >
              <div
                className="h-[18.792rem] w-[19.44rem] overflow-hidden lg:h-[22.032rem] lg:w-[22.68rem]"
              >
                <img
                  src="/images/L1A.png"
                  alt=""
                  width={362}
                  height={467}
                  decoding="async"
                  className="h-[145%] w-full object-contain object-bottom mix-blend-screen"
                />
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
