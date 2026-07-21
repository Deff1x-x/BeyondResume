"use client";

import { useState, type FormEvent } from "react";

import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { SectionHeader } from "@/components/ui/section-header";
import { SkeletonCard } from "@/components/ui/skeleton";
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
      return "Analyzing";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "cancelled":
      return "Cancelled";
    case "expired":
      return "Expired";
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
      <div className="mt-4" role="status" aria-label="Loading repository details">
        <SkeletonCard />
      </div>
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
        {detail.snapshot.is_archived ? (
          <Badge variant="danger">Archived</Badge>
        ) : null}
      </div>

      {detail.snapshot.languages.length > 0 ? (
        <div>
          <p className="text-sm font-medium text-ink">Languages</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {detail.snapshot.languages.map((language) => (
              <li key={language} className="min-w-0 max-w-full">
                <Badge variant="neutral">{language}</Badge>
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
              <li key={`${skill.name}-${skill.category}`} className="min-w-0 max-w-full">
                <Badge variant="neutral" title={`${skill.name} · ${skill.category}`}>
                  {skill.name}
                  <span className="ml-1.5 text-secondary">{skill.category}</span>
                </Badge>
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
    <Card className="bg-background">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <p className="break-all text-sm font-medium text-ink">{repository.repository_url}</p>
            <div className="flex flex-wrap items-center gap-2" aria-live="polite">
              <StatusBadge
                status={job?.status ?? "unverified"}
                label={jobStatusLabel(job)}
              />
              {job?.status === "completed" && job.completed_at ? (
                <span className="text-sm text-secondary">
                  Last analyzed {formatDate(job.completed_at)}
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDetailsOpen((open) => !open)}
              aria-expanded={detailsOpen}
            >
              {detailsOpen ? "Hide details" : "Details"}
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={onAnalyze}
              disabled={isBusy}
              loading={isAnalysisActive}
            >
              {job ? "Re-run analysis" : "Analyze"}
            </Button>
            <Button
              type="button"
              variant={confirmingDelete ? "destructive" : "secondary"}
              onClick={onDelete}
              loading={deleteMutation.isPending}
              className={!confirmingDelete ? "text-danger" : undefined}
            >
              {confirmingDelete ? "Confirm delete" : "Delete"}
            </Button>
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
      </CardContent>
    </Card>
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
      <Card className="lg:col-span-2" aria-labelledby="github-section-title">
        <CardContent className="p-6">
          <SectionHeader
            title="GitHub"
            icon="github"
            titleId="github-section-title"
            description="GitHub integration is available only to candidate accounts."
          />
        </CardContent>
      </Card>
    );
  }

  const repositories = repositoriesQuery.data ?? [];
  const showConnectForm = repositoriesQuery.isSuccess;

  return (
    <Card className="lg:col-span-2" aria-labelledby="github-section-title">
      <CardContent className="space-y-6 p-6">
        <SectionHeader
          title="GitHub"
          icon="github"
          titleId="github-section-title"
          description="Connect a public GitHub repository to analyze it and add detected skills to your profile."
        />

        <div className="space-y-6">
          {repositoriesQuery.isLoading ? (
            <div
              className="space-y-3"
              role="status"
              aria-label="Loading repositories"
            >
              <SkeletonCard />
            </div>
          ) : null}

          {repositoriesQuery.isError ? (
            <EmptyState
              role="alert"
              title="Could not load repositories"
              description={errorMessage(repositoriesQuery.error)}
              primaryAction={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void repositoriesQuery.refetch()}
                >
                  Try again
                </Button>
              }
            />
          ) : null}

          {repositories.map((repository) => (
            <RepositoryCard key={repository.id} repository={repository} />
          ))}

          {showConnectForm ? (
            <Card className="bg-background">
              <CardContent className="space-y-4 p-4">
                <div>
                  <p className="text-sm font-medium text-ink">No repository connected</p>
                  <p className="mt-2 text-sm text-secondary">
                    Add a public repository URL, for example https://github.com/owner/repository.
                  </p>
                </div>

                <form className="space-y-4" onSubmit={onConnect}>
                  <div className="space-y-2">
                    <label
                      htmlFor="github-repository-url"
                      className="block text-sm font-medium text-ink"
                    >
                      Repository URL
                    </label>
                    <Input
                      id="github-repository-url"
                      name="repository_url"
                      type="url"
                      value={repositoryUrl}
                      onChange={(event) => setRepositoryUrl(event.target.value)}
                      disabled={connectMutation.isPending}
                      maxLength={2048}
                      placeholder="https://github.com/owner/repository"
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

                  <Button
                    type="submit"
                    variant="primary"
                    disabled={!repositoryUrl.trim()}
                    loading={connectMutation.isPending}
                  >
                    Connect repository
                  </Button>
                </form>
              </CardContent>
            </Card>
          ) : null}

          {repositoriesQuery.isSuccess && repositories.length > 0 ? (
            <p className="text-sm text-secondary">
              Connect additional public repositories to aggregate evidence across your work.
            </p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
