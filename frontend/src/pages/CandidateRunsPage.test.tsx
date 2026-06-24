import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CandidateRunsPage } from "./CandidateRunsPage";

describe("CandidateRunsPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("deletes one run after confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const onDeleteRun = vi.fn().mockResolvedValue(undefined);

    render(
      <CandidateRunsPage
        runs={[{ request_id: "candidate-run-001", current_step: "reporting", human_review_status: "pending" }]}
        batches={[]}
        onSelectRun={vi.fn()}
        onDeleteRun={onDeleteRun}
        onClearRuns={vi.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText("删除 candidate-run-001"));

    await waitFor(() => expect(onDeleteRun).toHaveBeenCalledWith("candidate-run-001"));
  });

  it("clears all records after confirmation", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const onClearRuns = vi.fn().mockResolvedValue(undefined);

    render(
      <CandidateRunsPage
        runs={[{ request_id: "candidate-run-001", current_step: "reporting" }]}
        batches={[]}
        onSelectRun={vi.fn()}
        onDeleteRun={vi.fn()}
        onClearRuns={onClearRuns}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "清空记录" }));

    await waitFor(() => expect(onClearRuns).toHaveBeenCalledTimes(1));
  });
});
