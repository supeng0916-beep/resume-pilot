import type { Report, TraceEvent, WorkflowRun } from "../api/types";
import { ReportPreview } from "../components/ReportPreview";
import { StatusChip } from "../components/StatusChip";
import { TraceTimeline } from "../components/TraceTimeline";

interface RunDetailPageProps {
  run: WorkflowRun;
  trace: TraceEvent[];
  report: Report | null;
}

export function RunDetailPage({ run, trace, report }: RunDetailPageProps) {
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
    </section>
  );
}
