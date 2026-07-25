"use client";

import { useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { controlClassName } from "@/components/ui/input";
import { ApiClientError } from "@/lib/api/error";
import { useUpdateEmployerShortlistNote } from "@/lib/employer/hooks";
import { cn } from "@/lib/cn";

const NOTE_MAX_LENGTH = 5000;

type ShortlistNoteEditorProps = Readonly<{
  vacancyId: string;
  candidateId: string;
  note: string | null;
  candidateLabel?: string;
}>;

type SyncedServerState = {
  vacancyId: string;
  candidateId: string;
  note: string | null;
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return "The note could not be saved. Please try again.";
}

export function ShortlistNoteEditor({
  vacancyId,
  candidateId,
  note,
  candidateLabel
}: ShortlistNoteEditorProps) {
  const textareaId = useId();
  const noteMutation = useUpdateEmployerShortlistNote(vacancyId);
  const [draft, setDraft] = useState(note ?? "");
  const [synced, setSynced] = useState<SyncedServerState>({
    vacancyId,
    candidateId,
    note
  });

  const identityChanged =
    vacancyId !== synced.vacancyId || candidateId !== synced.candidateId;
  const noteChanged = note !== synced.note;

  if (identityChanged || noteChanged) {
    setSynced({ vacancyId, candidateId, note });
    setDraft(note ?? "");
  }

  const labelTarget = candidateLabel?.trim() || "candidate";
  const normalized = draft.trim();
  const nextNote = normalized === "" ? null : normalized;
  const unchanged = nextNote === note;
  const pendingThis =
    noteMutation.isPending && noteMutation.variables?.candidateId === candidateId;
  const errorThis =
    noteMutation.isError && noteMutation.variables?.candidateId === candidateId;

  return (
    <div className="w-full space-y-3">
      <label htmlFor={textareaId} className="block text-sm font-medium text-ink">
        Private note for {labelTarget}
      </label>
      <textarea
        id={textareaId}
        value={draft}
        rows={3}
        maxLength={NOTE_MAX_LENGTH}
        disabled={pendingThis}
        aria-busy={pendingThis || undefined}
        className={cn(controlClassName, "min-h-24 px-3 py-3")}
        onChange={(event) => setDraft(event.target.value)}
      />
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          loading={pendingThis}
          disabled={pendingThis || unchanged}
          aria-label={`Save note for ${labelTarget}`}
          onClick={() => {
            if (pendingThis || unchanged) {
              return;
            }
            noteMutation.reset();
            noteMutation.mutate({ candidateId, note: nextNote });
          }}
        >
          {pendingThis ? "Saving..." : "Save note"}
        </Button>
        <p className="text-xs leading-5 text-muted">
          Visible only to your team. {draft.length}/{NOTE_MAX_LENGTH}
        </p>
      </div>
      {errorThis ? (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(noteMutation.error)}
        </p>
      ) : null}
    </div>
  );
}
