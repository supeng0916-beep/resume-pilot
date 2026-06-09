import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders persisted runs and batches from FastAPI", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/health")) {
        return Promise.resolve(
          new Response(JSON.stringify({ status: "ok", storage: "sqlite" }), { status: 200 })
        );
      }
      if (url.endsWith("/runs")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              runs: [
                {
                  request_id: "react-run-001",
                  current_step: "human_review",
                  match_score: 91,
                  risk_score: 0.18,
                  human_review_status: "pending"
                }
              ]
            }),
            { status: 200 }
          )
        );
      }
      if (url.endsWith("/batches")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              batches: [
                {
                  request_id: "react-batch-001",
                  candidate_count: 2,
                  top_candidate_request_id: "react-batch-001-001-alice",
                  ranked_candidates: []
                }
              ]
            }),
            { status: 200 }
          )
        );
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });

    render(<App />);

    await waitFor(() => expect(screen.getByText("react-run-001")).toBeInTheDocument());
    expect(screen.getByText("招聘评估工作台")).toBeInTheDocument();
    expect(screen.getByText("今日待复核")).toBeInTheDocument();
    expect(screen.getByText("候选人批次")).toBeInTheDocument();
    expect(screen.getByText("最近评估批次")).toBeInTheDocument();
    expect(screen.getAllByText("创建评估批次").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("react-batch-001")).toBeInTheDocument();
    expect(screen.getByText("human_review")).toBeInTheDocument();
  });
});
