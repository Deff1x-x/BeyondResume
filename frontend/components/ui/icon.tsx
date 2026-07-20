import type { ReactNode, SVGProps } from "react";

import { cn } from "@/lib/cn";

export type IconName = "dashboard" | "profile" | "resume" | "github" | "evidence" | "passport" | "roadmap" | "employer";

type IconProps = SVGProps<SVGSVGElement> & { name: IconName };

const paths: Record<IconName, ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  profile: <><circle cx="12" cy="8" r="4" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" /></>,
  resume: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
  github: <><path d="M15 22v-3.9c.04-1.01-.31-2-.98-2.76 3.2-.36 6.56-1.57 6.56-7.1a5.55 5.55 0 0 0-1.48-3.85A5.15 5.15 0 0 0 19 1.7S17.8 1.32 15 3.18a13.55 13.55 0 0 0-6 0C6.2 1.32 5 1.7 5 1.7a5.15 5.15 0 0 0-.1 2.69 5.55 5.55 0 0 0-1.48 3.85C3.42 13.76 6.78 14.97 10 15.34a3.56 3.56 0 0 0-.98 2.76V22" /><path d="M9 19c-3 .92-5-1.5-5-1.5" /></>,
  evidence: <><path d="M12 22s8-3.7 8-10V5l-8-3-8 3v7c0 6.3 8 10 8 10Z" /><path d="m9 12 2 2 4-4" /></>,
  passport: <><path d="M8 3h8l3 3v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h2Z" /><path d="M8 3v5h8V3M8.5 14l2 2 4-4" /></>,
  roadmap: <><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" /><path d="M8 18h3a3 3 0 0 0 3-3v-1a3 3 0 0 1 3-3h1" /></>,
  employer: <><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-5h6v5M8 10h.01M12 10h.01M16 10h.01" /></>
};

export function Icon({ name, className, ...props }: IconProps) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={cn("h-5 w-5", className)} {...props}>{paths[name]}</svg>;
}

export function BrandMark({ className }: { className?: string }) {
  return <span className={cn("inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-primary to-cyan-500 text-white shadow-lg shadow-primary/25", className)} aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5"><path d="M6 4h7a5 5 0 0 1 0 10H6Z" /><path d="M6 14h8a3 3 0 0 1 0 6H6Z" /></svg></span>;
}
