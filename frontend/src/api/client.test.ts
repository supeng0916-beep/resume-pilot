import { afterEach, describe, expect, it, vi } from "vitest";
import { createApiClient } from "./client";

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("lists persisted runs from the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        runs: [{ request_id: "run-001", match_score: 88.5 }]
      })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const runs = await client.listRuns();

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/runs");
    expect(runs[0].request_id).toBe("run-001");
  });

  it("creates batch evaluations through FastAPI", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        request_id: "batch-001",
        candidate_count: 1,
        ranked_candidates: [],
        batch_report: "# report"
      })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const result = await client.createBatchEvaluation({
      request_id: "batch-001",
      resumes: [{ candidate_id: "candidate-a", resume_text: "Python FastAPI" }]
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/batch-evaluations",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.candidate_count).toBe(1);
  });
});
