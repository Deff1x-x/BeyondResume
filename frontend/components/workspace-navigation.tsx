"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/ui/icon";
import { cn } from "@/lib/cn";
import { useLogout } from "@/lib/auth/hooks";

type WorkspaceRole = "candidate" | "employer";

type NavigationItem = {
  href: string;
  label: string;
  kind: "route" | "anchor";
};

type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

const candidateNavigation: NavigationGroup[] = [
  {
    label: "Workspace",
    items: [
      { href: "/", label: "Overview", kind: "route" },
      { href: "/skill-passport", label: "Skill Passport", kind: "route" },
      { href: "/vacancies", label: "Opportunities", kind: "route" }
    ]
  },
  {
    label: "Evidence & development",
    items: [
      { href: "/#github-section-title", label: "GitHub", kind: "anchor" },
      { href: "/#resume-section-title", label: "Resume", kind: "anchor" },
      { href: "/#evidence-hub-section-title", label: "Evidence", kind: "anchor" },
      { href: "/#roadmap-section-title", label: "Roadmap", kind: "anchor" }
    ]
  },
  {
    label: "Account",
    items: [{ href: "/profile", label: "Profile", kind: "route" }]
  }
];

const employerNavigation: NavigationGroup[] = [
  {
    label: "Workspace",
    items: [
      { href: "/", label: "Overview", kind: "route" },
      { href: "/#employer-vacancies", label: "Vacancies", kind: "anchor" },
      { href: "/#top-matches-by-vacancy", label: "Matches", kind: "anchor" },
      { href: "/#employer-company", label: "Company", kind: "anchor" }
    ]
  }
];

function navigationFor(role: WorkspaceRole): NavigationGroup[] {
  return role === "candidate" ? candidateNavigation : employerNavigation;
}

function isActiveRoute(pathname: string, item: NavigationItem): boolean {
  return item.kind === "route" && pathname === item.href;
}

function NavigationGroups({ role, mobile = false }: Readonly<{ role: WorkspaceRole; mobile?: boolean }>) {
  const pathname = usePathname();

  return (
    <div className={cn("space-y-6", mobile && "space-y-5")}>
      {navigationFor(role).map((group) => (
        <section key={group.label} aria-label={group.label}>
          <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
            {group.label}
          </p>
          <ul className="space-y-1">
            {group.items.map((item) => {
              const active = isActiveRoute(pathname, item);
              const className = cn(
                "flex min-h-10 items-center rounded-lg px-3 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2",
                active
                  ? "bg-primary/10 text-primary"
                  : item.kind === "anchor"
                    ? "text-secondary hover:bg-surface-subtle hover:text-ink"
                    : "text-secondary hover:bg-surface-subtle hover:text-ink"
              );
              return (
                <li key={item.href}>
                  {item.kind === "route" ? (
                    <Link href={item.href} className={className} aria-current={active ? "page" : undefined}>
                      {item.label}
                    </Link>
                  ) : (
                    <a href={item.href} className={className}>
                      {item.label}
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

export function WorkspaceNavigation({ role, email }: Readonly<{ role: WorkspaceRole; email?: string }>) {
  const router = useRouter();
  const logout = useLogout();
  const workspaceName = role === "candidate" ? "Candidate workspace" : "Employer workspace";

  function onLogout() {
    logout();
    router.push("/login");
  }

  return (
    <>
      <aside className="hidden min-h-screen border-r border-border/80 bg-surface/80 px-4 py-6 lg:flex lg:h-screen lg:w-72 lg:shrink-0 lg:sticky lg:top-0 lg:flex-col lg:overflow-y-auto">
        <Link href="/" className="flex items-center gap-3 rounded-lg px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">
          <BrandMark />
          <span className="text-sm font-semibold text-ink">BeyondResume</span>
        </Link>
        <div className="mx-2 mt-8 rounded-xl border border-border bg-background px-3 py-3">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-primary">{role}</p>
          <p className="mt-1 text-sm font-medium text-ink">{workspaceName}</p>
        </div>
        <nav className="mt-8 flex-1" aria-label={`${workspaceName} navigation`}>
          <NavigationGroups role={role} />
        </nav>
        <div className="border-t border-border pt-4">
          {email ? <p className="truncate px-3 pb-3 text-sm text-secondary" title={email}>{email}</p> : null}
          <Button type="button" variant="ghost" className="w-full justify-start" onClick={onLogout}>
            Log out
          </Button>
        </div>
      </aside>

      <header className="sticky top-0 z-20 border-b border-border/80 bg-background/95 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <Link href="/" className="flex min-w-0 items-center gap-2 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">
            <BrandMark />
            <span className="truncate text-sm font-semibold text-ink">{workspaceName}</span>
          </Link>
          <details className="group relative">
            <summary className="flex min-h-10 cursor-pointer list-none items-center rounded-lg border border-border bg-surface px-3 text-sm font-medium text-ink marker:content-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">
              Menu
            </summary>
            <div className="absolute right-0 mt-2 max-h-[calc(100vh-5rem)] w-[min(22rem,calc(100vw-2rem))] overflow-y-auto rounded-xl border border-border bg-background p-4 shadow-lg">
              <nav aria-label={`${workspaceName} navigation`}>
                <NavigationGroups role={role} mobile />
              </nav>
              <div className="mt-5 border-t border-border pt-4">
                {email ? <p className="mb-3 truncate text-sm text-secondary" title={email}>{email}</p> : null}
                <Button type="button" variant="ghost" className="w-full justify-start" onClick={onLogout}>
                  Log out
                </Button>
              </div>
            </div>
          </details>
        </div>
      </header>
    </>
  );
}
