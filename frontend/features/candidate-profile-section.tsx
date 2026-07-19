"use client";

import { useEffect, useState, type FormEvent } from "react";

import { ApiClientError } from "@/lib/api/error";
import type {
  CandidateProfilePatchRequest,
  CandidateProfileResponse
} from "@/lib/api/types/candidate";
import {
  useCandidateProfileQuery,
  useUpdateCandidateProfile
} from "@/lib/candidate/hooks";

type NullableBooleanInput = "" | "true" | "false";

type ProfileFormValues = {
  display_name: string;
  target_role: string;
  location: string;
  remote_preference: string;
  english_level: string;
  availability: string;
  summary: string;
  data_processing_consent: NullableBooleanInput;
  salary_expectation: string;
  preferred_employment_type: string;
  relocation_readiness: NullableBooleanInput;
  portfolio_url: string;
  linkedin_url: string;
};

type StringFieldName = Exclude<
  keyof ProfileFormValues,
  "summary" | "data_processing_consent" | "relocation_readiness"
>;

const textFields: ReadonlyArray<{
  name: StringFieldName;
  label: string;
  maxLength?: number;
  type?: "text" | "url";
}> = [
  { name: "display_name", label: "Display name", maxLength: 150 },
  { name: "target_role", label: "Target role", maxLength: 80 },
  { name: "location", label: "Location", maxLength: 80 },
  { name: "remote_preference", label: "Remote preference", maxLength: 50 },
  { name: "english_level", label: "English level", maxLength: 50 },
  { name: "availability", label: "Availability", maxLength: 100 },
  { name: "salary_expectation", label: "Salary expectation", maxLength: 100 },
  {
    name: "preferred_employment_type",
    label: "Preferred employment type",
    maxLength: 50
  },
  { name: "portfolio_url", label: "Portfolio URL", type: "url" },
  { name: "linkedin_url", label: "LinkedIn URL", type: "url" }
];

const inputClassName =
  "min-h-control w-full rounded-input border border-border bg-surface px-3 text-ink outline-none focus:border-primary focus:ring-2 focus:ring-primary disabled:bg-background";

function toBooleanInput(value: boolean | null): NullableBooleanInput {
  if (value === null) {
    return "";
  }

  return value ? "true" : "false";
}

function fromBooleanInput(value: NullableBooleanInput): boolean | null {
  if (value === "") {
    return null;
  }

  return value === "true";
}

function parseBooleanInput(value: string): NullableBooleanInput {
  if (value === "true" || value === "false") {
    return value;
  }

  return "";
}

function toFormValues(profile: CandidateProfileResponse): ProfileFormValues {
  return {
    display_name: profile.display_name ?? "",
    target_role: profile.target_role ?? "",
    location: profile.location ?? "",
    remote_preference: profile.remote_preference ?? "",
    english_level: profile.english_level ?? "",
    availability: profile.availability ?? "",
    summary: profile.summary ?? "",
    data_processing_consent: toBooleanInput(profile.data_processing_consent),
    salary_expectation: profile.salary_expectation ?? "",
    preferred_employment_type: profile.preferred_employment_type ?? "",
    relocation_readiness: toBooleanInput(profile.relocation_readiness),
    portfolio_url: profile.portfolio_url ?? "",
    linkedin_url: profile.linkedin_url ?? ""
  };
}

function normalizeString(value: string): string | null {
  const normalized = value.trim();
  return normalized === "" ? null : normalized;
}

function buildProfilePatch(
  values: ProfileFormValues,
  profile: CandidateProfileResponse
): CandidateProfilePatchRequest {
  const patch: CandidateProfilePatchRequest = {};

  for (const { name } of textFields) {
    const value = normalizeString(values[name]);
    if (value !== profile[name]) {
      patch[name] = value;
    }
  }

  const summary = normalizeString(values.summary);
  if (summary !== profile.summary) {
    patch.summary = summary;
  }

  const dataProcessingConsent = fromBooleanInput(values.data_processing_consent);
  if (dataProcessingConsent !== profile.data_processing_consent) {
    patch.data_processing_consent = dataProcessingConsent;
  }

  const relocationReadiness = fromBooleanInput(values.relocation_readiness);
  if (relocationReadiness !== profile.relocation_readiness) {
    patch.relocation_readiness = relocationReadiness;
  }

  return patch;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  return "The profile request failed. Please try again.";
}

