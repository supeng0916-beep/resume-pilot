import { Mail } from "lucide-react";
import { useState } from "react";
import type { EmailDelivery, Report, TraceEvent, WorkflowRun } from "../api/types";
import { ReportPreview } from "../components/ReportPreview";
import { StatusChip } from "../components/StatusChip";
import { TraceTimeline } from "../components/TraceTimeline";

interface RunDetailPageProps {
  run: WorkflowRun;
  trace: TraceEvent[];
  report: Report | null;
  onSendReportEmail: (request: {
    request_id: string;
    recipient: string;
    subject: string;
  }) => Promise<EmailDelivery>;
}

export function RunDetailPage({ run, trace, report, onSendReportEmail }: RunDetailPageProps) {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState(`Agentic HR 候选人评估报告 - ${run.request_id}`);
  const [deliveryMessage, setDeliveryMessage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  async function submitEmail(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSending(true);
    setDeliveryMessage(null);
    try {
      const delivery = await onSendReportEmail({
        request_id: run.request_id,
        recipient: recipient.trim(),
        subject: subject.trim()
      });
      setDeliveryMessage(delivery.message);
    } catch (caught: unknown) {
      setDeliveryMessage(caught instanceof Error ? caught.message : "邮件发送失败");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <section className="run-detail">
      <div className="panel">
        <div className="panel__header">
          <div>
            <h2>候选人评估详情</h2>
            <p>{run.request_id}</p>
          </div>
          <StatusChip>{run.human_review_status ?? "unknown"}</StatusChip>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>当前步骤</dt>
            <dd>{run.current_step ?? "-"}</dd>
          </div>
          <div>
            <dt>匹配分</dt>
            <dd>{run.match_score ?? "-"}</dd>
          </div>
          <div>
            <dt>风险分</dt>
            <dd>{run.risk_score ?? "-"}</dd>
          </div>
        </dl>
      </div>

      <section className="panel" id="trace">
        <div className="panel__header">
          <div>
            <h2>流程追踪</h2>
            <p>展示解析、抽取、评分、风险评估和报告生成的节点执行记录。</p>
          </div>
        </div>
        <TraceTimeline trace={trace} />
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>候选人评估报告</h2>
            <p>供招聘官复核的匹配依据、风险提示和面试建议。</p>
          </div>
        </div>
        <ReportPreview report={report} />
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>发送评估报告</h2>
            <p>通过后端 SMTP 配置发送当前候选人的 Markdown 报告，并记录投递结果。</p>
          </div>
          <StatusChip>FastAPI 邮件服务</StatusChip>
        </div>
        <form className="email-form" onSubmit={submitEmail}>
          <label>
            <span>收件人邮箱</span>
            <input
              type="email"
              value={recipient}
              onChange={(event) => setRecipient(event.target.value)}
              placeholder="hr-lead@example.com"
              required
            />
          </label>
          <label>
            <span>邮件主题</span>
            <input value={subject} onChange={(event) => setSubject(event.target.value)} />
          </label>
          <button className="button-primary" type="submit" disabled={isSending || !report?.markdown}>
            <Mail size={16} />
            {isSending ? "发送中..." : "发送报告"}
          </button>
        </form>
        {deliveryMessage ? <p className="email-status">{deliveryMessage}</p> : null}
      </section>
    </section>
  );
}
