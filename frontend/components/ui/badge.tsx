import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

type BadgeVariant =
  | "neutral"
  | "primary"
  | "accent"
  | "verified"
  | "ai"
  | "success"
  | "warning"
  | "danger";

const badgeVariantClass: Record<BadgeVariant, string> = {
  neutral: "border-border bg-surface-subtle text-secondary",
  primary: "border-primary/15 bg-primary/5 text-primary",
  accent: "border-accent/40 bg-accent/20 text-accent-muted",
  verified: "border-verified/40 bg-verified/20 text-verified-muted",
  ai: "border-ai/40 bg-ai/15 text-ai-muted",
  success: "border-success/25 bg-success/10 text-success-muted",
  warning: "border-warning/30 bg-warning/10 text-warning-muted",
  danger: "border-danger/20 bg-danger/10 text-danger-muted"
};

export type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
  children: ReactNode;
};

export function Badge({
  variant = "neutral",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center truncate rounded-badge border px-2.5 py-1 text-xs font-semibold tracking-wide",
        badgeVariantClass[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export type StatusBadgeProps = HTMLAttributes<HTMLSpanElement> & {
  status: string;
  label?: string;
};

function statusVariant(status: string): BadgeVariant {
  const normalized = status.trim().toLowerCase();
  if (
    normalized === "completed" ||
    normalized === "parsed" ||
    normalized === "analyzed" ||
    normalized === "ownership_confirmed" ||
    normalized === "issuer_verified" ||
    normalized === "source_reachable"
  ) {
    return "success";
  }
  if (
    normalized === "failed" ||
    normalized === "invalidated" ||
    normalized === "disputed"
  ) {
    return "danger";
  }
  if (
    normalized === "processing" ||
    normalized === "running" ||
    normalized === "pending" ||
    normalized === "queued" ||
    normalized === "uploaded" ||
    normalized === "platform_assessed"
  ) {
    return "warning";
  }
  if (normalized === "unverified") {
    return "neutral";
  }
  return "neutral";
}

function defaultStatusLabel(status: string): string {
  const normalized = status.trim().toLowerCase();
  if (normalized === "unverified") {
    return "Unverified";
  }
  if (normalized === "source_reachable") {
    return "Source reachable";
  }
  if (normalized === "ownership_confirmed") {
    return "Ownership confirmed";
  }
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function StatusBadge({
  status,
  label,
  className,
  ...props
}: StatusBadgeProps) {
  const text = label ?? defaultStatusLabel(status);
  return (
    <Badge
      variant={statusVariant(status)}
      className={className}
      title={text}
      {...props}
    >
      {text}
    </Badge>
  );
}
