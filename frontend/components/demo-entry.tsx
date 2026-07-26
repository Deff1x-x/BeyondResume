"use client";

import { useEffect, useId, useRef, useState } from "react";

import { Button, primaryActionClass } from "@/components/ui/button";
import { useDemoStatus, useStartDemo } from "@/lib/demo/hooks";
import type { Role } from "@/lib/api/types/auth";
import { cn } from "@/lib/cn";
import { ApiClientError } from "@/lib/api/error";

const choices: Array<{ role: Role; title: string; description: string }> = [
  {
    role: "candidate",
    title: "Candidate Demo",
    description: "Experience BeyondResume from a candidate's perspective."
  },
  {
    role: "employer",
    title: "Employer Demo",
    description: "See how recruiters discover and evaluate talent."
  }
];

export function DemoEntryButton({ className }: Readonly<{ className?: string }>) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  const statusQuery = useDemoStatus();
  const startDemo = useStartDemo();
  const [error, setError] = useState<string | null>(null);

  const enabled = statusQuery.data?.enabled === true;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    function onClose() {
      setError(null);
      startDemo.reset();
    }
    dialog.addEventListener("close", onClose);
    return () => dialog.removeEventListener("close", onClose);
  }, [startDemo]);

  if (statusQuery.isError || statusQuery.isLoading) {
    // Keep landing usable while status loads; hide CTA if demo is disabled.
    if (statusQuery.isError) {
      return null;
    }
  }

  if (statusQuery.isSuccess && !enabled) {
    return null;
  }

  function openModal() {
    setError(null);
    dialogRef.current?.showModal();
  }

  function closeModal() {
    dialogRef.current?.close();
  }

  async function onChoose(role: Role) {
    setError(null);
    try {
      await startDemo.mutateAsync(role);
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : "Demo Mode could not start. Please try again.";
      setError(message);
    }
  }

  return (
    <>
      <button
        type="button"
        className={cn(primaryActionClass, "px-6 shadow-accent/25", className)}
        onClick={openModal}
        disabled={!enabled && !statusQuery.isLoading}
      >
        Try Live Demo
      </button>

      <dialog
        ref={dialogRef}
        className="w-[min(28rem,calc(100vw-2rem))] rounded-card border border-border bg-surface p-0 text-ink shadow-float backdrop:bg-ink/40"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <div className="space-y-5 p-5 sm:p-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">Demo Mode</p>
            <h2 id={titleId} className="mt-1 text-xl font-semibold tracking-tight text-ink">
              Choose a live demo
            </h2>
            <p id={descriptionId} className="mt-2 text-sm leading-6 text-secondary">
              Jump into the real product with preloaded evidence, matches, and instant AI responses.
              No registration required.
            </p>
          </div>

          <div className="grid gap-3">
            {choices.map((choice) => (
              <button
                key={choice.role}
                type="button"
                className="rounded-card border border-border bg-background px-4 py-4 text-left transition hover:border-accent/50 hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 disabled:opacity-60"
                disabled={startDemo.isPending}
                onClick={() => void onChoose(choice.role)}
              >
                <span className="block text-sm font-semibold text-ink">{choice.title}</span>
                <span className="mt-1 block text-sm leading-6 text-secondary">{choice.description}</span>
              </button>
            ))}
          </div>

          {error ? (
            <p className="text-sm text-danger" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex justify-end">
            <Button type="button" variant="ghost" onClick={closeModal} disabled={startDemo.isPending}>
              Cancel
            </Button>
          </div>
        </div>
      </dialog>
    </>
  );
}
