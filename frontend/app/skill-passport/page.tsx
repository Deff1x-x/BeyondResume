"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import { SkillPassportWorkspace } from "@/features/skill-passport-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function SkillPassportPage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login");
  }, [isLoading, router, user]);

  if (isLoading) return <WorkspaceShell role="candidate"><div role="status" aria-label="Loading skill passport" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /></div></WorkspaceShell>;
  if (!user || user.role !== "candidate") return null;

  return <WorkspaceShell role="candidate" email={user.email}><PageHeader eyebrow="Evidence profile" titleId="skill-passport-title" title="Skill Passport" description="A living view of the skills your work has already demonstrated, connected directly to the evidence behind them." /><div className="mt-8"><SkillPassportWorkspace /></div></WorkspaceShell>;
}
