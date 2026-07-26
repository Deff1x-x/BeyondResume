import { LandingPage } from "@/components/landing-page";

/**
 * Always-public marketing landing.
 * Auth pages link here so "Back to landing" never opens a workspace session view.
 */
export default function PublicLandingPage() {
  return <LandingPage sessionError={false} />;
}
