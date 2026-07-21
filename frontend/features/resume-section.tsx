"use client";

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonCard } from "@/components/ui/skeleton";
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
    if (error.code === "DATABASE_ERROR" || error.code === "RESUME_STORAGE_ERROR") {
      return "Resume could not be saved. Please try again.";
    }
    if (error.code === "UNSUPPORTED_RESUME_TYPE") {
      return "Only PDF files are supported.";
    }
    if (error.code === "INVALID_RESUME_PDF") {
      return "The PDF could not be read.";
    }
    if (error.code === "EMPTY_RESUME_FILE") {
      return "Resume file is empty.";
    }
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

function resumeStatusLabel(status: ResumeResponse["status"]): string {
  switch (status) {
    case "uploaded":
      return "Uploaded";
    case "parsed":
      return "Parsed";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

function CurrentResume({ resume }: Readonly<{ resume: ResumeResponse }>) {
  return (
    <Card className="bg-background">
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="break-words text-sm font-medium text-ink">{resume.original_filename}</p>
            <p className="mt-1 text-sm text-secondary">
              {formatFileSize(resume.file_size)} · {resume.mime_type}
            </p>
            <p className="mt-1 text-sm text-secondary">
              Uploaded {formatUploadedAt(resume.uploaded_at)}
            </p>
            {resume.parsed_at ? (
              <p className="mt-1 text-sm text-secondary">
                Parsed {formatUploadedAt(resume.parsed_at)}
              </p>
            ) : null}
            {resume.extracted_text_length != null ? (
              <p className="mt-1 text-sm text-secondary">
                Extracted text: {resume.extracted_text_length.toLocaleString("en")} characters
              </p>
            ) : null}
            {resume.evidence_id ? (
              <p className="mt-1 text-sm text-secondary">Evidence linked to this document.</p>
            ) : null}
          </div>
          <StatusBadge status={resume.status} label={resumeStatusLabel(resume.status)} />
        </div>
        {resume.skills.length > 0 ? (
          <div className="border-t border-border pt-4">
            <p className="text-sm font-medium text-ink">Skills</p>
            <ul className="mt-2 flex flex-wrap gap-2" aria-label="Resume skills">
              {resume.skills.map((skill, index) => (
                <li key={`${skill.name}-${skill.extraction_method}-${index}`} className="min-w-0 max-w-full">
                  <Badge variant="success" title={skill.name}>
                    {skill.name}
                  </Badge>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <p className="text-sm leading-6 text-secondary">
          Your resume is used alongside GitHub and project evidence. It is not treated as verified proof on its own.
        </p>
      </CardContent>
    </Card>
  );
}

export function ResumeSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
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
      <Card aria-labelledby="resume-section-title">
        <CardContent className="p-6">
          <SectionHeader
            title="Resume"
            icon="resume"
            titleId="resume-section-title"
            description="Resume management is available only to candidate accounts."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card aria-labelledby="resume-section-title">
      <CardContent className="space-y-6 p-6">
        <SectionHeader
          title="Resume"
          icon="resume"
          titleId="resume-section-title"
          description="Add your resume as one source of evidence. BeyondResume compares stated skills with verified evidence from GitHub and projects."
        />

        <div className="space-y-6" aria-live="polite">
          {currentResumeQuery.isLoading ? (
            <div role="status" aria-label="Loading current resume">
              <SkeletonCard />
            </div>
          ) : null}

          {currentResumeQuery.isError && !resumeMissing ? (
            <EmptyState
              role="alert"
              title="Could not load resume"
              description={errorMessage(currentResumeQuery.error)}
              primaryAction={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void currentResumeQuery.refetch()}
                >
                  Try again
                </Button>
              }
            />
          ) : null}

          {currentResumeQuery.data ? <CurrentResume resume={currentResumeQuery.data} /> : null}

          {resumeMissing && !isProcessing ? (
            <EmptyState
              title="No resume evidence added yet"
              description="Upload a PDF to compare your stated experience with verified project evidence."
              className="bg-background"
            />
          ) : null}

          {job ? (
            <Card className="bg-background">
              <CardContent className="space-y-3 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium text-ink">Processing status</p>
                  <StatusBadge status={job.status} />
                </div>
                {isProcessing ? (
                  <p className="text-sm text-secondary">
                    Your resume is being processed. This section updates automatically.
                  </p>
                ) : null}
                {job.status === "completed" ? (
                  <p className="text-sm text-success">
                    Resume evidence added. Text was extracted and evidence was created for this document.
                  </p>
                ) : null}
                {isTerminalFailure ? (
                  <p className="text-sm text-danger" role="alert">
                    {jobFailureMessage(job)}
                  </p>
                ) : null}
                {canRetry ? (
                  <div>
                    <Button
                      type="button"
                      variant="primary"
                      onClick={onRetry}
                      loading={retryMutation.isPending}
                    >
                      Retry processing
                    </Button>
                    {retryMutation.isError ? (
                      <p className="mt-2 text-sm text-danger" role="alert">
                        {errorMessage(retryMutation.error)}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          {jobQuery.isError ? (
            <EmptyState
              role="alert"
              title="Could not check processing status"
              description={errorMessage(jobQuery.error)}
              primaryAction={
                <Button type="button" variant="secondary" onClick={() => void jobQuery.refetch()}>
                  Check status again
                </Button>
              }
            />
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
                ref={fileInputRef}
                id="resume-file"
                name="file"
                type="file"
                accept=".pdf,application/pdf"
                onChange={onFileChange}
                disabled={isBusy}
                aria-describedby="resume-file-help"
                className="block min-h-control w-full rounded-input border border-border bg-surface px-3 py-2 text-sm text-ink file:mr-4 file:rounded-button file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring focus-visible:ring-offset-2 disabled:bg-background"
              />
              <p id="resume-file-help" className="text-sm text-secondary">
                PDF only · Maximum file size: 8 MiB
              </p>
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

            <Button
              type="submit"
              variant="primary"
              disabled={!selectedFile || isBusy}
              loading={uploadMutation.isPending || isProcessing}
            >
              {currentResumeQuery.data ? "Replace resume" : "Add resume evidence"}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}
