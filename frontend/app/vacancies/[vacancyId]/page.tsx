"use client";

import { useRouter } from "next/navigation";
import { use, useEffect } from "react";

import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import { CandidateVacancyDetailWorkspace } from "@/features/candidate-vacancies-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function CandidateVacancyDetailPage({ params }: Readonly<{ params: Promise<{ vacancyId: string }> }>) {
  const { vacancyId } = use(params);
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();
  useEffect(() => { if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login"); }, [isLoading, router, user]);
  if (isLoading) return <WorkspaceShell role="candidate"><div role="status" aria-label="Loading vacancy"><SkeletonText className="h-8 w-56" /></div></WorkspaceShell>;
  if (!user || user.role !== "candidate") return null;
  return <WorkspaceShell role="candidate" email={user.email}><CandidateVacancyDetailWorkspace vacancyId={vacancyId} /></WorkspaceShell>;
}
