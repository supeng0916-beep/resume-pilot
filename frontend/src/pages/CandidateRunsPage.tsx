import { Search, Trash2, UsersRound } from "lucide-react";
import { useMemo, useState } from "react";
import type { BatchSummary, WorkflowRun } from "../api/types";
import { StatusChip } from "../components/StatusChip";

interface CandidateRunsPageProps {
  runs: WorkflowRun[];
  batches: BatchSummary[];
  onSelectRun: (requestId: string) => void;
  onDeleteRun: (requestId: string) => Promise<void>;
  onClearRuns: () => Promise<void>;
}

function formatScore(value?: number | null) {
  return typeof value === "number" ? value : "-";
}

function reviewTone(status?: string | null) {
  if (!status) {
    return "neutral";
  }
  if (status.includes("pending")) {
    return "warning";
  }
  if (status.includes("approved") || status.includes("complete")) {
    return "success";
  }
  return "neutral";
}

export function CandidateRunsPage({
  runs,
  batches,
  onSelectRun,
  onDeleteRun,
  onClearRuns
}: CandidateRunsPageProps) {
  const [query, setQuery] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const filteredRuns = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) {
      return runs;
    }
    return runs.filter((run) =>
      [run.request_id, run.current_step, run.human_review_status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(keyword))
    );
  }, [query, runs]);

  async function deleteRun(requestId: string) {
    if (!window.confirm(`确认删除记录 ${requestId}？相关 trace、报告、复核和批次关联也会一起删除。`)) {
      return;
    }
    setDeletingId(requestId);
    try {
      await onDeleteRun(requestId);
    } finally {
      setDeletingId(null);
    }
  }

  async function clearRuns() {
    if (!window.confirm("确认清空所有评估记录？该操作会删除候选人运行、批次、报告、trace 和复核记录。")) {
      return;
    }
    setIsClearing(true);
    try {
      await onClearRuns();
    } finally {
      setIsClearing(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Candidate Workspace</p>
          <h2>候选人库</h2>
          <p>按批次、评分、风险和复核状态查看每一次候选人评估，进入详情后可以审计 Supervisor 路由和 Agent 输出。</p>
        </div>
        <div className="toolbar-row">
          <div className="search-box">
            <Search size={16} />
            <input
              aria-label="搜索候选人运行记录"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="搜索 request id / 阶段 / 状态"
            />
          </div>
          <button className="button-danger" type="button" onClick={clearRuns} disabled={isClearing || runs.length === 0}>
            <Trash2 size={16} />
            {isClearing ? "清空中..." : "清空记录"}
          </button>
        </div>
      </div>

      <section className="panel panel--table">
        <div className="panel__header">
          <div>
            <h2>候选人评估记录</h2>
            <p>每条记录都是一次完整的 LangGraph 执行，包含状态、评分、报告和 trace。</p>
          </div>
          <StatusChip>{`${filteredRuns.length} 条记录`}</StatusChip>
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
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <span className="empty-inline">
                      <UsersRound size={16} />
                      暂无匹配的候选人记录。
                    </span>
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run) => (
                  <tr key={run.request_id}>
                    <td>
                      <button className="link-button" type="button" onClick={() => onSelectRun(run.request_id)}>
                        {run.request_id}
                      </button>
                    </td>
                    <td>{run.current_step ?? "-"}</td>
                    <td>{formatScore(run.match_score)}</td>
                    <td>{formatScore(run.risk_score)}</td>
                    <td>
                      <StatusChip tone={reviewTone(run.human_review_status)}>{run.human_review_status ?? "unknown"}</StatusChip>
                    </td>
                    <td>
                      <button
                        className="icon-danger-button"
                        type="button"
                        aria-label={`删除 ${run.request_id}`}
                        onClick={() => deleteRun(run.request_id)}
                        disabled={deletingId === run.request_id}
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel panel--table">
        <div className="panel__header">
          <div>
            <h2>批次记录</h2>
            <p>从批量任务角度查看候选人数量、最高优先级记录和最近更新时间。</p>
          </div>
          <StatusChip>{`${batches.length} 个批次`}</StatusChip>
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
                  <td colSpan={4}>暂无评估批次。创建任务后，这里会显示批量评估进展。</td>
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
    </section>
  );
}
