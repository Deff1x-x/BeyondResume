import { cn } from "@/lib/cn";

type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn("animate-pulse rounded-button bg-border/80", className)}
      aria-hidden="true"
    />
  );
}

export function SkeletonText({ className }: SkeletonProps) {
  return <Skeleton className={cn("h-3 w-full", className)} />;
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-card border border-border bg-background p-4",
        className
      )}
      aria-hidden="true"
    >
      <Skeleton className="h-4 w-32" />
      <SkeletonText className="mt-3 w-full" />
      <SkeletonText className="mt-2 w-2/3" />
      <div className="mt-4 flex gap-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
      </div>
    </div>
  );
}

export function SkeletonListRow({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "flex items-start justify-between gap-3 rounded-card border border-border bg-background px-4 py-4",
        className
      )}
      aria-hidden="true"
    >
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-40" />
        <SkeletonText className="w-full" />
        <SkeletonText className="w-1/2" />
      </div>
      <Skeleton className="h-3 w-16 shrink-0" />
    </div>
  );
}
