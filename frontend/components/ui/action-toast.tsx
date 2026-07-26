"use client";

import { useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";

import { Icon } from "@/components/ui/icon";
import { cn } from "@/lib/cn";

type ToastTone = "success" | "neutral";

type ToastMessage = {
  id: number;
  text: string;
  tone: ToastTone;
};

let toastId = 0;

export function useActionToast() {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  function showToast(text: string, tone: ToastTone = "success") {
    toastId += 1;
    setToast({ id: toastId, text, tone });
  }

  return {
    toast,
    showToast,
    dismissToast: () => setToast(null)
  };
}

export function ActionToast({
  toast,
  onDismiss
}: Readonly<{
  toast: ToastMessage | null;
  onDismiss: () => void;
}>) {
  const titleId = useId();

  useEffect(() => {
    if (!toast) {
      return;
    }
    const timer = window.setTimeout(onDismiss, 3200);
    return () => window.clearTimeout(timer);
  }, [toast, onDismiss]);

  if (!toast || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      className="pointer-events-none fixed inset-x-0 bottom-6 z-[60] flex justify-center px-4"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div
        key={toast.id}
        role="alertdialog"
        aria-labelledby={titleId}
        className={cn(
          "pointer-events-auto flex max-w-md items-start gap-3 rounded-button border px-4 py-3 shadow-float",
          "transition-all duration-200 ease-out",
          toast.tone === "success"
            ? "border-success/25 bg-success-soft text-success-muted"
            : "border-border bg-surface text-ink"
        )}
      >
        <span
          className={cn(
            "mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
            toast.tone === "success" ? "bg-accent/35 text-accent-muted" : "bg-surface-subtle text-secondary"
          )}
          aria-hidden="true"
        >
          <Icon name="check-circle" className="h-4 w-4" />
        </span>
        <p id={titleId} className="pt-1 text-sm font-medium leading-5">
          {toast.text}
        </p>
      </div>
    </div>,
    document.body
  );
}
