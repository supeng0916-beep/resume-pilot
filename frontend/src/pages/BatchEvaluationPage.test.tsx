import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BatchEvaluationPage } from "./BatchEvaluationPage";

describe("BatchEvaluationPage", () => {
  it("submits textarea resumes as a batch evaluation", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<BatchEvaluationPage onSubmit={onSubmit} onUploadSubmit={vi.fn()} isRunning={false} />);

    fireEvent.change(screen.getByLabelText("Request ID"), { target: { value: "batch-ui-001" } });
    fireEvent.change(screen.getByLabelText("Job description"), { target: { value: "Backend requires Python" } });
    fireEvent.change(screen.getByLabelText("Resume texts"), {
      target: { value: "Alice Python FastAPI\n---\nBob React TypeScript" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Run batch" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith({
      request_id: "batch-ui-001",
      jd_text: "Backend requires Python",
      risk_model_path: "models/review_risk_model.json",
      enable_llm_structured_extraction: false,
      enable_llm_report_enhancement: false,
      resumes: [
        { candidate_id: "candidate-001", resume_text: "Alice Python FastAPI" },
        { candidate_id: "candidate-002", resume_text: "Bob React TypeScript" }
      ]
    });
  });

  it("submits uploaded files through the upload callback", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onUploadSubmit = vi.fn().mockResolvedValue(undefined);
    render(<BatchEvaluationPage onSubmit={onSubmit} onUploadSubmit={onUploadSubmit} isRunning={false} />);
    const file = new File(["Alice Python"], "alice.txt", { type: "text/plain" });

    fireEvent.change(screen.getByLabelText("Resume files"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload and run" }));

    await waitFor(() => expect(onUploadSubmit).toHaveBeenCalledTimes(1));
    expect(onUploadSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        risk_model_path: "models/review_risk_model.json",
        files: [file]
      })
    );
  });
});
