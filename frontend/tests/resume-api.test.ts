import { afterEach, describe, expect, it, vi } from "vitest";

import { uploadResume } from "@/lib/api/resume";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("uploadResume", () => {
  it("sends the File in the backend's multipart file field without forcing Content-Type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ resume_id: "resume-id", job_id: "job-id" }), { status: 202 })
    );
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["%PDF-1.4"], "resume.pdf", { type: "application/pdf" });

    await uploadResume(file);

    const [, request] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request.body).toBeInstanceOf(FormData);
    expect((request.body as FormData).get("file")).toBe(file);
    expect(new Headers(request.headers).has("Content-Type")).toBe(false);
  });
});
