"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageContainer } from "@/components/ui/page-container";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonText } from "@/components/ui/skeleton";
import { WorkspaceNavigation } from "@/components/workspace-navigation";
import { CandidateProfileSection } from "@/features/candidate-profile-section";
import { useCurrentUser } from "@/lib/auth/hooks";

export default function ProfilePage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();
  useEffect(() => {
    if (!isLoading && (!user || user.role !== "candidate")) router.replace(user ? "/" : "/login");
  }, [isLoading, router, user]);
  if (isLoading) return <PageContainer><div role="status" className="space-y-3"><SkeletonText className="h-4 w-28" /><SkeletonText className="h-8 w-64" /></div></PageContainer>;
  if (!user || user.role !== "candidate") return null;
  return <PageContainer><WorkspaceNavigation role="candidate" /><PageHeader title="Your profile" description="Keep the details employers need to understand your goals and experience up to date." /><div className="mt-8"><CandidateProfileSection enabled /></div></PageContainer>;
}
