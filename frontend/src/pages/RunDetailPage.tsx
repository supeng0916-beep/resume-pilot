import { Mail } from "lucide-react";
import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { AgentMetric, EmailDelivery, Report, TraceEvent, WorkflowRun } from "../api/types";
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

function formatPercent(value?: number | null) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function formatTokens(metric: AgentMetric) {
  const total = metric.token_usage?.total_tokens;
  return typeof total === "number" && total > 0 ? String(total) : "-";
}

export function RunDetailPage({ run, trace, report, onSendReportEmail }: RunDetailPageProps) {
  const payload = run.payload ?? {};
  const agentMetrics = (run.agent_metrics ?? payload.agent_metrics ?? {}) as Record<string, AgentMetric>;
  const supervisorDecisions =
    run.supervisor_decisions ?? (payload.supervisor_decisions as WorkflowRun["supervisor_decisions"]) ?? [];
  const specialistExecution =
    run.specialist_execution ?? (payload.specialist_execution as WorkflowRun["specialist_execution"]) ?? null;
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState(`Agentic HR 候选人评估报告 - ${run.request_id}`);
  const [deliveryMessage, setDeliveryMessage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const agentRows = useMemo(
    () =>
      Object.entries(agentMetrics).map(([agentName, metric]) => ({
        agentName,
        metric
      })),
    [agentMetrics]
  );

  async function submitEmail(event: FormEvent<HTMLFormElement>) {
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
    <section className="run-detail page-stack">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Run Detail</p>
          <h2>候选人评估详情</h2>
          <p>{run.request_id}</p>
        </div>
        <StatusChip>{run.human_review_status ?? "unknown"}</StatusChip>
      </div>

      <section className="panel">
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
          <div>
            <dt>Specialist 执行</dt>
            <dd>{specialistExecution?.mode ? `${specialistExecution.mode} / ${specialistExecution.duration_ms ?? 0}ms` : "-"}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Supervisor 路由决策</h2>
            <p>展示中心化 Supervisor 在不同阶段激活或跳过 Agent 的原因。</p>
          </div>
          <StatusChip>{`${supervisorDecisions.length} 次决策`}</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>阶段</th>
                <th>激活 Agent</th>
                <th>跳过原因</th>
              </tr>
            </thead>
            <tbody>
              {supervisorDecisions.length === 0 ? (
                <tr>
                  <td colSpan={3}>暂无 Supervisor 决策记录。</td>
                </tr>
              ) : (
                supervisorDecisions.map((decision, index) => (
                  <tr key={`${decision.stage ?? "decision"}-${index}`}>
                    <td>{decision.stage ?? "-"}</td>
                    <td>{(decision.active_agents ?? []).join(", ") || "-"}</td>
                    <td>
                      {Object.entries(decision.skipped_agents ?? {})
                        .map(([agent, reason]) => `${agent}: ${reason}`)
                        .join("; ") || "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Agent 执行矩阵</h2>
            <p>展示每个 Agent 的状态、置信度、模型来源和 token 使用量。</p>
          </div>
          <StatusChip>{`${agentRows.length} 个 Agent`}</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>状态</th>
                <th>置信度</th>
                <th>模型</th>
                <th>Token</th>
              </tr>
            </thead>
            <tbody>
              {agentRows.length === 0 ? (
                <tr>
                  <td colSpan={5}>暂无 Agent 执行记录。</td>
                </tr>
              ) : (
                agentRows.map(({ agentName, metric }) => (
                  <tr key={agentName}>
                    <td>{agentName}</td>
                    <td>{metric.status ?? "-"}</td>
                    <td>{formatPercent(metric.confidence)}</td>
                    <td>{metric.model_name ? `${metric.provider ?? "model"} / ${metric.model_name}` : "deterministic"}</td>
                    <td>{formatTokens(metric)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>流程追踪</h2>
            <p>展示解析、抽取、路由、评分、风险评估和报告生成的节点执行记录。</p>
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
          <StatusChip>报告投递服务</StatusChip>
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
