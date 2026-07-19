import type { EvidenceHubSkill } from "@/lib/api/types/evidence";

export function EvidenceSkillBadges({
  skills
}: Readonly<{ skills: EvidenceHubSkill[] }>) {
  if (skills.length === 0) {
    return <p className="text-sm text-secondary">No linked skills yet.</p>;
  }

  return (
    <ul className="flex flex-wrap gap-2" aria-label="Linked skills">
      {skills.map((skill) => (
        <li
          key={skill.id}
          className="rounded-button border border-border bg-background px-2.5 py-1 text-xs font-medium text-ink"
        >
          {skill.name}
        </li>
      ))}
    </ul>
  );
}
