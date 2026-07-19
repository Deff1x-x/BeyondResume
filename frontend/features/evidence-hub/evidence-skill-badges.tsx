import { Badge } from "@/components/ui/badge";
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
        <li key={skill.id} className="min-w-0 max-w-full">
          <Badge variant="neutral" title={skill.name}>
            {skill.name}
          </Badge>
        </li>
      ))}
    </ul>
  );
}
