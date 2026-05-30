type IconProps = { className?: string };

export function PapyrusLogo({ className = "h-[83px] w-[52px]" }: IconProps) {
  return (
    <img
      src="/images/logo.png"
      alt="Papyrus logo"
      className={className}
      draggable={false}
    />
  );
}

export function ChevronDown({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function CheckIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <circle cx="8" cy="8" r="8" fill="#dcfce7" />
      <path
        d="M5 8l2 2 4-4"
        stroke="#2d6a4f"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SparkIcon({ className = "h-3.5 w-3.5" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 14 14" fill="currentColor" aria-hidden>
      <path d="M7 0l1 4 4 1-4 1-1 4-1-4-4-1 4-1 1-4z" />
    </svg>
  );
}

export function DocIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#40916c" strokeWidth="1.5" aria-hidden>
      <path d="M8 4h8l4 4v12H8V4z" />
      <path d="M16 4v4h4M10 12h6M10 16h4" />
    </svg>
  );
}

export function ShieldIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#40916c" strokeWidth="1.5" aria-hidden>
      <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V6l8-3z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function ClockIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#40916c" strokeWidth="1.5" aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

export function ChartIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#0a3d2e" strokeWidth="1.5" aria-hidden>
      <path d="M4 18V6M10 18V10M16 18V14M22 18V4" strokeLinecap="round" />
    </svg>
  );
}

export function LinkIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#0a3d2e" strokeWidth="1.5" aria-hidden>
      <path d="M10 13a5 5 0 0 1 0-7l1-1a5 5 0 0 1 7 7l-1 1M14 11a5 5 0 0 1 0 7l-1 1a5 5 0 0 1-7-7l1-1" strokeLinecap="round" />
    </svg>
  );
}

export function DownloadIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#0a3d2e" strokeWidth="1.5" aria-hidden>
      <path d="M12 3v12M7 10l5 5 5-5M5 21h14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LockIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#0a3d2e" strokeWidth="1.5" aria-hidden>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 1 1 8 0v3" />
    </svg>
  );
}

export function UsersIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="#40916c" strokeWidth="1.5" aria-hidden>
      <circle cx="9" cy="8" r="3" />
      <circle cx="16" cy="10" r="2.5" />
      <path d="M4 19c0-3 2.5-5 5-5s5 2 5 5M13 19c0-2 1.5-3.5 3.5-3.5" />
    </svg>
  );
}

export function PersonLaptopIllustration({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 140 115" fill="none" aria-hidden>
      <circle cx="78" cy="30" r="11" stroke="#18181b" strokeWidth="1.3" />
      <path
        d="M68 44c3-2 18-2 22 0v9H68v-9z"
        stroke="#18181b"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
      <path
        d="M64 48h28"
        stroke="#18181b"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
      <rect x="48" y="56" width="52" height="32" rx="2.5" stroke="#18181b" strokeWidth="1.3" />
      <path d="M42 90h64" stroke="#18181b" strokeWidth="1.3" strokeLinecap="round" />
      <path
        d="M72 30c-4 0-6 2-6 4"
        stroke="#18181b"
        strokeWidth="1"
        strokeLinecap="round"
      />
      <ellipse cx="84" cy="32" rx="5" ry="3" stroke="#18181b" strokeWidth="1" />
      <path d="M98 68c5-7 12-9 18-5" stroke="#95d5b2" strokeWidth="1" />
      <ellipse cx="108" cy="54" rx="4" ry="6" fill="#d8f3dc" stroke="#74c69d" strokeWidth="0.8" />
    </svg>
  );
}

export function PersonMagnifierIllustration({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 140 110" fill="none" aria-hidden>
      <circle cx="55" cy="32" r="11" stroke="#18181b" strokeWidth="1.2" />
      <path d="M42 48h26v10H42z" stroke="#18181b" strokeWidth="1.2" />
      <path d="M48 58v28M62 58v28" stroke="#18181b" strokeWidth="1.2" />
      <circle cx="95" cy="45" r="14" stroke="#18181b" strokeWidth="1.2" />
      <path d="M106 56l12 12" stroke="#18181b" strokeWidth="2" strokeLinecap="round" />
      <rect x="78" y="68" width="36" height="28" rx="2" stroke="#18181b" strokeWidth="1" strokeDasharray="2 2" />
    </svg>
  );
}

export function PersonDeskIllustration({ className }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 130 100" fill="none" aria-hidden>
      <circle cx="45" cy="28" r="10" stroke="#18181b" strokeWidth="1.2" />
      <path d="M32 42h26v8H32z" stroke="#18181b" strokeWidth="1.2" />
      <rect x="20" y="52" width="60" height="6" rx="1" fill="#e4e4e7" stroke="#18181b" strokeWidth="1" />
      <rect x="28" y="58" width="44" height="24" rx="2" stroke="#18181b" strokeWidth="1.2" />
      <path d="M18 82h72" stroke="#18181b" strokeWidth="1.2" />
      <ellipse cx="88" cy="70" rx="5" ry="8" fill="#dcfce7" stroke="#40916c" strokeWidth="0.8" />
    </svg>
  );
}
