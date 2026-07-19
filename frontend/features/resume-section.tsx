"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";

import { ApiClientError } from "@/lib/api/error";
import type { JobPollingResponse } from "@/lib/api/types/jobs";
import type { ResumeResponse } from "@/lib/api/types/resume";
import { isTerminalJobStatus } from "@/lib/jobs/hooks";
import {
  useCurrentResumeQuery,
  useResumeJobQuery,
  useRetryResumeMutation,
  useUploadResumeMutation
} from "@/lib/resume/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The resume request failed. Please try again.";
}

function isResumeMissing(error: unknown): boolean {
  return error instanceof ApiClientError && error.code === "RESUME_NOT_FOUND";
}

function formatFileSize(bytes: number): string {
  if (bytes >= 1_048_576) {
    return `${(bytes / 1_048_576).toFixed(1)} MiB`;
  }

  return `${Math.max(1, Math.ceil(bytes / 1_024))} KiB`;
}

function formatUploadedAt(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function jobFailureMessage(job: JobPollingResponse): string {
  if (job.error_message) {
    return job.error_message;
  }

  if (job.status === "cancelled") {
    return "Resume processing was cancelled. Upload the file again to restart processing.";
  }

  if (job.status === "expired") {
    return "Resume processing expired. Upload the file again to restart processing.";
  }

  return "Resume processing failed. Upload another file to continue.";
}

function CurrentResume({ resume }: Readonly<{ resume: ResumeResponse }>) {
  return (
    <div className="rounded-card border border-border bg-background p-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="break-words text-sm font-medium text-ink">{resume.original_filename}</p>
          <p className="mt-1 text-sm text-secondary">
            {formatFileSize(resume.file_size)} · {resume.mime_type}
          </p>
          <p className="mt-1 text-sm text-secondary">
            Uploaded {formatUploadedAt(resume.uploaded_at)}
          </p>
        </div>
        <span className="rounded-button border border-border bg-surface px-3 py-2 text-sm text-ink">
          {resume.status}
        </span>
      </div>
    </div>
  );
}

export function ResumeSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const currentResumeQuery = useCurrentResumeQuery(enabled);
  const uploadMutation = useUploadResumeMutation();
  const retryMutation = useRetryResumeMutation();
  const jobQuery = useResumeJobQuery(activeJobId);

  const job = jobQuery.data;
  const isProcessing = job?.status === "pending" || job?.status === "running";
  const isTerminalFailure =
    job !== undefined && isTerminalJobStatus(job.status) && job.status !== "completed";
  const canRetry = job?.status === "failed" && job.retry_available;
  const isBusy = uploadMutation.isPending || retryMutation.isPending || isProcessing;
  const resumeMissing = isResumeMissing(currentResumeQuery.error);

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    uploadMutation.reset();
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile || isBusy) {
      return;
    }

    uploadMutation.mutate(selectedFile, {
      onSuccess: (response) => {
        setActiveJobId(response.job_id);
      }
    });
  }

  function onRetry() {
    if (!canRetry || retryMutation.isPending) {
      return;
    }

    retryMutation.mutate(undefined, {
      onSuccess: (response) => {
        setActiveJobId(response.id);
      }
    });
  }

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6"
        aria-labelledby="resume-section-title"
      >
        <h2 id="resume-section-title" className="text-xl font-semibold text-ink">
          Resume
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          Resume management is available only to candidate accounts.
        </p>
      </section>
    );
  }

  return (
    <section
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby="resume-section-title"
    >
      <h2 id="resume-section-title" className="text-xl font-semibold text-ink">
        Resume
      </h2>
      <p className="mt-2 text-sm text-secondary">
        Upload a PDF or DOCX resume. The maximum file size is 8 MiB.
      </p>

      <div className="mt-6 space-y-6">
        {currentResumeQuery.isLoading ? (
          <p className="text-sm text-secondary" role="status">
            Loading current resume…
          </p>
        ) : null}

        {currentResumeQuery.isError && !resumeMissing ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(currentResumeQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void currentResumeQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Try again
            </button>
          </div>
        ) : null}

        {currentResumeQuery.data ? <CurrentResume resume={currentResumeQuery.data} /> : null}

        {resumeMissing && !isProcessing ? (
          <div className="rounded-card border border-border bg-background p-4">
            <p className="text-sm font-medium text-ink">No resume uploaded</p>
            <p className="mt-2 text-sm text-secondary">
              Choose a PDF or DOCX file below to create your current resume.
            </p>
          </div>
        ) : null}

        {job ? (
          <div className="rounded-card border border-border bg-background p-4" aria-live="polite">
            <p className="text-sm font-medium text-ink">
              Processing status: <span className="capitalize">{job.status}</span>
            </p>
            {isProcessing ? (
              <p className="mt-2 text-sm text-secondary">
                Your resume is being processed. This section updates automatically.
              </p>
            ) : null}
            {job.status === "completed" ? (
              <p className="mt-2 text-sm text-success">
                Processing completed. The current resume has been refreshed.
              </p>
            ) : null}
            {isTerminalFailure ? (
              <p className="mt-2 text-sm text-danger" role="alert">
                {jobFailureMessage(job)}
              </p>
            ) : null}
            {canRetry ? (
              <div className="mt-4">
                <button
                  type="button"
                  onClick={onRetry}
                  disabled={retryMutation.isPending}
                  className="min-h-control rounded-button bg-primary px-4 text-sm font-medium text-white disabled:opacity-60"
                >
                  {retryMutation.isPending ? "Retrying…" : "Retry processing"}
                </button>
                {retryMutation.isError ? (
                  <p className="mt-2 text-sm text-danger" role="alert">
                    {errorMessage(retryMutation.error)}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {jobQuery.isError ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(jobQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void jobQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Check status again
            </button>
          </div>
        ) : null}

        {currentResumeQuery.isFetching && currentResumeQuery.data ? (
          <p className="text-sm text-secondary" role="status">
            Refreshing current resume…
          </p>
        ) : null}

        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-2">
            <label htmlFor="resume-file" className="block text-sm font-medium text-ink">
              Resume file
            </label>
            <input
              id="resume-file"
              name="file"
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={onFileChange}
              disabled={isBusy}
              className="block min-h-control w-full rounded-input border border-border bg-surface px-3 py-2 text-sm text-ink file:mr-4 file:rounded-button file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-white disabled:bg-background"
            />
            <p className="text-sm text-secondary" aria-live="polite">
              {selectedFile ? `Selected file: ${selectedFile.name}` : "No file selected."}
            </p>
          </div>

          {uploadMutation.isError ? (
            <div>
              <p className="text-sm text-danger" role="alert">
                {errorMessage(uploadMutation.error)}
              </p>
              {uploadMutation.error instanceof ApiClientError &&
              uploadMutation.error.code === "CANDIDATE_PROFILE_REQUIRED" ? (
                <a
                  href="#profile-section-title"
                  className="mt-2 inline-block text-sm font-medium text-primary underline-offset-2 hover:underline"
                >
                  Complete candidate profile
                </a>
              ) : null}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={!selectedFile || isBusy}
            className="min-h-control rounded-button bg-primary px-6 text-sm font-medium text-white disabled:opacity-60"
          >
            {uploadMutation.isPending
              ? "Uploading…"
              : isProcessing
                ? "Processing…"
                : "Upload resume"}
          </button>
        </form>
      </div>
    </section>
  );
}
