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

  it("lists persisted batches from the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        batches: [{ request_id: "batch-001", candidate_count: 2, top_candidate_request_id: "batch-001-001-a" }]
      })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const batches = await client.listBatches();

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/batches");
    expect(batches[0].candidate_count).toBe(2);
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

  it("uploads resume files through multipart batch endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        request_id: "upload-001",
        candidate_count: 1,
        ranked_candidates: [],
        batch_report: "# upload"
      })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });
    const file = new File(["Alice Python"], "alice.txt", { type: "text/plain" });

    const result = await client.uploadBatchEvaluation({
      request_id: "upload-001",
      jd_text: "Backend requires Python",
      risk_model_path: "models/review_risk_model.json",
      files: [file]
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/batch-evaluations/uploads",
      expect.objectContaining({ method: "POST", body: expect.any(FormData) })
    );
    expect(result.batch_report).toBe("# upload");
  });
});
