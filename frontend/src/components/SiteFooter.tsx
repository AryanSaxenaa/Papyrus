/** Footer links only — no placeholder pages or non-functional controls. */
export function SiteFooter() {
  return (
    <footer className="border-t border-zinc-100 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-8 text-sm text-zinc-500 lg:px-10">
        <p>© {new Date().getFullYear()} Papyrus</p>
        <p>
          Built by{" "}
          <a
            href="https://github.com/AryanSaxenaa"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors hover:text-[#0a3d2e]"
          >
            @AryanSaxenaa
          </a>
        </p>
      </div>
    </footer>
  );
}
