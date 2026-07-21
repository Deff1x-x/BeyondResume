import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { MatchDetailsMatch, MatchDetailsPassport, MatchDetailsPassportSkill } from "@/lib/api/types/employer";

type EmployerSkillPassportProps = Readonly<{
  passport: MatchDetailsPassport;
  match: MatchDetailsMatch;
  onSelectSkill: (skill: string) => void;
}>;

function sourceTypeLabel(sourceType: string): string {
  if (sourceType === "github_repository") return "GitHub";
  if (sourceType === "resume") return "Resume";
  return sourceType
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function relevanceFor(skill: MatchDetailsPassportSkill, match: MatchDetailsMatch): string {
  if (match.required.matched.includes(skill.name)) return "Required · Matched";
  if (match.preferred.matched.includes(skill.name)) return "Preferred · Matched";
  return "Additional skill";
}

function evidenceCountLabel(count: number): string {
  return `${count} evidence ${count === 1 ? "item" : "items"}`;
}

function SkillPassportFallback({ skills }: Readonly<{ skills: string[] }>) {
  if (skills.length === 0) {
    return <p className="mt-5 text-sm leading-6 text-secondary">No evidence-backed skills are available for this candidate.</p>;
  }

  return (
    <ul className="mt-5 space-y-3" aria-label="Candidate skills">
      {skills.map((skill) => (
        <li key={skill} className="rounded-xl border border-border bg-background px-4 py-3">
          <p className="font-medium text-ink">{skill}</p>
          <p className="mt-1 text-sm text-secondary">Confidence unavailable</p>
        </li>
      ))}
    </ul>
  );
}

export function EmployerSkillPassport({ passport, match, onSelectSkill }: EmployerSkillPassportProps) {
  const skills = passport.skills;

  return (
    <section aria-labelledby="employer-skill-passport-title">
      <Card>
        <CardContent className="p-5 sm:p-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-primary">Candidate evidence</p>
            <h2 id="employer-skill-passport-title" className="mt-2 text-xl font-semibold tracking-tight text-ink">Skill Passport</h2>
            <p className="mt-2 text-sm leading-6 text-secondary">Read-only evidence-backed skills for this candidate.</p>
          </div>

          {skills === undefined ? <SkillPassportFallback skills={passport.top_skills} /> : null}
          {skills !== undefined && skills.length === 0 ? <p className="mt-5 text-sm leading-6 text-secondary">No evidence-backed skills are available for this candidate.</p> : null}
          {skills !== undefined && skills.length > 0 ? (
            <ul className="mt-5 divide-y divide-border" aria-label="Candidate Skill Passport">
              {skills.map((skill) => {
                const percentage = Math.round(skill.evidence_confidence * 100);
                const sourceTypes = [...new Set(skill.source_types)];

                return (
                  <li key={skill.name} className="py-4 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="min-w-0">
                        <h3 className="break-words text-base font-semibold tracking-tight text-ink sm:text-lg">{skill.name}</h3>
                        <Badge className="mt-1.5" variant="primary">{relevanceFor(skill, match)}</Badge>
                      </div>
                      <div className="shrink-0 text-right">
                        <p className="text-2xl font-semibold tracking-[-0.04em] tabular-nums text-ink">{percentage}%</p>
                        <p className="mt-0.5 text-xs text-secondary">Evidence confidence</p>
                      </div>
                    </div>

                    <div
                      className="mt-3 h-2 overflow-hidden rounded-full bg-surface-subtle"
                      role="progressbar"
                      aria-label={`${skill.name} evidence confidence: ${percentage} percent`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={percentage}
                    >
                      <div className="h-full rounded-full bg-primary" style={{ width: `${percentage}%` }} />
                    </div>

                    <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-secondary">
                      <span>{evidenceCountLabel(skill.evidence_count)}</span>
                      {sourceTypes.map((sourceType) => <Badge key={sourceType} variant="neutral">{sourceTypeLabel(sourceType)}</Badge>)}
                    </div>
                    <Button type="button" variant="secondary" size="sm" className="mt-3" onClick={() => onSelectSkill(skill.name)}>View evidence</Button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
