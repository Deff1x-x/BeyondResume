"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { SkeletonCard } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api/error";
import type { SkillPassportEvidence, SkillPassportSkill } from "@/lib/api/types/skill-passport";
import { useSkillPassportQuery } from "@/lib/skill-passport/hooks";

type SourceFilter = "all" | "github" | "resume" | "multiple";
type Strength = "strong" | "moderate" | "limited";

const categoryLabels: Record<string, string> = {
  language: "Languages",
  frontend: "Frontend",
  backend: "Backend",
  database: "Databases",
  infrastructure: "Tools",
  testing: "Testing",
  data_ai: "Data & AI"
};

function errorMessage(error: unknown): string {
  return error instanceof ApiClientError
    ? error.message
    : "The skill passport could not be loaded. Please try again.";
}

function sourceTypeLabel(sourceType: string): string {
  if (sourceType === "github_repository") return "GitHub";
  if (sourceType === "resume") return "Resume";
  return sourceType.replaceAll("_", " ");
}

function strengthFor(confidence: number): Strength {
  if (confidence >= 0.8) return "strong";
  if (confidence >= 0.5) return "moderate";
  return "limited";
}

function strengthCopy(confidence: number): string {
  return `${Math.round(confidence * 100)}% evidence strength`;
}

function uniqueSources(skill: SkillPassportSkill): string[] {
  return [...new Set(skill.evidence.map((item) => item.source_type))];
}

function EvidenceDetail({ evidence }: Readonly<{ evidence: SkillPassportEvidence }>) {
  const title = evidence.title ?? evidence.source_reference ?? "Evidence";
  const hasSafeLink = Boolean(evidence.source_reference?.startsWith("https://"));

  return (
    <li className="border-t border-border py-4 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="min-w-0 break-words text-sm font-medium text-ink">{title}</p>
        <Badge variant="neutral">{sourceTypeLabel(evidence.source_type)}</Badge>
      </div>
      {evidence.source_reference ? (
        <p className="mt-2 break-all text-sm text-secondary">
          {hasSafeLink ? <a href={evidence.source_reference} target="_blank" rel="noreferrer" className="app-link">Open source</a> : evidence.source_reference}
        </p>
      ) : null}
      {evidence.description ? <p className="mt-2 text-sm leading-6 text-secondary">{evidence.description}</p> : null}
    </li>
  );
}

