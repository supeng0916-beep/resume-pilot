import { useEffect, useMemo, useState } from "react";
import { createApiClient } from "./api/client";
import type { HealthResponse, WorkflowRun } from "./api/types";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
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
    <AppShell health={health}>
      <DashboardPage health={health} runs={runs} error={error} />
    </AppShell>
  );
}
