import type { ReactNode, SVGProps } from "react";
import Image from "next/image";

import { cn } from "@/lib/cn";

export type IconName =
  | "dashboard"
  | "profile"
  | "resume"
  | "github"
  | "evidence"
  | "passport"
  | "roadmap"
  | "employer"
  | "check"
  | "check-circle"
  | "send"
  | "undo"
  | "alert"
  | "arrow-right"
  | "gauge"
  | "spark"
  | "refresh"
  | "code"
  | "user-search"
  | "bookmark-check"
  | "bookmark-plus"
  | "message-square-question"
  | "clipboard-check"
  | "folder-open"
  | "trash-2"
  | "chevron-down"
  | "circle-dot"
  | "lock";

type IconProps = SVGProps<SVGSVGElement> & { name: IconName };

const paths: Record<IconName, ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" /></>,
  resume: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
  github: <><path d="M15 22v-3.9c.04-1.01-.31-2-.98-2.76 3.2-.36 6.56-1.57 6.56-7.1a5.55 5.55 0 0 0-1.48-3.85A5.15 5.15 0 0 0 19 1.7S17.8 1.32 15 3.18a13.55 13.55 0 0 0-6 0C6.2 1.32 5 1.7 5 1.7a5.15 5.15 0 0 0-.1 2.69 5.55 5.55 0 0 0-1.48 3.85C3.42 13.76 6.78 14.97 10 15.34a3.56 3.56 0 0 0-.98 2.76V22" /><path d="M9 19c-3 .92-5-1.5-5-1.5" /></>,
  evidence: <><path d="M12 22s8-3.7 8-10V5l-8-3-8 3v7c0 6.3 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></>,
  passport: <><path d="M8 3h8l3 3v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h2Z" /><path d="M8 3v5h8V3M8.5 14l2 2 4-4" /></>,
  roadmap: <><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" /><path d="M8 18h3a3 3 0 0 0 3-3v-1a3 3 0 0 1 3-3h1" /></>,
  employer: <><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-5h6v5M8 10h.01M12 10h.01M16 10h.01" /></>,
  check: <><path d="m5 12.5 4.5 4.5L19 7.5" /></>,
  "check-circle": (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.2 2.4 2.4 4.6-5" />
    </>
  ),
  send: (
    <>
      <path d="M4.5 12.5 19.2 4.8 12.5 19.5l-1.8-6.2Z" />
      <path d="m10.7 13.3 8.5-8.5" />
    </>
  ),
  undo: (
    <>
      <path d="M9.5 7.5 5.5 11.5 9.5 15.5" />
      <path d="M5.5 11.5h8a5 5 0 1 1 0 10H12" />
    </>
  ),
  alert: <><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4.5M12 17.5h.01" /></>,
  "arrow-right": <><path d="M4 12h15M13 6l6 6-6 6" /></>,
  gauge: <><path d="M3.5 18a9 9 0 1 1 17 0" /><path d="m12 14 3.5-4.5" /><path d="M12 14h.01" /></>,
  spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7Z" /><path d="M18.5 3.5v3M20 5h-3" /></>,
  refresh: <><path d="M20.5 12a8.5 8.5 0 1 1-2.5-6" /><path d="M20.5 4v5h-5" /></>,
  code: <><path d="m8.5 8.5-4 3.5 4 3.5M15.5 8.5l4 3.5-4 3.5M13.5 6l-3 12" /></>,
  "user-search": (
    <>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <circle cx="19" cy="11" r="2" />
      <path d="m22 13-1.9-1.9" />
    </>
  ),
  "bookmark-check": (
    <>
      <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z" />
      <path d="m9 10 2 2 4-4" />
    </>
  ),
  "bookmark-plus": (
    <>
      <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z" />
      <path d="M12 7v6" />
      <path d="M9 10h6" />
    </>
  ),
  "message-square-question": (
    <>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <path d="M12 17h.01" />
    </>
  ),
  "clipboard-check": (
    <>
      <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <path d="m9 14 2 2 4-4" />
    </>
  ),
  "folder-open": (
    <>
      <path d="m6 14 1.45-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.55 6a2 2 0 0 1-1.94 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2" />
    </>
  ),
  "trash-2": (
    <>
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </>
  ),
  "chevron-down": <path d="m6 9 6 6 6-6" />,
  "circle-dot": (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />
    </>
  ),
  lock: (
    <>
      <rect width="14" height="10" x="5" y="11" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  )
};

export function Icon({ name, className, ...props }: IconProps) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={cn("h-5 w-5", className)} {...props}>{paths[name]}</svg>;
}

export function BrandMark({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex h-10 w-10 shrink-0 items-center justify-center", className)} aria-hidden="true">
      <Image src="/brand/beyondresume-logo.jpg" alt="" width={798} height={705} className="h-full w-full object-contain" priority />
    </span>
  );
}
