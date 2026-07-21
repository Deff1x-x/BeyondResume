"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceShell } from "@/components/workspace-shell";
import { CandidateProfileSection } from "@/features/candidate-profile-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function ProfilePage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();
  useEffect(() => {
    if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login");
  }, [isLoading, router, user]);
  if (isLoading) return <WorkspaceShell role="candidate"><div role="status" aria-label="Loading profile" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /></div></WorkspaceShell>;
  if (!user || user.role !== "candidate") return null;
  return <WorkspaceShell role="candidate" email={user.email}><PageHeader eyebrow="Account" title="Your profile" description="Keep the details employers need to understand your goals and experience up to date." /><div className="mt-8"><CandidateProfileSection enabled /></div></WorkspaceShell>;
}
