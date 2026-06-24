import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders a console shell and switches between application workspaces", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/health")) {
        return Promise.resolve(
          new Response(JSON.stringify({ status: "ok", storage: "sqlite", queue_backend: "fastapi_background_tasks" }), {
            status: 200
          })
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
      if (url.endsWith("/runs/react-run-001")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              request_id: "react-run-001",
              current_step: "human_review",
              match_score: 91,
              risk_score: 0.18,
              human_review_status: "pending"
            }),
            { status: 200 }
          )
        );
      }
      if (url.endsWith("/traces/react-run-001")) {
        return Promise.resolve(new Response(JSON.stringify({ trace: [] }), { status: 200 }));
      }
      if (url.endsWith("/reports/react-run-001")) {
        return Promise.resolve(
          new Response(JSON.stringify({ request_id: "react-run-001", markdown: "# Report" }), { status: 200 })
        );
      }
      return Promise.resolve(new Response("{}", { status: 404 }));
    });

    render(<App />);

    await waitFor(() => expect(screen.getByText("招聘评估运营总览")).toBeInTheDocument());
    expect(screen.getByText("Agentic HR 工作台")).toBeInTheDocument();
    expect(screen.getByText("任务调度就绪")).toBeInTheDocument();
    expect(screen.getByText("待复核")).toBeInTheDocument();
    expect(screen.getByText("Agent 流程态势")).toBeInTheDocument();

    const nav = screen.getByLabelText("主导航");
    fireEvent.click(within(nav).getByRole("button", { name: /候选人库/ }));
    expect(await screen.findByRole("heading", { name: "候选人库" })).toBeInTheDocument();
    expect(screen.getByText("react-batch-001")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "react-run-001" }));
    expect(await screen.findByRole("heading", { name: "候选人评估详情" })).toBeInTheDocument();

    fireEvent.click(within(nav).getByRole("button", { name: /评估任务/ }));
    expect(await screen.findByRole("heading", { name: "创建评估任务" })).toBeInTheDocument();

    fireEvent.click(within(nav).getByRole("button", { name: /人工复核/ }));
    expect(await screen.findByRole("heading", { name: "人工复核工作台" })).toBeInTheDocument();
  });
});
