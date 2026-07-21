import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResumeSection } from "@/features/resume-section";
import { ApiClientError } from "@/lib/api/error";

const currentResumeQuery = vi.fn();
const uploadMutation = vi.fn();
const retryMutation = vi.fn();
const resumeJobQuery = vi.fn();

vi.mock("@/lib/resume/hooks", () => ({
  useCurrentResumeQuery: () => currentResumeQuery(),
  useResumeJobQuery: () => resumeJobQuery(),
  useRetryResumeMutation: () => retryMutation(),
  useUploadResumeMutation: () => uploadMutation()
}));

vi.mock("@/lib/jobs/hooks", () => ({
  isTerminalJobStatus: (status: string) => ["completed", "failed", "cancelled", "expired"].includes(status)
}));

function missingResumeQuery() {
  return {
    data: null,
    error: new ApiClientError({ status: 404, code: "RESUME_NOT_FOUND", message: "Current resume not found" }),
    isError: true,
    isFetching: false,
    isLoading: false,
    refetch: vi.fn()
  };
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("ResumeSection", () => {
  it("positions a PDF resume as an additional evidence source and submits the selected File once", () => {
    const mutate = vi.fn();
    currentResumeQuery.mockReturnValue(missingResumeQuery());
    uploadMutation.mockReturnValue({ isError: false, isPending: false, mutate, reset: vi.fn() });
    retryMutation.mockReturnValue({ isError: false, isPending: false, mutate: vi.fn() });
    resumeJobQuery.mockReturnValue({ data: undefined, isError: false, refetch: vi.fn() });

    render(<ResumeSection enabled />);

    expect(screen.getByText("No resume evidence added yet")).toBeInTheDocument();
    expect(screen.getByText("PDF only · Maximum file size: 8 MiB")).toBeInTheDocument();
    const input = screen.getByLabelText("Resume file");
    const file = new File(["%PDF-1.4"], "resume.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Add resume evidence" }));

    expect(mutate).toHaveBeenCalledTimes(1);
    expect(mutate.mock.calls[0][0]).toBe(file);
    expect(input).toHaveAttribute("aria-describedby", "resume-file-help");
  });

  it("uses a safe storage error message instead of database terminology", () => {
    currentResumeQuery.mockReturnValue(missingResumeQuery());
    uploadMutation.mockReturnValue({
      isError: true,
      isPending: false,
      error: new ApiClientError({ status: 500, code: "DATABASE_ERROR", message: "Database operation failed" }),
      mutate: vi.fn(),
      reset: vi.fn()
    });
    retryMutation.mockReturnValue({ isError: false, isPending: false, mutate: vi.fn() });
    resumeJobQuery.mockReturnValue({ data: undefined, isError: false, refetch: vi.fn() });

    render(<ResumeSection enabled />);

    expect(screen.getByRole("alert")).toHaveTextContent("Resume could not be saved. Please try again.");
    expect(document.body.textContent).not.toContain("Database operation failed");
  });
});
