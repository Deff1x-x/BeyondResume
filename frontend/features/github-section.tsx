"use client";

import { useState, type FormEvent } from "react";

import { GitHubEvidenceList } from "@/features/github-evidence-list";
import { ApiClientError } from "@/lib/api/error";
import type { GitHubRepositoryResponse } from "@/lib/api/types/github";
import type { JobPollingResponse } from "@/lib/api/types/jobs";
import {
  useConnectGitHubRepository,
  useDeleteGitHubRepository,
  useGitHubRepositoriesQuery,
  useGitHubRepositoryQuery,
  useGitHubScanJobQuery,
  useStartGitHubScan
} from "@/lib/github/hooks";
import { isTerminalJobStatus } from "@/lib/jobs/hooks";

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The GitHub request failed. Please try again.";
}

function isProfileRequired(error: unknown): boolean {
  return error instanceof ApiClientError && error.code === "CANDIDATE_PROFILE_REQUIRED";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function jobStatusLabel(job: JobPollingResponse | null): string {
  if (!job) {
    return "Not analyzed";
  }

  switch (job.status) {
    case "pending":
      return "Queued";
    case "running":
      return "Analyzing…";
    case "completed":
      return "Analyzed";
    case "failed":
      return "Analysis failed";
    case "cancelled":
      return "Analysis cancelled";
    case "expired":
      return "Analysis expired";
  }
}

function jobFailureMessage(job: JobPollingResponse): string {
  if (job.error_message) {
    return job.error_message;
  }

  return "Repository analysis failed. Run the analysis again.";
}

function RepositoryDetails({ repositoryId }: Readonly<{ repositoryId: string }>) {
  const detailQuery = useGitHubRepositoryQuery(repositoryId, true);

  if (detailQuery.isLoading) {
    return (
      <p className="mt-4 text-sm text-secondary" role="status">
        Loading repository details…
      </p>
    );
  }

  if (detailQuery.isError) {
    return (
      <p className="mt-4 text-sm text-danger" role="alert">
        {errorMessage(detailQuery.error)}
      </p>
    );
  }

  const detail = detailQuery.data;
  if (!detail) {
    return null;
  }

  if (!detail.snapshot) {
    return (
      <p className="mt-4 text-sm text-secondary">
        This repository has not been analyzed yet. Run an analysis to collect repository
        data and skills.
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-4 border-t border-border pt-4">
      <div>
        <p className="text-sm font-medium text-ink">Description</p>
        <p className="mt-1 text-sm text-secondary">
          {detail.snapshot.description ?? "No description provided."}
        </p>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-secondary">
        <span>
          Files: <span className="font-medium text-ink">{detail.snapshot.file_count}</span>
        </span>
        <span>
          Manifests:{" "}
          <span className="font-medium text-ink">{detail.snapshot.manifest_count}</span>
        </span>
        {detail.snapshot.is_archived ? <span className="text-danger">Archived</span> : null}
      </div>

      {detail.snapshot.languages.length > 0 ? (
        <div>
          <p className="text-sm font-medium text-ink">Languages</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {detail.snapshot.languages.map((language) => (
              <li
                key={language}
                className="rounded-button border border-border bg-background px-3 py-1 text-sm text-ink"
              >
                {language}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div>
        <p className="text-sm font-medium text-ink">Detected skills</p>
        {detail.skills.length === 0 ? (
          <p className="mt-1 text-sm text-secondary">
            No skills were detected from this repository yet.
          </p>
        ) : (
          <ul className="mt-2 flex flex-wrap gap-2">
            {detail.skills.map((skill) => (
              <li
                key={`${skill.name}-${skill.category}`}
                className="rounded-button border border-border bg-background px-3 py-1 text-sm text-ink"
              >
                {skill.name}
                <span className="ml-2 text-secondary">{skill.category}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <p className="text-sm font-medium text-ink">Evidence</p>
        <div className="mt-2">
          <GitHubEvidenceList repositoryId={repositoryId} />
        </div>
      </div>
    </div>
  );
}

function RepositoryCard({ repository }: Readonly<{ repository: GitHubRepositoryResponse }>) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [startedJobId, setStartedJobId] = useState<string | null>(null);
  const startScanMutation = useStartGitHubScan();
  const deleteMutation = useDeleteGitHubRepository();

  const serverJob = repository.job;
  const serverActiveJobId =
    serverJob && !isTerminalJobStatus(serverJob.status) ? serverJob.id : null;
  const activeJobId = startedJobId ?? serverActiveJobId;
  const jobQuery = useGitHubScanJobQuery(activeJobId, repository.id);

  const job = jobQuery.data ?? serverJob;
  const isAnalysisActive =
    startScanMutation.isPending || (job !== null && !isTerminalJobStatus(job.status));
  const isBusy = isAnalysisActive || deleteMutation.isPending;

  function onAnalyze() {
    if (isBusy) {
      return;
    }
    setConfirmingDelete(false);
    startScanMutation.mutate(repository.id, {
      onSuccess: (startedJob) => {
        setStartedJobId(startedJob.id);
      }
    });
  }

  function onDelete() {
    if (deleteMutation.isPending) {
      return;
    }
    if (!confirmingDelete) {
      setConfirmingDelete(true);
      return;
    }
    deleteMutation.mutate(repository.id);
  }

  return (
    <div className="rounded-card border border-border bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="break-all text-sm font-medium text-ink">{repository.repository_url}</p>
          <p className="mt-1 text-sm text-secondary" aria-live="polite">
            Status: <span className="font-medium text-ink">{jobStatusLabel(job)}</span>
            {job?.status === "completed" && job.completed_at
              ? ` · Last analyzed ${formatDate(job.completed_at)}`
              : null}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setDetailsOpen((open) => !open)}
            className="min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
          >
            {detailsOpen ? "Hide details" : "Details"}
          </button>
          <button
            type="button"
            onClick={onAnalyze}
            disabled={isBusy}
            className="min-h-control rounded-button bg-primary px-4 text-sm font-medium text-white disabled:opacity-60"
          >
            {isAnalysisActive ? "Analyzing…" : job ? "Re-run analysis" : "Analyze"}
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={deleteMutation.isPending}
            className="min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-danger disabled:opacity-60"
          >
            {deleteMutation.isPending
              ? "Deleting…"
              : confirmingDelete
                ? "Confirm delete"
                : "Delete"}
          </button>
        </div>
      </div>

      {job && isTerminalJobStatus(job.status) && job.status !== "completed" ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {jobFailureMessage(job)}
        </p>
      ) : null}

      {startScanMutation.isError ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {errorMessage(startScanMutation.error)}
        </p>
      ) : null}

      {jobQuery.isError ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {errorMessage(jobQuery.error)}
        </p>
      ) : null}

      {deleteMutation.isError ? (
        <p className="mt-3 text-sm text-danger" role="alert">
          {errorMessage(deleteMutation.error)}
        </p>
      ) : null}

      {detailsOpen ? <RepositoryDetails repositoryId={repository.id} /> : null}
    </div>
  );
}

export function GitHubSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const repositoriesQuery = useGitHubRepositoriesQuery(enabled);
  const connectMutation = useConnectGitHubRepository();

  function onConnect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUrl = repositoryUrl.trim();
    if (!trimmedUrl || connectMutation.isPending) {
      return;
    }

    connectMutation.mutate(
      { repository_url: trimmedUrl },
      {
        onSuccess: () => {
          setRepositoryUrl("");
        }
      }
    );
  }

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
        aria-labelledby="github-section-title"
      >
        <h2 id="github-section-title" className="text-xl font-semibold text-ink">
          GitHub
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          GitHub integration is available only to candidate accounts.
        </p>
      </section>
    );
  }

  const repositories = repositoriesQuery.data ?? [];
  const showConnectForm = repositoriesQuery.isSuccess && repositories.length === 0;

  return (
    <section
      className="rounded-card border border-border bg-surface p-6 lg:col-span-2"
      aria-labelledby="github-section-title"
    >
      <h2 id="github-section-title" className="text-xl font-semibold text-ink">
        GitHub
      </h2>
      <p className="mt-2 text-sm text-secondary">
        Connect a public GitHub repository to analyze it and add detected skills to your
        profile.
      </p>

      <div className="mt-6 space-y-6">
        {repositoriesQuery.isLoading ? (
          <p className="text-sm text-secondary" role="status">
            Loading repositories…
          </p>
        ) : null}

        {repositoriesQuery.isError ? (
          <div>
            <p className="text-sm text-danger" role="alert">
              {errorMessage(repositoriesQuery.error)}
            </p>
            <button
              type="button"
              onClick={() => void repositoriesQuery.refetch()}
              className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
            >
              Try again
            </button>
          </div>
        ) : null}

        {repositories.map((repository) => (
          <RepositoryCard key={repository.id} repository={repository} />
        ))}

        {showConnectForm ? (
          <div className="rounded-card border border-border bg-background p-4">
            <p className="text-sm font-medium text-ink">No repository connected</p>
            <p className="mt-2 text-sm text-secondary">
              Add a public repository URL, for example https://github.com/owner/repository.
            </p>

            <form className="mt-4 space-y-4" onSubmit={onConnect}>
              <div className="space-y-2">
                <label htmlFor="github-repository-url" className="block text-sm font-medium text-ink">
                  Repository URL
                </label>
                <input
                  id="github-repository-url"
                  name="repository_url"
                  type="url"
                  value={repositoryUrl}
                  onChange={(event) => setRepositoryUrl(event.target.value)}
                  disabled={connectMutation.isPending}
                  maxLength={2048}
                  placeholder="https://github.com/owner/repository"
                  className="min-h-control w-full rounded-input border border-border bg-surface px-3 text-sm text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background"
                />
              </div>

              {connectMutation.isError ? (
                <div>
                  <p className="text-sm text-danger" role="alert">
                    {errorMessage(connectMutation.error)}
                  </p>
                  {isProfileRequired(connectMutation.error) ? (
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
                disabled={!repositoryUrl.trim() || connectMutation.isPending}
                className="min-h-control rounded-button bg-primary px-6 text-sm font-medium text-white disabled:opacity-60"
              >
                {connectMutation.isPending ? "Connecting…" : "Connect repository"}
              </button>
            </form>
          </div>
        ) : null}

        {repositoriesQuery.isSuccess && repositories.length > 0 ? (
          <p className="text-sm text-secondary">
            One repository can be connected per profile. Delete the current repository to
            connect a different one.
          </p>
        ) : null}
      </div>
    </section>
  );
}
