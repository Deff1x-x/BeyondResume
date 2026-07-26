"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MouseEvent as ReactMouseEvent
} from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BrandMark } from "@/components/ui/icon";
import { useScrollSpy } from "@/hooks/use-scroll-spy";
import { useCandidateOnboarding } from "@/hooks/use-candidate-onboarding";
import { cn } from "@/lib/cn";
import { useLogout } from "@/lib/auth/hooks";
import {
  resolveScrollBehavior,
  scrollToSectionId,
  sectionIdFromHash
} from "@/lib/navigation/scroll-spy";

type WorkspaceRole = "candidate" | "employer";

type NavigationItem = {
  href: string;
  label: string;
  kind: "route" | "anchor";
  /** Overview-page section observed for scroll-aware highlighting. */
  sectionId?: string;
};

type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

const candidateNavigation: NavigationGroup[] = [
  {
    label: "Workspace",
    items: [
      { href: "/", label: "Overview", kind: "route", sectionId: "overview-section" },
      { href: "/skill-passport", label: "Skill Passport", kind: "route", sectionId: "skill-passport-section" },
      { href: "/vacancies", label: "Opportunities", kind: "route", sectionId: "opportunities-section" }
    ]
  },
  {
    label: "Evidence & development",
    items: [
      { href: "/#resume-section", label: "Resume", kind: "anchor", sectionId: "resume-section" },
      { href: "/#github-section", label: "GitHub", kind: "anchor", sectionId: "github-section" },
      { href: "/#evidence-section", label: "Evidence", kind: "anchor", sectionId: "evidence-section" },
      {
        href: "/#career-companion-section",
        label: "Career Companion",
        kind: "anchor",
        sectionId: "career-companion-section"
      }
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
      { href: "/", label: "Overview", kind: "route", sectionId: "overview-section" },
      { href: "/#employer-vacancies", label: "Vacancies", kind: "anchor", sectionId: "employer-vacancies" },
      {
        href: "/#top-matches-by-vacancy",
        label: "Recommended",
        kind: "anchor",
        sectionId: "top-matches-by-vacancy"
      },
      { href: "/#employer-company", label: "Company", kind: "anchor", sectionId: "employer-company" }
    ]
  }
];

function navigationFor(role: WorkspaceRole): NavigationGroup[] {
  return role === "candidate" ? candidateNavigation : employerNavigation;
}

function flatNavigationItems(role: WorkspaceRole): NavigationItem[] {
  return navigationFor(role).flatMap((group) => group.items);
}

function isOverviewPath(pathname: string): boolean {
  return pathname === "/";
}

function isActiveNavItem(
  item: NavigationItem,
  pathname: string,
  activeSectionId: string | null
): boolean {
  // Dedicated routes remain the source of truth off Overview.
  if (!isOverviewPath(pathname)) {
    return item.kind === "route" && pathname === item.href;
  }

  // On Overview, visible section position drives the active item.
  if (activeSectionId) {
    return item.sectionId === activeSectionId;
  }

  return item.kind === "route" && item.href === "/";
}

function ariaCurrentFor(
  item: NavigationItem,
  active: boolean,
  onOverview: boolean
): "page" | "location" | undefined {
  if (!active) {
    return undefined;
  }
  if (onOverview && item.sectionId) {
    return "location";
  }
  return "page";
}

