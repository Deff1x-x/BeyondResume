import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type SectionHeaderProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  count?: ReactNode;
  titleId?: string;
  className?: string;
  titleAs?: "h2" | "h3";
  size?: "md" | "lg";
};

export function SectionHeader({
  title,
  description,
  action,
  count,
  titleId,
  className,
  titleAs = "h2",
  size = "lg"
}: SectionHeaderProps) {
  const TitleTag = titleAs;

  return (
    <div
      className={cn(
        "flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <TitleTag
            id={titleId}
            className={cn(
              "font-semibold text-ink",
              size === "lg" ? "text-xl" : "text-base"
            )}
          >
            {title}
          </TitleTag>
          {count != null ? (
            <span className="text-sm text-secondary">{count}</span>
          ) : null}
        </div>
        {description ? (
          <p className="mt-2 text-sm leading-6 text-secondary">{description}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
