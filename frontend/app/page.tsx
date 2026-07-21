"use client";

import { LandingPage } from "@/components/landing-page";
import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import { CandidateOverviewSection } from "@/features/candidate-overview-section";
import { EmployerSection } from "@/features/employer-section";
import { EvidenceHubSection } from "@/features/evidence-hub/evidence-hub-section";
import { GitHubSection } from "@/features/github-section";
import { ResumeSection } from "@/features/resume-section";
import { RoadmapSection } from "@/features/roadmap-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function HomePage() {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return <PageContainer><div role="status" aria-label="Loading account" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /><SkeletonText className="h-4 w-48" /></div></PageContainer>;
  }

  if (!user) return <LandingPage sessionError={isError} />;

  return (
    <WorkspaceShell role={user.role} email={user.email}>
      <PageHeader
        eyebrow={user.role === "employer" ? "Recruiting workspace" : "Candidate workspace"}
        title={user.role === "employer" ? "Employer dashboard" : "Your next steps"}
        description={user.role === "employer" ? "Focus on vacancy setup, candidate matches, and the next recruiting action." : "Turn your existing evidence into a clearer, more actionable professional profile."}
      />
      {user.role === "employer" ? <div className="mt-8 grid gap-6 lg:grid-cols-2"><EmployerSection enabled /></div> : <>
        <div className="mt-8"><CandidateOverviewSection enabled /></div>
        <section className="mt-14 grid gap-6 lg:grid-cols-2" aria-label="Manage evidence sources and development">
          <div className="lg:col-span-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Manage your evidence</p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">Sources and development</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">Connect sources, review collected evidence, and use your existing roadmap when you want to go deeper.</p>
          </div>
          <ResumeSection enabled />
          <GitHubSection enabled />
          <EvidenceHubSection enabled />
          <RoadmapSection enabled />
        </section>
      </>}
    </WorkspaceShell>
  );
}
