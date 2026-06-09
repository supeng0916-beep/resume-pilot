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
          <h1>Evaluation cockpit</h1>
        </div>
        <a className="button-primary" href="#new-batch">New batch</a>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <section className="metric-grid" aria-label="Run metrics">
        <MetricTile icon={<Database size={18} />} label="Persisted runs" value={runs.length} />
        <MetricTile
          icon={<ShieldCheck size={18} />}
          label="Pending review"
          value={runs.filter((run) => run.human_review_status === "pending").length}
        />
        <MetricTile icon={<GitBranch size={18} />} label="Backend storage" value={health?.storage ?? "sqlite"} />
      </section>

      <section className="panel" id="runs">
        <div className="panel__header">
          <h2>Recent runs</h2>
          <StatusChip>FastAPI backed</StatusChip>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Request</th>
                <th>Step</th>
                <th>Match</th>
                <th>Risk</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={5}>No persisted runs yet. Start FastAPI and run an evaluation.</td>
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
