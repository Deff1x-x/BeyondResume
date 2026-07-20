"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { PageContainer } from "@/components/ui/page-container";
import { SkeletonText } from "@/components/ui/skeleton";
import { CandidateVacancyDetailWorkspace } from "@/features/candidate-vacancies-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function CandidateVacancyDetailPage({ params }: Readonly<{ params: { vacancyId: string } }>) {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();
  useEffect(() => { if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login"); }, [isLoading, router, user]);
  if (isLoading) return <PageContainer><SkeletonText className="h-8 w-56" /></PageContainer>;
  if (!user || user.role !== "candidate") return null;
  return <PageContainer><WorkspaceNavigation role="candidate" /><CandidateVacancyDetailWorkspace vacancyId={params.vacancyId} /></PageContainer>;
}
