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


