type IconProps = { className?: string };

export function UploadCloudIcon({ className = "h-5 w-5" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M17 15a4 4 0 0 0-3.8-4.8A5 5 0 1 0 7 14.5"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 9v6M9.5 12.5 12 10l2.5 2.5"
        stroke="currentColor"
        strokeWidth="1.35"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SettingsIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="2" stroke="currentColor" strokeWidth="1.3" />
      <path
        d="M10 2.5v1.5M10 16v1.5M17.5 10h-1.5M4 10H2.5M15.3 4.7l-1 1M5.7 14.3l-1 1M15.3 15.3l-1-1M5.7 5.7l-1-1"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function SparklesIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 1.5l.7 2.8 2.8.7-2.8.7L8 8.5l-.7-2.8-2.8-.7 2.8-.7L8 1.5zM3.5 12l.4 1.6 1.6.4-1.6.4-.4 1.6-.4-1.6-1.6-.4 1.6-.4.4-1.6zM13 10.5l.3 1.2 1.2.3-1.2.3-.3 1.2-.3-1.2-1.2-.3 1.2-.3.3-1.2z"
        fill="currentColor"
      />
    </svg>
  );
}

export function ShieldFeatureIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 2.5 12.5 4.5V8c0 2.8-1.8 5.2-4.5 6-2.7-.8-4.5-3.2-4.5-6V4.5L8 2.5z"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinejoin="round"
      />
      <path d="M6 8l1.2 1.2L10 6.2" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function DownloadFeatureIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M8 3v7M5.5 7.5 8 10l2.5-2.5M4 13h8" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function LockSmallIcon({ className = "h-3 w-3" }: IconProps) {
  return (
    <svg className={className} viewBox="0 0 12 12" fill="none" aria-hidden>
      <rect x="2.5" y="5.5" width="7" height="5" rx="1" stroke="currentColor" strokeWidth="1.1" />
      <path d="M4 5.5V4a2 2 0 1 1 4 0v1.5" stroke="currentColor" strokeWidth="1.1" />
    </svg>
  );
}


