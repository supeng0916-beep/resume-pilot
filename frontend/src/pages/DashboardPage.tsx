import { Database, GitBranch, ShieldCheck } from "lucide-react";
import type { HealthResponse, WorkflowRun } from "../api/types";
import { MetricTile } from "../components/MetricTile";
import { StatusChip } from "../components/StatusChip";

interface DashboardPageProps {
  health: HealthResponse | null;
  runs: WorkflowRun[];
  error: string | null;
  onSelectRun: (requestId: string) => void;
}

export function DashboardPage({ health, runs, error, onSelectRun }: DashboardPageProps) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Primary frontend</p>
          <h1>招聘评估控制舱</h1>
        </div>
        <a className="button-primary" href="#new-batch">新建批量评估</a>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <section className="metric-grid" aria-label="Run metrics">
        <MetricTile icon={<Database size={18} />} label="已持久化运行" value={runs.length} />
        <MetricTile
          icon={<ShieldCheck size={18} />}
          label="待人工复核"
          value={runs.filter((run) => run.human_review_status === "pending").length}
        />
        <MetricTile icon={<GitBranch size={18} />} label="后端存储" value={health?.storage ?? "sqlite"} />
      </section>

      <section className="panel" id="runs">
        <div className="panel__header">
          <h2>最近运行</h2>
          <StatusChip>FastAPI 驱动</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>请求 ID</th>
                <th>当前步骤</th>
                <th>匹配分</th>
                <th>风险分</th>
                <th>复核状态</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={5}>暂无持久化运行记录。请先启动 FastAPI 并运行一次评估。</td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.request_id}>
                    <td>
                      <button className="link-button" type="button" onClick={() => onSelectRun(run.request_id)}>
                        {run.request_id}
                      </button>
                    </td>
                    <td>{run.current_step ?? "-"}</td>
                    <td>{run.match_score ?? "-"}</td>
                    <td>{run.risk_score ?? "-"}</td>
                    <td>{run.human_review_status ?? "-"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
