import { useState } from "react";
import type { WorkflowRun } from "../api/types";
import { StatusChip } from "../components/StatusChip";

interface ReviewQueuePageProps {
  runs: WorkflowRun[];
  onSubmitReview: (
    requestId: string,
    review: { decision: string; feedback: string; reviewer: string }
  ) => Promise<void>;
}

export function ReviewQueuePage({ runs, onSubmitReview }: ReviewQueuePageProps) {
  const pendingRuns = runs.filter((run) => (run.human_review_status ?? "").includes("pending"));
  const [selectedRequestId, setSelectedRequestId] = useState(pendingRuns[0]?.request_id ?? "");
  const [decision, setDecision] = useState("need_more_info");
  const [feedback, setFeedback] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function submitReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    try {
      await onSubmitReview(selectedRequestId, {
        decision,
        feedback,
        reviewer: "react-cabin"
      });
      setFeedback("");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="panel" id="reviews">
      <div className="panel__header">
        <h2>人工复核队列</h2>
        <StatusChip>{`${pendingRuns.length} 个待复核`}</StatusChip>
      </div>

      {pendingRuns.length === 0 ? (
        <p className="empty">当前没有待人工复核的运行。</p>
      ) : (
        <form className="review-form" onSubmit={submitReview}>
          <label>
            <span>运行记录</span>
            <select value={selectedRequestId} onChange={(event) => setSelectedRequestId(event.target.value)}>
              {pendingRuns.map((run) => (
                <option value={run.request_id} key={run.request_id}>
                  {run.request_id} · risk {run.risk_score ?? "-"}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>复核结论</span>
            <select aria-label="复核结论" value={decision} onChange={(event) => setDecision(event.target.value)}>
              <option value="approve">approve</option>
              <option value="reject">reject</option>
              <option value="revise">revise</option>
              <option value="need_more_info">need_more_info</option>
            </select>
          </label>
          <label className="wide">
            <span>复核反馈</span>
            <textarea
              aria-label="复核反馈"
              value={feedback}
              rows={3}
              onChange={(event) => setFeedback(event.target.value)}
            />
          </label>
          <div className="form-actions wide">
            <button className="button-primary" type="submit" disabled={isSaving || !selectedRequestId}>
              {isSaving ? "保存中..." : "保存复核"}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
