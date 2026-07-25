import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type PageHeaderProps = {
  title: string;
  description?: string;
  eyebrow?: string;
  actions?: ReactNode;
  breadcrumb?: ReactNode;
  className?: string;
  titleId?: string;
};

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  breadcrumb,
  className,
  titleId
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-5 border-b border-border/80 pb-8 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="min-w-0 space-y-2">
        {breadcrumb ? <div className="text-sm text-secondary">{breadcrumb}</div> : null}
        {eyebrow ? (
          <p className="text-xs font-semibold tracking-wide text-ai-muted">{eyebrow}</p>
        ) : null}
        <h1 id={titleId} className="type-page-title sm:text-[2.25rem]">
          {title}
        </h1>
        {description ? (
          <p className="max-w-2xl text-sm leading-6 text-secondary sm:text-base">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-3 sm:justify-end">{actions}</div>
      ) : null}
    </header>
  );
}