export function CandidateProfileSection({ enabled }: Readonly<{ enabled: boolean }>) {
  const profileQuery = useCandidateProfileQuery(enabled);
  const updateMutation = useUpdateCandidateProfile();
  const [formValues, setFormValues] = useState<ProfileFormValues | null>(null);

  useEffect(() => {
    if (profileQuery.data && formValues === null) {
      setFormValues(toFormValues(profileQuery.data));
    }
  }, [formValues, profileQuery.data]);

  useEffect(() => {
    if (updateMutation.data) {
      setFormValues(toFormValues(updateMutation.data));
    }
  }, [updateMutation.data]);

  if (!enabled) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6"
        aria-labelledby="profile-section-title"
      >
        <h2 id="profile-section-title" className="text-xl font-semibold text-ink">
          Candidate Profile
        </h2>
        <p className="mt-3 text-sm leading-6 text-secondary">
          Candidate profile management is available only to candidate accounts.
        </p>
      </section>
    );
  }

  if (profileQuery.isLoading || (profileQuery.data && formValues === null)) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6"
        aria-labelledby="profile-section-title"
      >
        <h2 id="profile-section-title" className="text-xl font-semibold text-ink">
          Candidate Profile
        </h2>
        <p className="mt-4 text-sm text-secondary" role="status">
          Loading profile…
        </p>
      </section>
    );
  }

  if (profileQuery.isError || !profileQuery.data || !formValues) {
    return (
      <section
        className="rounded-card border border-border bg-surface p-6"
        aria-labelledby="profile-section-title"
      >
        <h2 id="profile-section-title" className="text-xl font-semibold text-ink">
          Candidate Profile
        </h2>
        <p className="mt-4 text-sm text-danger" role="alert">
          {errorMessage(profileQuery.error)}
        </p>
        <button
          type="button"
          onClick={() => void profileQuery.refetch()}
          className="mt-4 min-h-control rounded-button border border-border bg-surface px-4 text-sm font-medium text-ink"
        >
          Try again
        </button>
      </section>
    );
  }

  const patch = buildProfilePatch(formValues, profileQuery.data);
  const isDirty = Object.keys(patch).length > 0;
  const isSaving = updateMutation.isPending;

  function updateStringField(name: StringFieldName | "summary", value: string) {
    setFormValues((current) => (current ? { ...current, [name]: value } : current));
  }

  function updateBooleanField(
    name: "data_processing_consent" | "relocation_readiness",
    value: NullableBooleanInput
  ) {
    setFormValues((current) => (current ? { ...current, [name]: value } : current));
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSaving || Object.keys(patch).length === 0) {
      return;
    }

    updateMutation.mutate(patch);
  }

  return (
    <section
      className="rounded-card border border-border bg-surface p-6"
      aria-labelledby="profile-section-title"
    >
      <div>
        <h2 id="profile-section-title" className="text-xl font-semibold text-ink">
          Candidate Profile
        </h2>
        <p className="mt-2 text-sm text-secondary">
          Onboarding status:{" "}
          <span className="capitalize">
            {profileQuery.data.onboarding_status.replaceAll("_", " ")}
          </span>
        </p>
      </div>

      <form className="mt-6 space-y-6" onSubmit={onSubmit}>
        <div className="grid gap-6 lg:grid-cols-2">
          {textFields.map(({ name, label, maxLength, type = "text" }) => (
            <div className="space-y-2" key={name}>
              <label htmlFor={`profile-${name}`} className="block text-sm font-medium text-ink">
                {label}
              </label>
              <input
                id={`profile-${name}`}
                name={name}
                type={type}
                maxLength={maxLength}
                value={formValues[name]}
                onChange={(event) => updateStringField(name, event.target.value)}
                disabled={isSaving}
                className={inputClassName}
              />
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <label htmlFor="profile-summary" className="block text-sm font-medium text-ink">
            Summary
          </label>
          <textarea
            id="profile-summary"
            name="summary"
            rows={5}
            value={formValues.summary}
            onChange={(event) => updateStringField("summary", event.target.value)}
            disabled={isSaving}
            className={`${inputClassName} py-3`}
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-2">
            <label
              htmlFor="profile-data-processing-consent"
              className="block text-sm font-medium text-ink"
            >
              Data processing consent
            </label>
            <select
              id="profile-data-processing-consent"
              name="data_processing_consent"
              value={formValues.data_processing_consent}
              onChange={(event) =>
                updateBooleanField(
                  "data_processing_consent",
                  parseBooleanInput(event.target.value)
                )
              }
              disabled={isSaving}
              className={inputClassName}
            >
              <option value="">Not specified</option>
              <option value="true">Granted</option>
              <option value="false">Not granted</option>
            </select>
          </div>

          <div className="space-y-2">
            <label
              htmlFor="profile-relocation-readiness"
              className="block text-sm font-medium text-ink"
            >
              Relocation readiness
            </label>
            <select
              id="profile-relocation-readiness"
              name="relocation_readiness"
              value={formValues.relocation_readiness}
              onChange={(event) =>
                updateBooleanField(
                  "relocation_readiness",
                  parseBooleanInput(event.target.value)
                )
              }
              disabled={isSaving}
              className={inputClassName}
            >
              <option value="">Not specified</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>

        {updateMutation.isError ? (
          <p className="text-sm text-danger" role="alert">
            {errorMessage(updateMutation.error)}
          </p>
        ) : null}

        {updateMutation.isSuccess && !isDirty ? (
          <p className="text-sm text-success" role="status">
            Profile saved.
          </p>
        ) : null}

        <button
          type="submit"
          disabled={!isDirty || isSaving}
          className="min-h-control rounded-button bg-primary px-6 text-sm font-medium text-white disabled:opacity-60"
        >
          {isSaving ? "Saving…" : "Save profile"}
        </button>
      </form>
    </section>
  );
}
