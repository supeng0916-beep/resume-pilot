import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders persisted runs from FastAPI", async () => {
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
      return Promise.resolve(new Response("{}", { status: 404 }));
    });

    render(<App />);

    await waitFor(() => expect(screen.getByText("react-run-001")).toBeInTheDocument());
    expect(screen.getByText("Evaluation cockpit")).toBeInTheDocument();
    expect(screen.getByText("Persisted runs")).toBeInTheDocument();
    expect(screen.getByText("Pending review")).toBeInTheDocument();
    expect(screen.getByText("human_review")).toBeInTheDocument();
  });
});
