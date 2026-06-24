import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
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

  useEffect(() => {
    if (!selectedRequestId && pendingRuns[0]?.request_id) {
      setSelectedRequestId(pendingRuns[0].request_id);
    }
  }, [pendingRuns, selectedRequestId]);

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
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Human Review</p>
          <h2>人工复核工作台</h2>
          <p>集中处理高风险、证据不足或需要人工判断的候选人，把复核结论写回系统记忆和运行记录。</p>
        </div>
        <StatusChip tone={pendingRuns.length > 0 ? "warning" : "success"}>{`${pendingRuns.length} 个待复核`}</StatusChip>
      </div>

      <section className="panel review-panel">
        {pendingRuns.length === 0 ? (
          <div className="empty-state empty-state--large">
            <ShieldCheck size={28} />
            <div>
              <strong>当前没有待人工复核的运行</strong>
              <p>当 Supervisor 标记高风险或低置信候选人时，这里会出现可处理任务。</p>
            </div>
          </div>
        ) : (
          <form className="review-form" onSubmit={submitReview}>
            <label>
              <span>候选人记录</span>
              <select value={selectedRequestId} onChange={(event) => setSelectedRequestId(event.target.value)}>
                {pendingRuns.map((run) => (
                  <option value={run.request_id} key={run.request_id}>
                    {run.request_id} · 风险分 {run.risk_score ?? "-"}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>复核结论</span>
              <select aria-label="复核结论" value={decision} onChange={(event) => setDecision(event.target.value)}>
                <option value="approve">通过，进入下一轮</option>
                <option value="reject">暂不推进</option>
                <option value="revise">要求调整报告</option>
                <option value="need_more_info">补充候选人信息</option>
              </select>
            </label>
            <label className="wide">
              <span>复核反馈</span>
              <textarea
                aria-label="复核反馈"
                value={feedback}
                rows={5}
                onChange={(event) => setFeedback(event.target.value)}
                placeholder="记录证据核验、面试追问、薪资或稳定性判断。"
              />
            </label>
            <div className="form-actions wide">
              <button className="button-primary" type="submit" disabled={isSaving || !selectedRequestId}>
                <ShieldCheck size={16} />
                {isSaving ? "保存中..." : "提交复核"}
              </button>
            </div>
          </form>
        )}
      </section>
    </section>
  );
}
