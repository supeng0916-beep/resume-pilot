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
          <h2>{run.request_id}</h2>
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
          <h2>Trace 时间线</h2>
        </div>
        <TraceTimeline trace={trace} />
      </section>

      <section className="panel">
        <div className="panel__header">
          <h2>评估报告</h2>
        </div>
        <ReportPreview report={report} />
      </section>
    </section>
  );
}
