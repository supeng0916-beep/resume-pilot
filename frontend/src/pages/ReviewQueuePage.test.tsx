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

    fireEvent.change(screen.getByLabelText("Decision"), { target: { value: "approve" } });
    fireEvent.change(screen.getByLabelText("Feedback"), { target: { value: "Evidence checked." } });
    fireEvent.click(screen.getByRole("button", { name: "Save review" }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith("review-001", {
      decision: "approve",
      feedback: "Evidence checked.",
      reviewer: "react-cabin"
    });
  });
});
