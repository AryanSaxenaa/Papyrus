const TRUSTED_BY = [
  { id: "mit", name: "MIT", sub: "Massachusetts Institute of Technology" },
  { id: "stanford", name: "Stanford", sub: "University" },
  { id: "berkeley", name: "Berkeley", sub: "University of California" },
  { id: "harvard", name: "Harvard", sub: "University" },
  { id: "nature", name: "nature", sub: null },
];

export function TrustLogos() {
  return (
    <div className="flex flex-col items-start gap-3">
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-400">
        Trusted by researchers at
      </p>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        {TRUSTED_BY.map((inst) => (
          <div key={inst.id} className="flex flex-col items-center">
            <span className="text-[14px] font-semibold text-zinc-500">
              {inst.name}
            </span>
            {inst.sub && (
              <span className="text-[8px] font-medium uppercase tracking-wider text-zinc-300">
                {inst.sub}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