function SkillEvidenceDialog({ skill, onClose }: Readonly<{ skill: SkillPassportSkill | null; onClose: () => void }>) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (skill && !dialog.open) {
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    if (!skill && dialog.open) {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    }
  }, [skill]);

  function closeDialog() {
    const dialog = dialogRef.current;
    if (typeof dialog?.close === "function") dialog.close();
    else onClose();
  }

  return (
    <dialog
      ref={dialogRef}
      className="m-auto max-h-[min(44rem,calc(100vh-2rem))] w-[min(42rem,calc(100vw-2rem))] overflow-y-auto rounded-dialog border border-border bg-surface p-0 text-ink shadow-float backdrop:bg-ink/40"
      aria-labelledby={skill ? `evidence-dialog-${skill.id}` : undefined}
      onClose={onClose}
    >
      {skill ? (
        <div className="p-5 sm:p-7">
          <div className="flex items-start justify-between gap-5 border-b border-border pb-5">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Evidence details</p>
              <h2 id={`evidence-dialog-${skill.id}`} className="mt-1 break-words text-2xl font-semibold tracking-tight text-ink">{skill.name}</h2>
              <p className="mt-2 text-sm text-secondary">{strengthCopy(skill.evidence_confidence)} · {skill.evidence_count} {skill.evidence_count === 1 ? "evidence unit" : "evidence units"}</p>
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={closeDialog} autoFocus>Close</Button>
          </div>

          <section className="mt-6" aria-labelledby={`evidence-sources-${skill.id}`}>
            <h3 id={`evidence-sources-${skill.id}`} className="text-sm font-semibold text-ink">Evidence sources</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {uniqueSources(skill).map((source) => <Badge key={source} variant="neutral">{sourceTypeLabel(source)}</Badge>)}
            </div>
          </section>

          {skill.github_repositories.length > 0 ? (
            <section className="mt-6" aria-labelledby={`repository-evidence-${skill.id}`}>
              <h3 id={`repository-evidence-${skill.id}`} className="text-sm font-semibold text-ink">GitHub repositories</h3>
              <ul className="mt-3 divide-y divide-border rounded-xl border border-border bg-background px-4">
                {skill.github_repositories.map((repository) => (
                  <li key={repository.repository_url} className="py-4 first:pt-4">
                    <a href={repository.repository_url} target="_blank" rel="noreferrer" className="app-link break-all text-sm">{repository.repository_name}</a>
                    <p className="mt-1 text-sm text-secondary">{repository.evidence_count} {repository.evidence_count === 1 ? "evidence unit" : "evidence units"}</p>
                    <p className="mt-1 text-sm font-medium text-ink">{repository.repository_confidence}% evidence in this repository</p>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs leading-5 text-secondary">Evidence in each repository is evaluated independently and does not add up to the overall confidence.</p>
            </section>
          ) : null}

          <section className="mt-6" aria-labelledby={`source-evidence-${skill.id}`}>
            <h3 id={`source-evidence-${skill.id}`} className="text-sm font-semibold text-ink">Source-specific evidence</h3>
            <ul className="mt-3 divide-y divide-border">
              {skill.evidence.map((evidence) => <EvidenceDetail key={`${skill.id}-${evidence.id}`} evidence={evidence} />)}
            </ul>
          </section>
        </div>
      ) : null}
    </dialog>
  );
}

function SkillCard({ skill, onOpenEvidence }: Readonly<{ skill: SkillPassportSkill; onOpenEvidence: (skill: SkillPassportSkill) => void }>) {
  const sources = uniqueSources(skill);
  const strength = strengthFor(skill.evidence_confidence);
  const strengthClass: Record<Strength, string> = { strong: "bg-success", moderate: "bg-primary", limited: "bg-muted" };
  const badgeVariant = strength === "strong" ? "success" : strength === "moderate" ? "primary" : "neutral";

  return (
    <li className="flex min-h-72 flex-col rounded-card border border-border bg-background p-5 shadow-card sm:p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="break-words text-lg font-semibold tracking-tight text-ink">{skill.name}</h3>
          <p className="mt-1 text-sm text-secondary">{categoryLabels[skill.category] ?? skill.category}</p>
        </div>
        <Badge variant={badgeVariant}>Confirmed</Badge>
      </div>

      <div className="mt-6">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-4xl font-semibold tracking-[-0.05em] text-ink">{Math.round(skill.evidence_confidence * 100)}%</p>
            <p className="mt-1 text-sm text-secondary">Evidence strength</p>
          </div>
          <Badge variant={badgeVariant}>{strength}</Badge>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-subtle" role="progressbar" aria-label={`${skill.name} evidence strength`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(skill.evidence_confidence * 100)}>
          <div className={`h-full rounded-full ${strengthClass[strength]}`} style={{ width: `${Math.round(skill.evidence_confidence * 100)}%` }} />
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Evidence sources</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {sources.map((source) => <Badge key={source} variant="neutral">{sourceTypeLabel(source)}</Badge>)}
        </div>
      </div>

      <Button type="button" variant="secondary" size="sm" className="mt-auto self-start pt-5" onClick={() => onOpenEvidence(skill)} aria-haspopup="dialog">
        Open evidence
      </Button>
    </li>
  );
}

function Metric({ label, value, detail }: Readonly<{ label: string; value: string | number; detail: string }>) {
  return <Card className="bg-background"><CardContent className="p-4"><p className="text-sm text-secondary">{label}</p><p className="mt-2 text-2xl font-semibold tracking-tight text-ink">{value}</p><p className="mt-1 text-xs leading-5 text-muted">{detail}</p></CardContent></Card>;
}

function PassportEmptyState() {
  return (
    <EmptyState
      className="py-12"
      icon={<Icon name="passport" className="h-7 w-7" />}
      title="No verified skills yet"
      description="Connect GitHub or upload evidence to begin building your Skill Passport."
      primaryAction={<Link href="/#github-section-title" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Connect GitHub</Link>}
      secondaryAction={<Link href="/#resume-section-title" className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Upload resume</Link>}
    />
  );
}

export function SkillPassportWorkspace() {
  const passportQuery = useSkillPassportQuery(true);
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [selectedSkill, setSelectedSkill] = useState<SkillPassportSkill | null>(null);
  const passport = passportQuery.data;

  const categories = useMemo(() => [...new Set(passport?.skills.map((skill) => skill.category) ?? [])].sort(), [passport]);
  const metrics = useMemo(() => {
    if (!passport) return null;
    const allSources = new Set(passport.skills.flatMap(uniqueSources));
    const categoryCounts = new Map<string, number>();
    passport.skills.forEach((skill) => categoryCounts.set(skill.category, (categoryCounts.get(skill.category) ?? 0) + 1));
    const strongestCategory = [...categoryCounts.entries()].sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))[0];
    return { sourceCount: allSources.size, strongestCategory };
  }, [passport]);
  const visibleSkills = useMemo(() => {
    if (!passport) return [];
    const normalizedSearch = search.trim().toLowerCase();
    return passport.skills.filter((skill) => {
      const sources = uniqueSources(skill);
      const sourceMatches = sourceFilter === "all" || (sourceFilter === "github" && sources.includes("github_repository")) || (sourceFilter === "resume" && sources.includes("resume")) || (sourceFilter === "multiple" && sources.length > 1);
      return sourceMatches && (categoryFilter === "all" || skill.category === categoryFilter) && (!normalizedSearch || skill.name.toLowerCase().includes(normalizedSearch));
    });
  }, [categoryFilter, passport, search, sourceFilter]);

  return (
    <section aria-labelledby="skill-passport-title">
      {passportQuery.isLoading ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" role="status" aria-label="Loading skill passport"><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></div> : null}
      {passportQuery.isError ? <EmptyState role="alert" title="Skill Passport unavailable" description={errorMessage(passportQuery.error)} primaryAction={<Button variant="secondary" onClick={() => void passportQuery.refetch()}>Try again</Button>} /> : null}
      {passport && passport.skills.length === 0 ? <PassportEmptyState /> : null}
      {passport && passport.skills.length > 0 && metrics ? <>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Confirmed skills" value={passport.total_skills} detail="Skills with supporting evidence" />
          <Metric label="Evidence units" value={passport.total_evidence} detail="Distinct pieces of supporting work" />
          <Metric label="Sources connected" value={metrics.sourceCount} detail="GitHub, resume, or other verified sources" />
          <Metric label="Strongest category" value={metrics.strongestCategory ? categoryLabels[metrics.strongestCategory[0]] ?? metrics.strongestCategory[0] : "—"} detail={metrics.strongestCategory ? `${metrics.strongestCategory[1]} confirmed skills` : "No category data yet"} />
        </div>
        <div className="mt-8 rounded-card border border-border bg-surface/90 p-5 sm:p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div><h2 className="text-xl font-semibold tracking-tight text-ink">Explore confirmed skills</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-secondary">Filter by source or category, then open evidence only when you need its technical detail.</p></div>
            <div className="w-full lg:max-w-xs"><label htmlFor="skill-passport-search" className="sr-only">Search confirmed skills</label><Input id="skill-passport-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search skills" /></div>
          </div>
          <div className="mt-6"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Evidence source</p><div className="mt-3 flex flex-wrap gap-2" aria-label="Evidence source filters">
            {([['all', 'All'], ['github', 'GitHub'], ['resume', 'Resume'], ['multiple', 'Multiple sources']] as const).map(([value, label]) => <Button key={value} type="button" size="sm" variant={sourceFilter === value ? "primary" : "secondary"} onClick={() => setSourceFilter(value)} aria-pressed={sourceFilter === value}>{label}</Button>)}
          </div></div>
          {categories.length > 0 ? <div className="mt-5"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-secondary">Category</p><div className="mt-3 flex flex-wrap gap-2" aria-label="Skill category filters"><Button type="button" size="sm" variant={categoryFilter === "all" ? "primary" : "secondary"} onClick={() => setCategoryFilter("all")} aria-pressed={categoryFilter === "all"}>All categories</Button>{categories.map((category) => <Button key={category} type="button" size="sm" variant={categoryFilter === category ? "primary" : "secondary"} onClick={() => setCategoryFilter(category)} aria-pressed={categoryFilter === category}>{categoryLabels[category] ?? category}</Button>)}</div></div> : null}
        </div>
        {visibleSkills.length > 0 ? <ul className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{visibleSkills.map((skill) => <SkillCard key={skill.id} skill={skill} onOpenEvidence={setSelectedSkill} />)}</ul> : <EmptyState className="mt-6" title="No matching skills" description="Try another search term or clear one of the active filters." />}
        <SkillEvidenceDialog skill={selectedSkill} onClose={() => setSelectedSkill(null)} />
      </> : null}
    </section>
  );
}
