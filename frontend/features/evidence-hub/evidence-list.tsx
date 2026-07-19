import type { EvidenceHubItem } from "@/lib/api/types/evidence";

import { EvidenceCard } from "./evidence-card";

export function EvidenceList({ items }: Readonly<{ items: EvidenceHubItem[] }>) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.id}>
          <EvidenceCard item={item} />
        </li>
      ))}
    </ul>
  );
}
