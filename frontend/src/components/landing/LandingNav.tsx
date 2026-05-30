import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { PapyrusLogo } from "./LandingIcons";
import { MagneticLinkButton } from "./motion";

const NAV_LINKS = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "Docs", href: "#features" },
];

function NavAnchor({
  label,
  href,
  onNavigate,
}: {
  label: string;
  href: string;
  onNavigate?: () => void;
}) {
  return (
    <a
      href={href}
      onClick={onNavigate}
      className="text-[15px] font-medium text-zinc-500 transition-colors hover:text-zinc-900"
    >
      {label}
    </a>
  );
}

function navHref(hash: string, onApp: boolean) {
  return onApp ? `/${hash}` : hash;
}

export function LandingNav() {
  const { pathname } = useLocation();
  const onApp = pathname.startsWith("/app");
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 shrink-0 border-b border-zinc-200/50 bg-[#fafafa]/90 backdrop-blur-md">
      <div className="mx-auto grid h-[var(--lp-nav-h)] max-w-[1280px] grid-cols-[1fr_auto] items-center gap-4 px-6 lg:grid-cols-[1fr_auto_1fr] lg:px-10">
        <Link
          to="/"
          className="flex items-center gap-2.5 justify-self-start"
          onClick={closeMenu}
        >
          <PapyrusLogo className="h-[83px] w-[52px]" />
          <span className="text-[1.35rem] font-bold tracking-[-0.02em] text-zinc-900">
            Papyrus
          </span>
        </Link>

        <nav
          className="hidden items-center justify-center gap-8 lg:flex"
          aria-label="Main navigation"
        >
          {NAV_LINKS.map((link) => (
            <NavAnchor key={link.label} label={link.label} href={navHref(link.href, onApp)} />
          ))}
        </nav>

        <div className="flex items-center justify-self-end gap-3 sm:gap-5">
          <MagneticLinkButton>
            {onApp ? (
              <a
                href="#audit-start"
                className="inline-block rounded-[10px] bg-[#1b4332] px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#163724] sm:px-4 sm:py-2.5 sm:text-[15px]"
              >
                New audit
              </a>
            ) : (
              <Link
                to="/app"
                className="inline-block rounded-[10px] bg-[#1b4332] px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#163724] sm:px-4 sm:py-2.5 sm:text-[15px]"
              >
                Get started
              </Link>
            )}
          </MagneticLinkButton>
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-200 text-zinc-700 lg:hidden"
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" aria-hidden>
              {menuOpen ? (
                <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              ) : (
                <path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            id="mobile-nav"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden border-t border-zinc-200/60 bg-[#fafafa] lg:hidden"
          >
            <nav className="flex flex-col gap-1 px-6 py-4" aria-label="Mobile navigation">
              {NAV_LINKS.map((link) => (
                <NavAnchor
                  key={link.label}
                  label={link.label}
                  href={navHref(link.href, onApp)}
                  onNavigate={closeMenu}
                />
              ))}
              {onApp && (
                <a
                  href="#audit-start"
                  onClick={closeMenu}
                  className="mt-2 inline-block rounded-[10px] bg-[#1b4332] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#163724]"
                >
                  New audit
                </a>
              )}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
