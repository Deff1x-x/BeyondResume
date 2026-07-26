"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/lib/auth/hooks";
import {
  getDemoSessionRole,
  markDemoSession,
  useExitDemo,
  useResetDemo
} from "@/lib/demo/hooks";
import { cn } from "@/lib/cn";

const DEMO_EMAIL_SUFFIX = "@beyondresume.dev";

export function DemoModeBadge() {
  const { data: user } = useCurrentUser();
  const resetDemo = useResetDemo();
  const exitDemo = useExitDemo();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!user) {
      setVisible(false);
      return;
    }
    const isDemoEmail = user.email.toLowerCase().endsWith(DEMO_EMAIL_SUFFIX);
    if (isDemoEmail) {
      markDemoSession(user.role);
      setVisible(true);
      return;
    }
    setVisible(Boolean(getDemoSessionRole()));
  }, [user]);

  if (!visible || !user) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-30 flex max-w-[min(22rem,calc(100vw-2rem))] flex-col gap-2 rounded-card border border-accent/40 bg-surface p-3 shadow-float",
        "sm:flex-row sm:items-center"
      )}
      role="region"
      aria-label="Demo Mode controls"
    >
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent-muted">Demo Mode</p>
        <p className="mt-0.5 truncate text-sm text-secondary">{user.role} workspace</p>
      </div>
      <div className="flex shrink-0 gap-2">
        <Button
          type="button"
          size="sm"
          variant="secondary"
          loading={resetDemo.isPending}
          onClick={() => void resetDemo.mutateAsync()}
        >
          Restart Demo
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={exitDemo}>
          Exit Demo
        </Button>
      </div>
      {resetDemo.isError ? (
        <p className="basis-full text-xs text-danger" role="alert">
          Could not restart the demo. Try again.
        </p>
      ) : null}
    </div>
  );
}
