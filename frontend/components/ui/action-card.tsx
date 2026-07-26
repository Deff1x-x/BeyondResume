import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { Icon, type IconName } from "@/components/ui/icon";
import { cn } from "@/lib/cn";

export type ActionCardVariant = "primary" | "secondary" | "success" | "destructive";
export type ActionCardIconTone =
  | "accent"
  | "ai"
  | "primary"
  | "success"
  | "danger"
  | "neutral";

type ActionCardSharedProps = Readonly<{
  title: string;
  description: string;
  icon: IconName;
  variant?: ActionCardVariant;
  iconTone?: ActionCardIconTone;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  "aria-label"?: string;
}>;

export type ActionCardProps = ActionCardSharedProps &
  (
    | Readonly<{ href: string; onClick?: never; status?: false }>
    | Readonly<{
        href?: never;
        onClick?: ButtonHTMLAttributes<HTMLButtonElement>["onClick"];
        type?: ButtonHTMLAttributes<HTMLButtonElement>["type"];
        status?: false;
      }>
    | Readonly<{ href?: never; onClick?: never; status: true }>
  );

const variantShellClass: Record<ActionCardVariant, string> = {
  primary:
    "border-accent/35 bg-accent-soft/80 shadow-md shadow-accent/20 hover:border-accent/50 hover:bg-accent-soft hover:shadow-lg hover:shadow-accent/25",
  secondary:
    "border-border bg-surface shadow-card hover:border-border-strong hover:bg-surface-subtle/60 hover:shadow-card-hover",
  success: "cursor-default border-success/20 bg-success-soft/70 shadow-sm",
  destructive:
    "border-danger/15 bg-surface shadow-card hover:border-danger/30 hover:bg-danger-soft/60 hover:shadow-card-hover"
};

const iconToneClass: Record<ActionCardIconTone, string> = {
  accent: "bg-accent text-accent-foreground shadow-sm shadow-accent/25",
  ai: "bg-ai-soft text-ai-muted ring-1 ring-ai/20",
  primary: "bg-primary/10 text-primary ring-1 ring-primary/15",
  success: "bg-success/15 text-success ring-1 ring-success/20",
  danger: "bg-danger-soft text-danger ring-1 ring-danger/15",
  neutral: "bg-surface-subtle text-ink ring-1 ring-border"
};

const variantDefaultIconTone: Record<ActionCardVariant, ActionCardIconTone> = {
  primary: "accent",
  secondary: "neutral",
  success: "success",
  destructive: "danger"
};

const interactiveMotionClass =
  "transition-all duration-200 ease-out hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 motion-reduce:transition-none motion-reduce:hover:translate-y-0 motion-reduce:active:scale-100";

function ActionCardContent({
  title,
  description,
  icon,
  iconTone
}: Readonly<{
  title: string;
  description: string;
  icon: IconName;
  iconTone: ActionCardIconTone;
}>) {
  return (
    <>
      <span
        className={cn(
          "inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-transform duration-200 ease-out group-hover:scale-105 motion-reduce:group-hover:scale-100",
          iconToneClass[iconTone]
        )}
        aria-hidden="true"
      >
        <Icon name={icon} className="h-[1.125rem] w-[1.125rem]" />
      </span>
      <span className="min-w-0 flex-1 text-left">
        <span className="block text-sm font-semibold tracking-tight text-ink">{title}</span>
        <span className="mt-0.5 block text-xs leading-5 text-secondary">{description}</span>
      </span>
    </>
  );
}

export function ActionCard(props: ActionCardProps) {
  const {
    title,
    description,
    icon,
    variant = "secondary",
    iconTone,
    className,
    disabled = false,
    loading = false,
    "aria-label": ariaLabel
  } = props;

  const isStatus = props.status === true;
  const isDisabled = disabled || loading;
  const resolvedIconTone = iconTone ?? variantDefaultIconTone[variant];
  const shellClass = cn(
    "group flex h-full min-h-[4.75rem] w-full items-start gap-3 rounded-card border px-4 py-3.5 text-left",
    variantShellClass[variant],
    !isStatus && interactiveMotionClass,
    isDisabled &&
      "pointer-events-none cursor-not-allowed opacity-60 shadow-none hover:translate-y-0 hover:shadow-none",
    className
  );

  const content = (
    <ActionCardContent
      title={title}
      description={description}
      icon={icon}
      iconTone={resolvedIconTone}
    />
  );

  if (isStatus) {
    return (
      <div className={shellClass} role="status" aria-label={ariaLabel ?? title}>
        {content}
      </div>
    );
  }

  if ("href" in props && typeof props.href === "string") {
    if (isDisabled) {
      return (
        <span className={shellClass} aria-disabled="true" aria-label={ariaLabel ?? title}>
          {content}
        </span>
      );
    }

    return (
      <Link href={props.href} className={shellClass} aria-label={ariaLabel ?? title}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type={"type" in props && props.type ? props.type : "button"}
      className={shellClass}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      aria-label={ariaLabel ?? title}
      onClick={"onClick" in props ? props.onClick : undefined}
    >
      {content}
    </button>
  );
}

/** Responsive action card grid: 1 / 2 / 3 columns. */
export function ActionCardGrid({
  children,
  className
}: Readonly<{ children: ReactNode; className?: string }>) {
  return (
    <div
      className={cn(
        "grid auto-rows-fr grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3",
        className
      )}
    >
      {children}
    </div>
  );
}
