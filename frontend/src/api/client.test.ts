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
});
