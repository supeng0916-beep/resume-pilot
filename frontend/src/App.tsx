import { Activity, Database, GitBranch, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { createApiClient } from "./api/client";
import type { HealthResponse, WorkflowRun } from "./api/types";
import "./styles/tokens.css";
import "./styles/app.css";

export default function App() {
  const api = useMemo(() => createApiClient(), []);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getHealth(), api.listRuns()])
      .then(([healthResponse, runList]) => {
        setHealth(healthResponse);
        setRuns(runList);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Unable to reach Agentic HR API");
      });
  }, [api]);

  return (
    <main className="app-shell">
      <header className="top-bar">
        <div className="top-bar__inner">
          <span className="brand">Agentic HR</span>
          <span className={health?.status === "ok" ? "health health--ok" : "health"}>
            <Activity size={14} />
            {health?.status ?? "checking"}
          </span>
        </div>
      </header>
      <nav className="sub-nav">
        <div className="sub-nav__inner">
          <strong>React Control Cabin</strong>
          <div className="sub-nav__links">
            <a href="#runs">Runs</a>
            <a href="#reviews">Reviews</a>
            <a href="#trace">Trace</a>
          </div>
        </div>
      </nav>
      <section className="workspace">
        <div className="page-heading">
          <div>
            <p className="eyebrow">Primary frontend</p>
            <h1>Evaluation cockpit</h1>
          </div>
          <button className="button-primary" type="button">New batch</button>
        </div>

        {error ? <div className="alert">{error}</div> : null}

        <section className="metric-grid" aria-label="Run metrics">
          <article className="metric-tile">
            <Database size={18} />
            <span>Persisted runs</span>
            <strong>{runs.length}</strong>
          </article>
          <article className="metric-tile">
            <ShieldCheck size={18} />
            <span>Pending review</span>
            <strong>{runs.filter((run) => run.human_review_status === "pending").length}</strong>
          </article>
          <article className="metric-tile">
            <GitBranch size={18} />
            <span>Backend storage</span>
            <strong>{health?.storage ?? "sqlite"}</strong>
          </article>
        </section>

        <section className="panel" id="runs">
          <div className="panel__header">
            <h2>Recent runs</h2>
            <span className="status-chip">FastAPI backed</span>
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
                      <td>{run.request_id}</td>
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
      </section>
    </main>
  );
}
