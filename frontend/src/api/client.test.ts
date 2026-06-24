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

  it("sends report email through FastAPI", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 1,
        request_id: "run-001",
        recipient: "hr@example.com",
        subject: "报告",
        sent: true,
        message: "sent"
      })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const delivery = await client.sendReportEmail({
      request_id: "run-001",
      recipient: "hr@example.com",
      subject: "报告"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/emails/report",
      expect.objectContaining({ method: "POST" })
    );
    expect(delivery.sent).toBe(true);
  });

  it("deletes one run through the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ request_id: "run-001", deleted: true })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const result = await client.deleteRun("run-001");

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/runs/run-001", { method: "DELETE" });
    expect(result.deleted).toBe(true);
  });

  it("clears all runs through the backend", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ deleted_count: 3 })
    });
    const client = createApiClient({ baseUrl: "http://api.test", fetchImpl: fetchMock });

    const result = await client.clearRuns();

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/runs", { method: "DELETE" });
    expect(result.deleted_count).toBe(3);
  });
});
