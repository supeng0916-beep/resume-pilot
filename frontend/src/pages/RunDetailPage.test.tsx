import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RunDetailPage } from "./RunDetailPage";

describe("RunDetailPage", () => {
  it("renders trace, report and email sections for one run", () => {
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
        onSendReportEmail={vi.fn()}
      />
    );

    expect(screen.getByText("detail-001")).toBeInTheDocument();
    expect(screen.getByText("流程追踪")).toBeInTheDocument();
    expect(screen.getByText("候选人评估报告")).toBeInTheDocument();
    expect(screen.getByText("发送评估报告")).toBeInTheDocument();
    expect(screen.getByText("Matched Python")).toBeInTheDocument();
    expect(screen.getByText("# Report")).toBeInTheDocument();
  });

  it("submits report email delivery request", async () => {
    const onSendReportEmail = vi.fn().mockResolvedValue({
      id: 1,
      request_id: "detail-001",
      recipient: "hr@example.com",
      subject: "报告",
      sent: true,
      message: "已发送"
    });

    render(
      <RunDetailPage
        run={{
          request_id: "detail-001",
          current_step: "human_review",
          match_score: 82,
          risk_score: 0.31,
          human_review_status: "pending"
        }}
        trace={[]}
        report={{ request_id: "detail-001", markdown: "# Report" }}
        onSendReportEmail={onSendReportEmail}
      />
    );

    fireEvent.change(screen.getByPlaceholderText("hr-lead@example.com"), {
      target: { value: "hr@example.com" }
    });
    fireEvent.click(screen.getByRole("button", { name: /发送报告/ }));

    await waitFor(() => expect(onSendReportEmail).toHaveBeenCalledWith(
      expect.objectContaining({ request_id: "detail-001", recipient: "hr@example.com" })
    ));
    expect(await screen.findByText("已发送")).toBeInTheDocument();
  });
});
