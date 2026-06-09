import { BriefcaseBusiness, Database, Layers3, ShieldCheck } from "lucide-react";
import type { BatchSummary, HealthResponse, WorkflowRun } from "../api/types";
import { MetricTile } from "../components/MetricTile";
import { StatusChip } from "../components/StatusChip";

interface DashboardPageProps {
  health: HealthResponse | null;
  runs: WorkflowRun[];
  batches: BatchSummary[];
  error: string | null;
  onSelectRun: (requestId: string) => void;
}

export function DashboardPage({ health, runs, batches, error, onSelectRun }: DashboardPageProps) {
  const pendingReviewCount = runs.filter((run) => run.human_review_status === "pending").length;
  const averageMatchScore =
    runs.length === 0
      ? "-"
      : Math.round(
          runs.reduce((total, run) => total + Number(run.match_score ?? 0), 0) / Math.max(runs.length, 1)
        );

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">招聘官工作台</p>
          <h1>招聘评估工作台</h1>
          <p className="page-subtitle">集中查看候选人批次、AI 初筛结果、风险提示和人工复核队列。</p>
        </div>
        <a className="button-primary" href="#new-batch">创建评估批次</a>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <section className="metric-grid" aria-label="Run metrics">
        <MetricTile icon={<BriefcaseBusiness size={18} />} label="候选人记录" value={runs.length} />
        <MetricTile
          icon={<ShieldCheck size={18} />}
          label="今日待复核"
          value={pendingReviewCount}
        />
        <MetricTile icon={<Layers3 size={18} />} label="候选人批次" value={batches.length} />
        <MetricTile icon={<Database size={18} />} label="平均匹配分" value={averageMatchScore} />
      </section>

      <section className="panel" id="batches">
        <div className="panel__header">
          <div>
            <h2>最近评估批次</h2>
            <p>按批次追踪岗位评估进度，快速进入 Top 候选人详情。</p>
          </div>
          <StatusChip>{health?.storage === "sqlite" ? "本地归档" : "已连接后端"}</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>批次 ID</th>
                <th>候选人数</th>
                <th>优先查看</th>
                <th>最近更新</th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={4}>暂无评估批次。创建一次批量评估后，这里会显示候选人批次。</td>
                </tr>
              ) : (
                batches.map((batch) => (
                  <tr key={batch.request_id}>
                    <td>{batch.request_id}</td>
                    <td>{batch.candidate_count}</td>
                    <td>
                      {batch.top_candidate_request_id ? (
                        <button
                          className="link-button"
                          type="button"
                          onClick={() => onSelectRun(batch.top_candidate_request_id as string)}
                        >
                          {batch.top_candidate_request_id}
                        </button>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td>{batch.updated_at ?? "-"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel" id="runs">
        <div className="panel__header">
          <div>
            <h2>候选人评估记录</h2>
            <p>查看每位候选人的匹配分、风险分和复核状态。</p>
          </div>
          <StatusChip>AI 初筛结果</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>候选人记录</th>
                <th>流程阶段</th>
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