function NavigationGroups({ role, mobile = false }: Readonly<{ role: WorkspaceRole; mobile?: boolean }>) {
  const pathname = usePathname();
  const onOverview = isOverviewPath(pathname);
  const { incompleteNavLabels, markVacanciesExplored } = useCandidateOnboarding();
  const items = useMemo(() => flatNavigationItems(role), [role]);
  const sectionIds = useMemo(
    () => items.map((item) => item.sectionId).filter((id): id is string => Boolean(id)),
    [items]
  );

  const [lockedSectionId, setLockedSectionId] = useState<string | null>(null);
  const unlockTimerRef = useRef<number | null>(null);

  const clearUnlockTimer = useCallback(() => {
    if (unlockTimerRef.current != null) {
      window.clearTimeout(unlockTimerRef.current);
      unlockTimerRef.current = null;
    }
  }, []);

  const lockSection = useCallback(
    (sectionId: string) => {
      clearUnlockTimer();
      setLockedSectionId(sectionId);
      const release = () => {
        setLockedSectionId((current) => (current === sectionId ? null : current));
        window.removeEventListener("scrollend", release);
      };
      window.addEventListener("scrollend", release, { once: true });
      unlockTimerRef.current = window.setTimeout(
        release,
        resolveScrollBehavior() === "auto" ? 50 : 900
      );
    },
    [clearUnlockTimer]
  );

  useEffect(() => () => clearUnlockTimer(), [clearUnlockTimer]);

  const activeSectionId = useScrollSpy({
    sectionIds,
    enabled: onOverview,
    lockedSectionId
  });

  // After navigating to Overview with a hash, scroll once the target exists.
  useEffect(() => {
    if (!onOverview) {
      return;
    }
    const hashId = sectionIdFromHash(window.location.hash);
    if (!hashId || !sectionIds.includes(hashId)) {
      return;
    }

    let attempts = 0;
    let frame = 0;
    const tryScroll = () => {
      attempts += 1;
      if (scrollToSectionId(hashId, { behavior: "auto" })) {
        lockSection(hashId);
        return;
      }
      if (attempts < 40) {
        frame = requestAnimationFrame(tryScroll);
      }
    };
    frame = requestAnimationFrame(tryScroll);
    return () => cancelAnimationFrame(frame);
  }, [onOverview, pathname, sectionIds, lockSection]);

  function onSectionNavClick(event: ReactMouseEvent<HTMLAnchorElement>, item: NavigationItem) {
    if (item.label === "Opportunities") {
      markVacanciesExplored();
    }
    if (!item.sectionId) {
      return;
    }
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    // Off Overview, keep normal route / hash navigation to dedicated destinations.
    if (!onOverview) {
      return;
    }

    // On Overview, scroll to the matching section when it exists on this page.
    const target = document.getElementById(item.sectionId);
    if (!target) {
      return;
    }

    event.preventDefault();
    lockSection(item.sectionId);
    const nextUrl =
      item.href === "/"
        ? `${window.location.pathname}${window.location.search}`
        : `${window.location.pathname}${window.location.search}#${item.sectionId}`;
    window.history.replaceState(null, "", nextUrl);
    scrollToSectionId(item.sectionId);
  }

  return (
    <div className={cn("space-y-6", mobile && "space-y-5")}>
      {navigationFor(role).map((group) => (
        <section key={group.label} aria-label={group.label}>
          <p
            className={cn(
              "mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.14em]",
              mobile ? "text-muted" : "text-primary-200"
            )}
          >
            {group.label}
          </p>
          <ul className="space-y-1">
            {group.items.map((item) => {
              const active = isActiveNavItem(item, pathname, activeSectionId);
              const isAiItem = item.label === "Career Companion";
              const className = cn(
                "relative flex min-h-10 items-center gap-2 rounded-control px-3 text-sm font-medium transition-all duration-fast ease-standard",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
                mobile
                  ? cn(
                      "focus-visible:ring-focus-ring focus-visible:ring-offset-surface",
                      active
                        ? "bg-surface-subtle text-ink shadow-sm before:absolute before:inset-y-1.5 before:left-0 before:w-[3px] before:rounded-full before:bg-accent"
                        : "text-secondary hover:translate-x-0.5 hover:bg-surface-subtle hover:text-ink motion-reduce:hover:translate-x-0"
                    )
                  : cn(
                      "focus-visible:ring-primary-foreground/40 focus-visible:ring-offset-primary",
                      active
                        ? "bg-primary-foreground/10 text-primary-foreground shadow-sm before:absolute before:inset-y-1.5 before:left-0 before:w-[3px] before:rounded-full before:bg-accent"
                        : isAiItem
                          ? "text-ai hover:translate-x-0.5 hover:bg-primary-foreground/10 hover:text-ai motion-reduce:hover:translate-x-0"
                          : "text-primary-200 hover:translate-x-0.5 hover:bg-primary-foreground/10 hover:text-primary-foreground motion-reduce:hover:translate-x-0"
                    )
              );
              const ariaCurrent = ariaCurrentFor(item, active, onOverview);
              const showGettingStarted = role === "candidate" && incompleteNavLabels.has(item.label);
              return (
                <li key={item.href}>
                  {item.kind === "route" ? (
                    <Link
                      href={item.href}
                      className={className}
                      aria-current={ariaCurrent}
                      onClick={(event) => onSectionNavClick(event, item)}
                    >
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                      {showGettingStarted ? (
                        <Badge
                          variant={mobile ? "accent" : "accent"}
                          className={cn(
                            "ml-2 shrink-0 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                            !mobile && "border-accent/50 bg-accent/20 text-accent"
                          )}
                        >
                          Getting Started
                        </Badge>
                      ) : null}
                    </Link>
                  ) : (
                    <a
                      href={item.href}
                      className={className}
                      aria-current={ariaCurrent}
                      onClick={(event) => onSectionNavClick(event, item)}
                    >
                      <span className="min-w-0 flex-1 truncate">{item.label}</span>
                      {showGettingStarted ? (
                        <Badge
                          variant="accent"
                          className={cn(
                            "ml-2 shrink-0 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                            !mobile && "border-accent/50 bg-accent/20 text-accent"
                          )}
                        >
                          Getting Started
                        </Badge>
                      ) : null}
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
      <aside className="hidden min-h-screen border-r border-primary-hover bg-primary px-4 py-6 text-primary-foreground lg:flex lg:h-screen lg:w-72 lg:shrink-0 lg:sticky lg:top-0 lg:flex-col lg:overflow-y-auto">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-control px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-foreground/40 focus-visible:ring-offset-2 focus-visible:ring-offset-primary"
        >
          <BrandMark />
          <span className="text-sm font-semibold text-primary-foreground">BeyondResume</span>
        </Link>
        <div className="mx-2 mt-8 rounded-card border border-primary-foreground/15 bg-primary-foreground/5 px-3 py-3">
          <p className="text-xs font-semibold tracking-wide text-accent">{role}</p>
          <p className="mt-1 text-sm font-medium text-primary-foreground">{workspaceName}</p>
        </div>
        <nav className="mt-8 flex-1" aria-label={`${workspaceName} navigation`}>
          <NavigationGroups role={role} />
        </nav>
        <div className="border-t border-primary-foreground/15 pt-4">
          {email ? (
            <p className="truncate px-3 pb-3 text-sm text-primary-200" title={email}>
              {email}
            </p>
          ) : null}
          <Button
            type="button"
            variant="ghost"
            className="w-full justify-start text-primary-200 hover:bg-primary-foreground/10 hover:text-primary-foreground"
            onClick={onLogout}
          >
            Log out
          </Button>
        </div>
      </aside>

      <header className="sticky top-0 z-20 border-b border-border bg-background/95 px-4 py-3 backdrop-blur lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <Link href="/" className="flex min-w-0 items-center gap-2 rounded-control focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">
            <BrandMark />
            <span className="truncate text-sm font-semibold text-ink">{workspaceName}</span>
          </Link>
          <details className="group relative">
            <summary className="flex min-h-10 cursor-pointer list-none items-center rounded-control border border-border bg-surface px-3 text-sm font-medium text-ink marker:content-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2">
              Menu
            </summary>
            <div className="absolute right-0 mt-2 max-h-[calc(100vh-5rem)] w-[min(22rem,calc(100vw-2rem))] overflow-y-auto rounded-card border border-border bg-surface p-4 shadow-card page-enter">
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

/** Exported for unit tests. */
export const __testing = {
  candidateNavigation,
  employerNavigation,
  isActiveNavItem,
  ariaCurrentFor,
  isOverviewPath
};
