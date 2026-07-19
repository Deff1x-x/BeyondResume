import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type EmptyStateProps = {
  title: string;
  description?: string;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
  icon?: ReactNode;
  className?: string;
  role?: "status" | "alert";
};

export function EmptyState({
  title,
  description,
  primaryAction,
  secondaryAction,
  icon,
  className,
  role = "status"
}: EmptyStateProps) {
  return (
    <div
      role={role}
      className={cn(
        "rounded-card border border-border bg-background px-4 py-8 text-center",
        className
      )}
    >
      {icon ? (
        <div className="mx-auto mb-3 flex h-9 w-9 items-center justify-center text-muted" aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <p className="text-sm font-medium text-ink">{title}</p>
      {description ? (
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-secondary">
          {description}
        </p>
      ) : null}
      {primaryAction || secondaryAction ? (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
          {primaryAction}
          {secondaryAction}
        </div>
      ) : null}
    </div>
  );
}
