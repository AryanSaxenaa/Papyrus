/** Footer links only — no placeholder pages or non-functional controls. */
export function SiteFooter() {
  return (
    <footer className="border-t border-zinc-100 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-8 text-sm text-zinc-500 lg:px-10">
        <p>© {new Date().getFullYear()} Papyrus</p>
        <nav className="flex flex-wrap items-center gap-6">
          <a
            href="/openapi.json"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-[#0a3d2e]"
          >
            API reference
          </a>
          <a href="mailto:hello@papyrus.app" className="transition-colors hover:text-[#0a3d2e]">
            Contact
          </a>
        </nav>
      </div>
    </footer>
  );
}
