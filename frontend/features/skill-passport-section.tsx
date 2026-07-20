"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

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
  if (sourceType === "resume") return "Résumé";
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

function confirmationCopy(skill: SkillPassportSkill): string {
  const sources = uniqueSources(skill).map(sourceTypeLabel);
  if (sources.length === 0) return "Confirmed by collected evidence";
  if (sources.length === 1) return `Confirmed by ${sources[0]}`;
  if (sources.length === 2) return `Confirmed by ${sources[0]} and ${sources[1]}`;
  return `Confirmed by ${sources.length} connected sources`;
}

function safeDetailId(name: string): string {
  return `skill-evidence-${name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`;
}

function EvidenceDetail({ evidence }: Readonly<{ evidence: SkillPassportEvidence }>) {
  const title = evidence.title ?? evidence.source_reference ?? "Evidence";
  const hasSafeLink = Boolean(evidence.source_reference?.startsWith("https://"));

  return (
    <li className="rounded-xl border border-border bg-surface/70 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="min-w-0 break-words text-sm font-medium text-ink">{title}</p>
        <Badge variant="neutral">{sourceTypeLabel(evidence.source_type)}</Badge>
      </div>
      {evidence.source_reference ? (
        <p className="mt-2 break-all text-sm text-secondary">
          {hasSafeLink ? (
            <a
              href={evidence.source_reference}
              target="_blank"
              rel="noreferrer"
              className="app-link"
            >
              Open source
            </a>
          ) : (
            evidence.source_reference
          )}
        </p>
      ) : null}
      {evidence.description ? <p className="mt-2 text-sm leading-6 text-secondary">{evidence.description}</p> : null}
    </li>
  );
}

function SkillCard({ skill }: Readonly<{ skill: SkillPassportSkill }>) {
  const [expanded, setExpanded] = useState(false);
  const sources = uniqueSources(skill);
  const strength = strengthFor(skill.evidence_confidence);
  const detailId = safeDetailId(skill.name);
  const strengthClass: Record<Strength, string> = {
    strong: "bg-success",
    moderate: "bg-primary",
    limited: "bg-muted"
  };

  return (
    <li className="group rounded-card border border-border bg-background p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-base font-semibold text-ink">{skill.name}</p>
          <p className="mt-1 text-sm text-secondary">{categoryLabels[skill.category] ?? skill.category}</p>
        </div>
        <Badge variant={strength === "strong" ? "success" : strength === "moderate" ? "primary" : "neutral"}>
          {strength}
        </Badge>
      </div>

      <div className="mt-5">
        <div className="flex items-center justify-between gap-3 text-xs font-medium text-secondary">
          <span>{strengthCopy(skill.evidence_confidence)}</span>
          <span>{skill.evidence_count} {skill.evidence_count === 1 ? "evidence unit" : "evidence units"}</span>
        </div>
        <div
          className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-subtle"
          role="progressbar"
          aria-label={`${skill.name} evidence strength`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(skill.evidence_confidence * 100)}
        >
          <div className={`h-full rounded-full ${strengthClass[strength]}`} style={{ width: `${Math.round(skill.evidence_confidence * 100)}%` }} />
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-secondary">{confirmationCopy(skill)}.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {sources.map((source) => <Badge key={source} variant="neutral">{sourceTypeLabel(source)}</Badge>)}
      </div>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className="mt-5"
        onClick={() => setExpanded((open) => !open)}
        aria-expanded={expanded}
        aria-controls={detailId}
      >
        {expanded ? "Hide evidence" : "View evidence"}
      </Button>

      {expanded ? (
        <section id={detailId} className="mt-5 border-t border-border pt-4" aria-label={`Evidence for ${skill.name}`}>
          <p className="text-sm font-medium text-ink">Evidence supporting {skill.name}</p>
          <ul className="mt-3 space-y-3">
            {skill.evidence.map((evidence) => <EvidenceDetail key={`${skill.name}-${evidence.source_reference ?? evidence.title ?? evidence.source_type}`} evidence={evidence} />)}
          </ul>
        </section>
      ) : null}
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
      title="Build your evidence-based skill passport"
      description="Connect a repository or upload a résumé to collect evidence and confirm the skills behind your work."
      primaryAction={<Link href="/#github-section-title" className="inline-flex min-h-control items-center rounded-button bg-primary px-4 text-sm font-medium text-white shadow-sm shadow-primary/25 transition hover:-translate-y-px focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Connect GitHub</Link>}
      secondaryAction={<Link href="/#resume-section-title" className="inline-flex min-h-control items-center rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink transition hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">Upload résumé</Link>}
    />
  );
}

export function SkillPassportWorkspace() {
  const passportQuery = useSkillPassportQuery(true);
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const passport = passportQuery.data;

  const categories = useMemo(
    () => [...new Set(passport?.skills.map((skill) => skill.category) ?? [])].sort(),
    [passport]
  );
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
          <Metric label="Sources connected" value={metrics.sourceCount} detail="GitHub, résumé, or other verified sources" />
          <Metric label="Strongest category" value={metrics.strongestCategory ? categoryLabels[metrics.strongestCategory[0]] ?? metrics.strongestCategory[0] : "—"} detail={metrics.strongestCategory ? `${metrics.strongestCategory[1]} confirmed skills` : "No category data yet"} />
        </div>
        <div className="mt-8 rounded-card border border-border bg-surface/80 p-4 sm:p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div><h2 className="text-lg font-semibold text-ink">Explore confirmed skills</h2><p className="mt-1 text-sm text-secondary">Filter by evidence source or category, then open the source behind each skill.</p></div>
            <div className="w-full lg:max-w-xs"><label htmlFor="skill-passport-search" className="sr-only">Search confirmed skills</label><Input id="skill-passport-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search skills" /></div>
          </div>
          <div className="mt-5 flex flex-wrap gap-2" aria-label="Evidence source filters">
            {([['all', 'All'], ['github', 'GitHub'], ['resume', 'Résumé'], ['multiple', 'Multiple sources']] as const).map(([value, label]) => <Button key={value} type="button" size="sm" variant={sourceFilter === value ? "primary" : "secondary"} onClick={() => setSourceFilter(value)} aria-pressed={sourceFilter === value}>{label}</Button>)}
          </div>
          {categories.length > 0 ? <div className="mt-3 flex flex-wrap gap-2" aria-label="Skill category filters"><Button type="button" size="sm" variant={categoryFilter === "all" ? "primary" : "secondary"} onClick={() => setCategoryFilter("all")} aria-pressed={categoryFilter === "all"}>All categories</Button>{categories.map((category) => <Button key={category} type="button" size="sm" variant={categoryFilter === category ? "primary" : "secondary"} onClick={() => setCategoryFilter(category)} aria-pressed={categoryFilter === category}>{categoryLabels[category] ?? category}</Button>)}</div> : null}
        </div>
        {visibleSkills.length > 0 ? <ul className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{visibleSkills.map((skill) => <SkillCard key={skill.id} skill={skill} />)}</ul> : <EmptyState className="mt-6" title="No matching skills" description="Try another search term or clear one of the active filters." />}
      </> : null}
    </section>
  );
}
