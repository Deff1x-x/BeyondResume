"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function SkillPassportPage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login");
  }, [isLoading, router, user]);

  if (isLoading) return <PageContainer><div role="status" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /></div></PageContainer>;
  if (!user || user.role !== "candidate") return null;

  return <PageContainer><WorkspaceNavigation role="candidate" /><PageHeader titleId="skill-passport-title" title="Skill Passport" description="A living view of the skills your work has already demonstrated, connected directly to the evidence behind them." /><div className="mt-8"><SkillPassportWorkspace /></div></PageContainer>;
}
