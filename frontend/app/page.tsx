"use client";

import { LandingPage } from "@/components/landing-page";
import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { CandidateDashboardSection } from "@/features/candidate-dashboard-section";
import { EmployerSection } from "@/features/employer-section";
import { EvidenceHubSection } from "@/features/evidence-hub/evidence-hub-section";
import { GitHubSection } from "@/features/github-section";
import { ResumeSection } from "@/features/resume-section";
import { RoadmapSection } from "@/features/roadmap-section";
import { SkillPassportSection } from "@/features/skill-passport-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function HomePage() {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return <PageContainer><div role="status" aria-label="Loading account" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /><SkeletonText className="h-4 w-48" /></div></PageContainer>;
  }

  if (!user) return <LandingPage sessionError={isError} />;

  return (
    <PageContainer>
      <WorkspaceNavigation role={user.role} />
      <PageHeader title={user.role === "employer" ? "Employer workspace" : "Candidate workspace"} description={user.role === "employer" ? `Signed in as ${user.email}` : "Your overview of verified professional signals and next steps."} />
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {user.role === "employer" ? <EmployerSection enabled /> : <>
          <CandidateDashboardSection enabled />
          <EvidenceHubSection enabled />
          <ResumeSection enabled />
          <GitHubSection enabled />
          <SkillPassportSection enabled />
          <RoadmapSection enabled />
        </>}
      </div>
    </PageContainer>
  );
}
