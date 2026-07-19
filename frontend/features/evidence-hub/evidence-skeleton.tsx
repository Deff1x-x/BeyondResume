export function EvidenceSkeleton() {
  return (
    <ul className="space-y-3" aria-hidden="true">
      {Array.from({ length: 3 }, (_, index) => (
        <li
          key={index}
          className="animate-pulse rounded-card border border-border bg-background px-4 py-4"
        >
          <div className="flex items-center justify-between gap-3">
            <div className="h-4 w-40 rounded bg-border" />
            <div className="h-3 w-20 rounded bg-border" />
          </div>
          <div className="mt-3 h-3 w-full rounded bg-border" />
          <div className="mt-2 h-3 w-2/3 rounded bg-border" />
          <div className="mt-4 flex gap-2">
            <div className="h-6 w-16 rounded bg-border" />
            <div className="h-6 w-20 rounded bg-border" />
          </div>
        </li>
      ))}
    </ul>
  );
}
