import type { ReactNode } from "react";

import { cn } from "@/lib/cn";
import { Icon, type IconName } from "@/components/ui/icon";

export type SectionHeaderProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  count?: ReactNode;
  titleId?: string;
  className?: string;
  titleAs?: "h2" | "h3";
  size?: "md" | "lg";
  icon?: IconName;
};

export function SectionHeader({
  title,
  description,
  action,
  count,
  titleId,
  className,
  titleAs = "h2",
  size = "lg",
  icon
}: SectionHeaderProps) {
  const TitleTag = titleAs;

  return (
    <div
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="flex min-w-0 gap-3">
        {icon ? <span className="mt-0.5 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/10"><Icon name={icon} className="h-[18px] w-[18px]" /></span> : null}
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
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
