"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard } from "@/components/ui/skeleton";
import { AiHiringIntelligenceSection } from "@/features/ai-hiring-intelligence-section";
import { MatchReviewNavigation } from "@/features/match-details/match-review-navigation";
import { ApiClientError } from "@/lib/api/error";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";

type AiHiringWorkspaceProps = Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>;

function detailsErrorMessage(error: unknown): string {
  return error instanceof ApiClientError ? error.message : "Candidate context could not be loaded. Please try again.";
}

function AiHiringSkeleton() {
  return <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]" role="status" aria-label="Loading AI Hiring"><div className="space-y-6"><SkeletonCard className="min-h-72" /><SkeletonCard className="min-h-52" /></div><SkeletonCard className="min-h-44" /></div>;
}

export function AiHiringWorkspace({ candidateId, vacancyId, enabled }: AiHiringWorkspaceProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);
  const breadcrumb = <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2"><Link href="/#employer-vacancies" className="app-link">Employer dashboard</Link><span aria-hidden="true" className="text-muted">/</span><Link href={`/employer/matches/${encodeURIComponent(candidateId)}?vacancy_id=${encodeURIComponent(vacancyId)}`} className="app-link">Candidate review</Link><span aria-hidden="true" className="text-muted">/</span><span className="text-secondary">AI Hiring</span></nav>;

  if (!enabled) return <EmptyState title="Employer access required" description="AI Hiring is available only to employer accounts." />;
  if (detailsQuery.isLoading) return <div className="space-y-6"><PageHeader eyebrow="AI Hiring" title="AI Hiring" description="AI-generated hiring analysis for the selected candidate and vacancy." breadcrumb={breadcrumb} /><AiHiringSkeleton /></div>;
  if (detailsQuery.isError || !detailsQuery.data) return <div className="space-y-6"><PageHeader eyebrow="AI Hiring" title="AI Hiring" description="AI-generated hiring analysis for the selected candidate and vacancy." breadcrumb={breadcrumb} /><EmptyState role="alert" title="Candidate context unavailable" description={detailsErrorMessage(detailsQuery.error)} /></div>;

  const details = detailsQuery.data;
  return <div className="space-y-6"><PageHeader eyebrow="AI Hiring" title="AI Hiring" description="AI-generated hiring analysis based on the selected vacancy and available candidate evidence." breadcrumb={breadcrumb} /><MatchReviewNavigation candidateId={candidateId} vacancyId={vacancyId} active="ai" /><div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]"><main><AiHiringIntelligenceSection candidateId={candidateId} vacancyId={vacancyId} enabled /></main><aside className="space-y-6"><Card aria-labelledby="ai-context-title"><CardContent className="p-5"><p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">Selected context</p><h2 id="ai-context-title" className="mt-2 break-words text-xl font-semibold tracking-tight text-ink">{details.candidate.name}</h2><p className="mt-2 text-sm leading-6 text-secondary">{details.candidate.headline?.trim() || "Candidate review for the selected vacancy."}</p><div className="mt-5 border-t border-border pt-4"><Badge variant="success">Vacancy match {details.match.score}%</Badge><p className="mt-2 text-sm text-secondary">This deterministic match remains separate from the AI recommendation.</p></div></CardContent></Card><Card><CardContent className="p-5"><p className="text-sm font-medium text-ink">Use AI as supporting information</p><p className="mt-2 text-sm leading-6 text-secondary">Use this analysis as supporting information, not as the sole basis for a hiring decision.</p></CardContent></Card></aside></div></div>;
}
