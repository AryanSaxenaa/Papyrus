type IconProps = { active?: boolean };

export function StepExtractIcon({ active }: IconProps) {
  const stroke = active ? "#2d6a4f" : "#18181b";
  const fill = active ? "#d8f3dc" : "none";
  return (
    <svg className="h-9 w-9 shrink-0 sm:h-10 sm:w-10" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M7 4h10l2 2v12H7V4z" fill={fill} stroke={stroke} strokeWidth="1.4" />
      <path d="M17 4v2h2M9 10h6M9 14h4" stroke={stroke} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export function StepVerifyIcon({ active }: IconProps) {
  const stroke = active ? "#2d6a4f" : "#18181b";
  return (
    <svg className="h-9 w-9 shrink-0 sm:h-10 sm:w-10" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M12 4l7 2.5v5c0 4.5-2.8 7.8-7 8.5-4.2-.7-7-4-7-8.5v-5L12 4z"
        stroke={stroke}
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      {active && <path d="M9 12l2 2 4-4" stroke={stroke} strokeWidth="1.3" strokeLinecap="round" />}
    </svg>
  );
}

export function StepCheckIcon({ active }: IconProps) {
  const stroke = active ? "#2d6a4f" : "#18181b";
  return (
    <svg className="h-9 w-9 shrink-0 sm:h-10 sm:w-10" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="10" cy="10" r="5.5" stroke={stroke} strokeWidth="1.4" />
      <path d="M14.5 14.5L19 19" stroke={stroke} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function StepClassifyIcon({ active }: IconProps) {
  const stroke = active ? "#2d6a4f" : "#18181b";
  return (
    <svg className="h-9 w-9 shrink-0 sm:h-10 sm:w-10" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="5" y="5" width="14" height="14" rx="2" stroke={stroke} strokeWidth="1.4" />
      <path d="M8 12l3 3 5-6" stroke={stroke} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function StepReportIcon({ active }: IconProps) {
  const stroke = active ? "#2d6a4f" : "#18181b";
  return (
    <svg className="h-9 w-9 shrink-0 sm:h-10 sm:w-10" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M8 4h8l2 2v14H8V4z" stroke={stroke} strokeWidth="1.4" strokeLinejoin="round" />
      <path d="M10 11h6M10 15h4M16 4v2h2" stroke={stroke} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

const ICONS = [StepExtractIcon, StepVerifyIcon, StepCheckIcon, StepClassifyIcon, StepReportIcon];

export function WorkflowStepIcon({ index, active }: { index: number; active: boolean }) {
  const Icon = ICONS[index] ?? StepExtractIcon;
  return <Icon active={active} />;
}
