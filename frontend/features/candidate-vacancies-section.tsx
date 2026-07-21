"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonCard } from "@/components/ui/skeleton";
import type { CandidateVacancy, CandidateVacancyDetail, MatchSkillGroup } from "@/lib/api/types/candidate-vacancies";
import { useCandidateVacanciesQuery, useCandidateVacancyQuery } from "@/lib/candidate-vacancies/hooks";

function SkillPreview({ skills, limit }: Readonly<{ skills: string[]; limit: number }>) {
  const visible = skills.slice(0, limit);
  return <div className="flex flex-wrap gap-2">{visible.map((skill) => <Badge key={skill} variant="neutral">{skill}</Badge>)}{skills.length > limit ? <Badge variant="neutral">+{skills.length - limit} more</Badge> : null}</div>;
}

function MatchScore({ score }: Readonly<{ score: number }>) {
  return <div className="flex items-center gap-3"><span className="flex h-12 w-12 items-center justify-center rounded-full border-4 border-success/25 bg-success/10 text-sm font-semibold tabular-nums text-success" aria-label={`${score}% match`}>{score}%</span><span className="text-sm font-medium text-ink">Match</span></div>;
}

const buttonLinkClass = "inline-flex min-h-9 items-center justify-center rounded-button border border-primary bg-gradient-to-b from-indigo-500 to-primary px-3 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px hover:from-indigo-400 hover:to-primary hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2";

export function CandidateVacancyCard({ vacancy }: Readonly<{ vacancy: CandidateVacancy }>) {
  const missing = [...vacancy.match.required.missing, ...vacancy.match.preferred.missing];
  return <Card><CardContent className="space-y-5 p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-sm text-secondary">{vacancy.company_name}</p><h2 className="mt-1 text-xl font-semibold tracking-tight text-ink">{vacancy.title}</h2></div><MatchScore score={vacancy.match.score} /></div>{vacancy.description ? <p className="line-clamp-2 text-sm leading-6 text-secondary">{vacancy.description}</p> : null}<div><p className="mb-2 text-xs font-semibold uppercase tracking-wide text-secondary">Required · {vacancy.required_skills.length}</p><SkillPreview skills={vacancy.required_skills} limit={3} /></div><div><p className="mb-2 text-xs font-semibold uppercase tracking-wide text-secondary">Missing</p>{missing.length > 0 ? <SkillPreview skills={missing} limit={2} /> : <p className="text-sm text-success">All listed skills are currently confirmed.</p>}</div></CardContent><CardFooter><Link href={`/vacancies/${vacancy.id}`} className={buttonLinkClass}>View details</Link><span className="text-sm text-secondary">{vacancy.preferred_skills.length} preferred skills</span></CardFooter></Card>;
}

export function CandidateVacanciesPreview() {
  const query = useCandidateVacanciesQuery(true);
  if (query.isLoading) return <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading recommended vacancies"><SkeletonCard className="min-h-72" /><SkeletonCard className="min-h-72" /><SkeletonCard className="min-h-72" /></div>;
  if (query.isError) return <EmptyState role="alert" title="Vacancies could not be loaded" description="Please try again." primaryAction={<Button variant="secondary" onClick={() => void query.refetch()}>Try again</Button>} />;
  if (!query.data || query.data.length === 0) return <EmptyState title="No vacancies available yet." description="Check back soon for roles that can be evaluated against your verified skills." />;
  return <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">{query.data.slice(0, 3).map((vacancy) => <CandidateVacancyCard key={vacancy.id} vacancy={vacancy} />)}</div>;
}

