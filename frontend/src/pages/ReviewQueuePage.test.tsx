import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReviewQueuePage } from "./ReviewQueuePage";

describe("ReviewQueuePage", () => {
  it("submits human review feedback for a pending run", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <ReviewQueuePage
        runs={[{ request_id: "review-001", human_review_status: "pending", risk_score: 0.52 }]}
        onSubmitReview={onSubmit}
      />
    );

    fireEvent.change(screen.getByLabelText("复核结论"), { target: { value: "approve" } });
    fireEvent.change(screen.getByLabelText("复核反馈"), { target: { value: "Evidence checked." } });
    fireEvent.click(screen.getByRole("button", { name: "保存复核" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith("review-001", {
      decision: "approve",
      feedback: "Evidence checked.",
      reviewer: "react-cabin"
    });
  });
});
