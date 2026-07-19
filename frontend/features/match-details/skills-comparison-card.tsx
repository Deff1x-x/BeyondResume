import type { MatchSkillGroup } from "@/lib/api/types/employer";

type SkillsComparisonCardProps = Readonly<{
  title: string;
  headingId: string;
  group: MatchSkillGroup;
}>;

export function SkillsComparisonCard({ title, headingId, group }: SkillsComparisonCardProps) {
  return (
    <section
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby={headingId}
    >
      <h2 id={headingId} className="text-base font-semibold text-ink">
        {title}
      </h2>

      <div className="mt-5 grid gap-6 sm:grid-cols-2">
        <SkillList label="Matched" skills={group.matched} tone="matched" />
        <SkillList label="Missing" skills={group.missing} tone="missing" />
      </div>
    </section>
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
  const marker = tone === "matched" ? "✓" : "✗";
  const markerClass = tone === "matched" ? "text-success" : "text-danger";

  return (
    <div>
      <h3 className="text-sm font-medium text-ink">{label}</h3>
      {skills.length === 0 ? (
        <p className="mt-2 text-sm text-secondary">None</p>
      ) : (
        <ul className="mt-2 space-y-2" aria-label={label}>
          {skills.map((skill) => (
            <li key={skill} className="flex items-start gap-2 text-sm text-ink">
              <span aria-hidden="true" className={markerClass}>
                {marker}
              </span>
              <span>{skill}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
