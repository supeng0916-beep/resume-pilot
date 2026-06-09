import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RunDetailPage } from "./RunDetailPage";

describe("RunDetailPage", () => {
  it("renders trace and report sections for one run", () => {
    render(
      <RunDetailPage
        run={{
          request_id: "detail-001",
          current_step: "human_review",
          match_score: 82,
          risk_score: 0.31,
          human_review_status: "pending"
        }}
        trace={[{ node: "matcher", output_summary: "Matched Python" }]}
        report={{ request_id: "detail-001", markdown: "# Report" }}
      />
    );

    expect(screen.getByText("detail-001")).toBeInTheDocument();
    expect(screen.getByText("流程追踪")).toBeInTheDocument();
    expect(screen.getByText("候选人评估报告")).toBeInTheDocument();
    expect(screen.getByText("Matched Python")).toBeInTheDocument();
    expect(screen.getByText("# Report")).toBeInTheDocument();
  });
});
