import { Activity, BriefcaseBusiness, Database, GitBranch, ShieldCheck, Workflow } from "lucide-react";
import type { BatchSummary, HealthResponse, WorkflowRun } from "../api/types";
import type { AppView } from "../components/AppShell";
import { MetricTile } from "../components/MetricTile";
import { StatusChip } from "../components/StatusChip";

interface DashboardPageProps {
  health: HealthResponse | null;
  runs: WorkflowRun[];
  batches: BatchSummary[];
  error: string | null;
  onNavigate: (view: AppView) => void;
  onSelectRun: (requestId: string) => void;
}

function formatScore(value?: number | null) {
  return typeof value === "number" ? value : "-";
}

export function DashboardPage({ health, runs, batches, error, onNavigate, onSelectRun }: DashboardPageProps) {
  const pendingReviewRuns = runs.filter((run) => run.human_review_status === "pending");
  const averageMatchScore =
    runs.length === 0
      ? "-"
      : Math.round(runs.reduce((total, run) => total + Number(run.match_score ?? 0), 0) / Math.max(runs.length, 1));
  const recentRuns = runs.slice(0, 5);
  const readinessTone = health?.status === "ok" ? "success" : "warning";

  return (
    <section className="page-stack">
      <div className="hero-panel hero-panel--app">
        <div>
          <p className="eyebrow">Operations Overview</p>
          <h2>招聘评估运营总览</h2>
          <p className="page-subtitle">
            这里聚合 Supervisor 路由、批量评估、候选人风险和人工复核压力。左侧功能栏负责进入具体工作区，首页只保留当前运营态势。
          </p>
        </div>
        <div className="hero-status">
          <StatusChip tone={readinessTone}>{health?.status === "ok" ? "服务就绪" : "服务连接中"}</StatusChip>
          <span>数据层已接入</span>
          <span>任务调度可用</span>
        </div>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <section className="metric-grid" aria-label="招聘评估指标">
        <MetricTile icon={<BriefcaseBusiness size={18} />} label="候选人记录" hint="已归档运行" value={runs.length} />
        <MetricTile icon={<ShieldCheck size={18} />} label="待复核" hint="需要人工确认" value={pendingReviewRuns.length} />
        <MetricTile icon={<GitBranch size={18} />} label="运行批次" hint="批量评估任务" value={batches.length} />
        <MetricTile icon={<Database size={18} />} label="平均匹配分" hint="已评估候选人均值" value={averageMatchScore} />
      </section>

      <section className="ops-grid">
        <div className="panel panel--table">
          <div className="panel__header">
            <div>
              <h2>最近运行</h2>
              <p>优先检查最新候选人的流程阶段、匹配分和风险分。</p>
            </div>
            <button className="button-secondary" type="button" onClick={() => onNavigate("candidates")}>
              查看全部
            </button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>记录</th>
                  <th>阶段</th>
                  <th>匹配</th>
                  <th>风险</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.length === 0 ? (
                  <tr>
                    <td colSpan={4}>暂无运行记录。请在评估任务工作区创建一次批量评估。</td>
                  </tr>
                ) : (
                  recentRuns.map((run) => (
                    <tr key={run.request_id}>
                      <td>
                        <button className="link-button" type="button" onClick={() => onSelectRun(run.request_id)}>
                          {run.request_id}
                        </button>
                      </td>
                      <td>{run.current_step ?? "-"}</td>
                      <td>{formatScore(run.match_score)}</td>
                      <td>{formatScore(run.risk_score)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="side-stack">
          <div className="panel">
            <div className="panel__header">
              <div>
                <h2>复核压力</h2>
                <p>高风险、低置信或证据不足的候选人会进入人工复核。</p>
              </div>
              <StatusChip tone={pendingReviewRuns.length > 0 ? "warning" : "success"}>
                {pendingReviewRuns.length > 0 ? "需要处理" : "队列清空"}
              </StatusChip>
            </div>
            <div className="review-summary">
              <strong>{pendingReviewRuns.length}</strong>
              <span>个待复核候选人</span>
              <button className="button-primary" type="button" onClick={() => onNavigate("reviews")}>
                处理复核队列
              </button>
            </div>
          </div>

          <div className="panel flow-panel">
            <div className="panel__header">
              <div>
                <h2>Agent 流程态势</h2>
                <p>Supervisor 统一调度专家节点，输出可追踪证据链。</p>
              </div>
              <Workflow size={20} />
            </div>
            <div className="flow-steps" aria-label="Agent 流程概览">
              <span>
                <Activity size={14} />
                Supervisor 路由
              </span>
              <span>Candidate Analyst</span>
              <span>Job Analyst</span>
              <span>Evidence / Critic</span>
              <span>Report / Review</span>
            </div>
          </div>
        </aside>
      </section>
    </section>
  );
}
