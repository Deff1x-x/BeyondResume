import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/ui/section-header";
import type { MatchSkillGroup } from "@/lib/api/types/employer";

type SkillsComparisonCardProps = Readonly<{
  title: string;
  headingId: string;
  group: MatchSkillGroup;
}>;

export function SkillsComparisonCard({ title, headingId, group }: SkillsComparisonCardProps) {
  return (
    <Card aria-labelledby={headingId}>
      <CardContent className="space-y-5 p-5 sm:p-6">
        <SectionHeader title={title} titleId={headingId} size="md" />

        <div className="grid gap-6 sm:grid-cols-2">
          <SkillList label="Matched" skills={group.matched} tone="matched" />
          <SkillList label="Missing" skills={group.missing} tone="missing" />
        </div>
      </CardContent>
    </Card>
  );
}

function SkillList({
  label,
  skills,
  tone
}: Readonly<{
  label: string;
  skills: string[];
  tone: "matched" | "missing";
}>) {
  return (
    <div>
      <h3 className="flex flex-wrap items-center gap-2 text-sm font-medium text-ink">
        <Badge variant={tone === "matched" ? "success" : "danger"}>{label}</Badge>
        <span className="text-secondary">{skills.length}</span>
      </h3>
      {skills.length === 0 ? (
        <p className="mt-2 text-sm text-secondary">None</p>
      ) : (
        <ul className="mt-2 space-y-2" aria-label={label}>
          {skills.map((skill) => (
            <li key={skill} className="break-words text-sm text-ink">
              <span className="sr-only">{tone === "matched" ? "Matched: " : "Missing: "}</span>
              {skill}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
