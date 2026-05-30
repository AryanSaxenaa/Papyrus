import { LandingHero } from "./LandingHero";

/** Full-viewport hero content (nav is rendered at page level). */
export function LandingHeroShell() {
  return (
    <div className="flex min-h-dvh flex-col bg-[#fafafa]">
      <LandingHero />
    </div>
  );
}
