import { Link } from "react-router-dom";
import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { LandingHeroShell } from "../components/landing/LandingHeroShell";
import { LandingNav } from "../components/landing/LandingNav";
import { LandingHowItWorks } from "../components/landing/LandingHowItWorks";
import { LandingStatsBar } from "../components/landing/LandingStatsBar";
import { SiteFooter } from "../components/SiteFooter";
import "../components/landing/landing.css";
import {
  ChartIcon,
  CheckIcon,
  DownloadIcon,
  LinkIcon,
  LockIcon,
} from "../components/landing/LandingIcons";
import {
  MagneticLinkButton,
  Reveal,
  Stagger,
  fadeUp,
} from "../components/landing/motion";

const FEATURES = [
  {
    icon: ChartIcon,
    title: "Live audit",
    body: "Upload a manuscript and watch citations resolve in real time with full transparency.",
  },
  {
    icon: LinkIcon,
    title: "Full traceability",
    body: "See exactly why each citation was flagged, with source-by-source resolution trails.",
  },
  {
    icon: DownloadIcon,
    title: "Export & share",
    body: "Export reports in TXT, JSON, or PDF for collaborators and journal submissions.",
  },
  {
    icon: LockIcon,
    title: "Private & secure",
    body: "Your data stays private. We never train models on your manuscripts.",
  },
];

export default function LandingPage() {
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const ctaIllustrationY = useTransform(scrollYProgress, [0.55, 0.85], [0, reduce ? 0 : -24]);

  return (
    <div className="landing-page min-h-screen overflow-x-hidden bg-[#fafafa] text-zinc-900">
      <LandingNav />
      <LandingHeroShell />

      <div className="bg-white">
      <LandingHowItWorks />

      <div className="mx-auto max-w-6xl px-6 pt-8 pb-6">
        <LandingStatsBar />
      </div>

      {/* Features */}
      <section
        id="features"
        className="relative scroll-mt-[var(--lp-nav-h)] overflow-hidden pt-4 pb-20 lg:pt-6 lg:pb-24"
      >
        <div className="pointer-events-none absolute top-1/4 z-10 hidden xl:block" style={{ right: "-216px" }}>
          <img
            src="/images/L3A.png"
            alt=""
            aria-hidden="true"
            className="h-[396px] w-auto opacity-90"
          />
        </div>

        <div className="relative mx-auto max-w-6xl px-6">
          <Reveal>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#40916c]">
              For editors, integrity offices, and researchers
            </p>
            <h2 className="font-serif-display mt-3 max-w-lg text-3xl font-bold tracking-tight text-[#0a3d2e] sm:text-4xl">
              Built for research.
              <br />
              Backed by transparency.
            </h2>
          </Reveal>

          <Stagger className="mt-12 grid gap-5 sm:grid-cols-2" stagger={0.1}>
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                whileHover={reduce ? undefined : { y: -6, transition: { duration: 0.2 } }}
                className="rounded-2xl border border-zinc-100 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#ecfdf3]">
                  <feature.icon />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-zinc-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-500">{feature.body}</p>
              </motion.div>
            ))}
          </Stagger>
        </div>
      </section>

      {/* CTA */}
      <section
        id="pricing"
        className="mx-auto max-w-6xl scroll-mt-[var(--lp-nav-h)] px-6 pb-20"
      >
        <Reveal>
          <div className="overflow-hidden rounded-3xl bg-[#ecfdf3] px-8 py-12 lg:px-14 lg:py-14">
            <div className="grid items-center gap-10 lg:grid-cols-[auto_1fr_auto]">
              <motion.div style={{ y: ctaIllustrationY }} className="mx-auto lg:mx-0">
                <img
                  src="/images/L5A.png"
                  alt=""
                  aria-hidden="true"
                  className="h-32 w-auto scale-[2.16] origin-center"
                />
              </motion.div>
              <div className="text-center lg:text-left lg:ml-12">
                <h2 className="font-serif-display text-2xl font-bold tracking-tight text-[#0a3d2e] sm:text-3xl">
                  <span className="sm:whitespace-nowrap">You focus on the research.</span>
                  <br />
                  <span className="sm:whitespace-nowrap">Papyrus audits the reference layer.</span>
                </h2>
                <div className="mt-7 flex flex-wrap justify-center gap-3 lg:justify-start">
                  <MagneticLinkButton>
                    <Link
                      to="/app"
                      className="inline-block rounded-xl bg-[#0a3d2e] px-6 py-3 text-sm font-semibold text-white hover:bg-[#082f24] transition-colors"
                    >
                      Start auditing for free
                    </Link>
                  </MagneticLinkButton>
                  <a
                    href="mailto:hello@papyrus.app"
                    className="inline-block rounded-xl border border-[#0a3d2e]/20 bg-white px-6 py-3 text-sm font-semibold text-[#0a3d2e] hover:bg-white/80 transition-colors"
                  >
                    Book a demo →
                  </a>
                </div>
              </div>
              <ul className="space-y-3 text-sm text-zinc-600">
                {["No credit card required", "Free plan available", "Cancel anytime"].map(
                  (item) => (
                    <li key={item} className="flex items-center gap-2">
                      <CheckIcon />
                      {item}
                    </li>
                  ),
                )}
              </ul>
            </div>
          </div>
        </Reveal>
      </section>

      </div>

      <SiteFooter />
    </div>
  );
}
