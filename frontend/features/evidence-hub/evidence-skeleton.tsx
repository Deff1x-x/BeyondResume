import { SkeletonListRow } from "@/components/ui/skeleton";

export function EvidenceSkeleton() {
  return (
    <ul className="space-y-3" aria-hidden="true">
      <li>
        <SkeletonListRow />
      </li>
      <li>
        <SkeletonListRow />
      </li>
      <li>
        <SkeletonListRow />
      </li>
    </ul>
  );
}
