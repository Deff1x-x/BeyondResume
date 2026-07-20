"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { SkeletonCard, SkeletonListRow } from "@/components/ui/skeleton";
import { EvidenceCard } from "@/features/match-details/evidence-card";
import { AiExplanationCard } from "@/features/match-details/ai-explanation-card";
import { RoadmapCard } from "@/features/match-details/roadmap-card";
import { SkillsComparisonCard } from "@/features/match-details/skills-comparison-card";
import { ApiClientError } from "@/lib/api/error";
import type { MatchDetailsResponse } from "@/lib/api/types/employer";
import { useMatchDetailsQuery } from "@/lib/employer/hooks";

type CandidateProfileViewProps = Readonly<{ candidateId: string; vacancyId: string; enabled: boolean }>;

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError ? error.message : "Match details could not be loaded. Please try again.";
}

function sourceLabel(sourceType: string): string {
  if (sourceType === "github_repository") return "GitHub";
  if (sourceType === "resume") return "Résumé";
  return sourceType.replaceAll("_", " ");
}

function MatchDetailsSkeleton() {
  return <div className="space-y-6" role="status" aria-label="Loading candidate profile"><SkeletonCard className="min-h-56" /><div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"><SkeletonCard className="min-h-80" /><div className="space-y-4"><SkeletonListRow /><SkeletonListRow /><SkeletonListRow /></div></div></div>;
}

function MatchHero({ details }: Readonly<{ details: MatchDetailsResponse }>) {
  const sources = [...new Set(details.evidence.map((item) => item.source_type))];
  return <section aria-labelledby="candidate-profile-title" className="rounded-card border border-primary/15 bg-gradient-to-br from-primary/10 via-background to-cyan-50 p-6 shadow-card sm:p-7"><div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><Badge variant="success">Match evaluated</Badge>{sources.map((source) => <Badge key={source} variant="neutral">{sourceLabel(source)}</Badge>)}</div><h1 id="candidate-profile-title" className="mt-4 break-words text-3xl font-semibold tracking-[-0.035em] text-ink sm:text-4xl">{details.candidate.name}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-secondary">{details.candidate.headline?.trim() || "Candidate match profile for this vacancy."}</p><p className="mt-5 text-sm text-secondary"><span className="font-medium text-ink">{details.evidence.length}</span> evidence {details.evidence.length === 1 ? "source supports" : "sources support"} this evaluation.</p></div><div className="w-full max-w-sm shrink-0 rounded-2xl border border-primary/15 bg-background/90 px-5 py-4"><div className="flex items-center gap-4"><div className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-success/25 bg-success/10 text-xl font-semibold tabular-nums text-success" aria-label={`Overall match ${details.match.score} percent`}>{details.match.score}%</div><div><p className="text-sm font-medium text-ink">Overall match</p><p className="mt-1 text-sm text-secondary">Based on vacancy requirements and verified skills</p></div></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-subtle" role="progressbar" aria-label="Overall match score" aria-valuemin={0} aria-valuemax={100} aria-valuenow={details.match.score}><div className="h-full rounded-full bg-success" style={{ width: `${details.match.score}%` }} /></div></div></div></section>;
}

function MatchSummary({ details }: Readonly<{ details: MatchDetailsResponse }>) {
  const missing = [...details.match.required.missing, ...details.match.preferred.missing];
  return <Card aria-labelledby="match-summary-title" className="bg-background"><CardContent className="p-5"><h2 id="match-summary-title" className="text-lg font-semibold tracking-tight text-ink">Match summary</h2><dl className="mt-5 space-y-4 text-sm"><div><dt className="text-secondary">Required skills matched</dt><dd className="mt-1 font-medium text-ink">{details.match.required.matched.length} of {details.match.required.matched.length + details.match.required.missing.length}</dd></div><div><dt className="text-secondary">Evidence signals</dt><dd className="mt-1 font-medium text-ink">{details.evidence.length} linked sources</dd></div><div><dt className="text-secondary">Needs attention</dt><dd className="mt-1 text-ink">{missing.length > 0 ? missing.slice(0, 3).join(", ") : "No missing skills reported"}</dd></div></dl>{details.passport.top_skills.length > 0 ? <div className="mt-5 border-t border-border pt-4"><p className="text-sm font-medium text-ink">Candidate strengths</p><ul className="mt-3 flex flex-wrap gap-2">{details.passport.top_skills.map((skill) => <li key={skill}><Badge variant="primary">{skill}</Badge></li>)}</ul></div> : null}</CardContent></Card>;
}

export function CandidateProfileView({ candidateId, vacancyId, enabled }: CandidateProfileViewProps) {
  const detailsQuery = useMatchDetailsQuery(candidateId, vacancyId, enabled);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);

  const evidenceCountBySkill = useMemo(() => {
    const counts = new Map<string, number>();
    detailsQuery.data?.evidence.forEach((item) => item.skills.forEach((skill) => counts.set(skill, (counts.get(skill) ?? 0) + 1)));
    return counts;
  }, [detailsQuery.data]);

  const backLink = <Link href="/" className="app-link">← Back to employer workspace</Link>;
  if (!enabled) return <EmptyState title="Employer access required" description="Match details are available only to employer accounts." />;
  if (detailsQuery.isLoading) return <div className="space-y-8"><PageHeader title="Candidate match" breadcrumb={backLink} /><MatchDetailsSkeleton /></div>;
  if (detailsQuery.isError || !detailsQuery.data) return <div className="space-y-8"><PageHeader title="Candidate match" breadcrumb={backLink} /><EmptyState role="alert" title="Match details unavailable" description={errorMessage(detailsQuery.error)} primaryAction={<Button variant="secondary" onClick={() => void detailsQuery.refetch()}>Try again</Button>} secondaryAction={backLink} /></div>;

  const details = detailsQuery.data;
  const partialGroup = { matched: details.match.preferred.matched, missing: [] };
  const missingGroup = { matched: [], missing: [...details.match.required.missing, ...details.match.preferred.missing] };

  return <div className="space-y-8"><div className="text-sm">{backLink}</div><MatchHero details={details} /><div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]"><div className="space-y-6"><SkillsComparisonCard title="Skill comparison" headingId="skill-comparison-title" required={details.match.required} partial={partialGroup} missing={missingGroup} evidenceCountBySkill={evidenceCountBySkill} selectedSkill={selectedSkill} onSelectSkill={setSelectedSkill} /><EvidenceCard evidence={details.evidence} selectedSkill={selectedSkill} onClearSkill={() => setSelectedSkill(null)} /></div><aside className="space-y-6"><MatchSummary details={details} /><RoadmapCard items={details.roadmap} /><AiExplanationCard candidateId={candidateId} vacancyId={vacancyId} enabled /></aside></div></div>;
}