export function CandidateVacanciesWorkspace() {
  const query = useCandidateVacanciesQuery(true);
  if (query.isLoading) return <div className="grid gap-5 lg:grid-cols-2"><SkeletonCard className="min-h-72" /><SkeletonCard className="min-h-72" /></div>;
  if (query.isError) return <EmptyState role="alert" title="Vacancies could not be loaded" description="Please try again." primaryAction={<Button variant="secondary" onClick={() => void query.refetch()}>Try again</Button>} />;
  if (!query.data || query.data.length === 0) return <EmptyState title="No vacancies available yet." description="Check back soon for roles that can be evaluated against your verified skills." />;
  return <div className="grid gap-5 lg:grid-cols-2">{query.data.map((vacancy) => <CandidateVacancyCard key={vacancy.id} vacancy={vacancy} />)}</div>;
}

function SkillGroup({ title, group, missing }: Readonly<{ title: string; group: MatchSkillGroup; missing?: boolean }>) {
  const skills = missing ? group.missing : group.matched;
  return <section><h2 className="text-sm font-semibold text-ink">{title}</h2>{skills.length > 0 ? <div className="mt-3 flex flex-wrap gap-2">{skills.map((skill) => <Badge key={skill} variant={missing ? "warning" : "success"}>{skill}</Badge>)}</div> : <p className="mt-2 text-sm text-secondary">None</p>}</section>;
}

function VacancyDetailContent({ vacancy }: Readonly<{ vacancy: CandidateVacancyDetail }>) {
  return <div className="space-y-6"><section className="rounded-card border border-primary/15 bg-gradient-to-br from-primary/10 via-background to-cyan-50 p-6"><div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-sm text-secondary">{vacancy.company_name}</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-ink">{vacancy.title}</h1>{vacancy.description ? <p className="mt-4 max-w-3xl text-sm leading-6 text-secondary">{vacancy.description}</p> : null}</div><MatchScore score={vacancy.match.score} /></div></section><div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"><div className="space-y-6"><Card><CardContent className="grid gap-6 p-5 sm:grid-cols-2"><section><h2 className="text-sm font-semibold text-ink">Required skills</h2><div className="mt-3"><SkillPreview skills={vacancy.required_skills} limit={vacancy.required_skills.length} /></div></section><section><h2 className="text-sm font-semibold text-ink">Preferred skills</h2><div className="mt-3"><SkillPreview skills={vacancy.preferred_skills} limit={vacancy.preferred_skills.length} /></div></section></CardContent></Card><Card><CardContent className="grid gap-6 p-5 sm:grid-cols-2"><SkillGroup title="Matched skills" group={{ matched: [...vacancy.match.required.matched, ...vacancy.match.preferred.matched], missing: [] }} /><SkillGroup title="Missing required skills" group={vacancy.match.required} missing /><SkillGroup title="Missing preferred skills" group={vacancy.match.preferred} missing /></CardContent></Card></div><Card><CardContent className="p-5"><h2 className="text-lg font-semibold text-ink">Vacancy Roadmap</h2>{vacancy.roadmap.length > 0 ? <ol className="mt-4 space-y-4">{vacancy.roadmap.map((item) => <li key={item.id} className="border-t border-border pt-4 first:border-t-0 first:pt-0"><Badge variant={item.priority === "high" ? "warning" : "neutral"}>{item.priority}</Badge><p className="mt-2 text-sm font-medium text-ink">{item.title}</p><p className="mt-1 text-sm leading-6 text-secondary">{item.reason}</p></li>)}</ol> : <p className="mt-3 text-sm text-secondary">No skill gaps were identified for this vacancy.</p>}</CardContent></Card></div></div>;
}

export function CandidateVacancyDetailWorkspace({ vacancyId }: Readonly<{ vacancyId: string }>) {
  const query = useCandidateVacancyQuery(vacancyId, true);
  if (query.isLoading) return <SkeletonCard className="min-h-96" />;
  if (query.isError || !query.data) return <EmptyState role="alert" title="Vacancy could not be loaded" description="It may no longer be available." primaryAction={<Link href="/vacancies" className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Back to vacancies</Link>} />;
  return <VacancyDetailContent vacancy={query.data} />;
}
