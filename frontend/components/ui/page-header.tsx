import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  breadcrumb?: ReactNode;
  className?: string;
  titleId?: string;
};

export function PageHeader({
  title,
  description,
  actions,
  breadcrumb,
  className,
  titleId
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 border-b border-border/80 pb-7 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="min-w-0 space-y-2">
        {breadcrumb ? <div className="text-sm text-secondary">{breadcrumb}</div> : null}
        <h1 id={titleId} className="text-3xl font-semibold tracking-[-0.035em] text-ink sm:text-4xl">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-sm leading-6 text-secondary">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-3">{actions}</div>
      ) : null}
    </header>
  );
}
