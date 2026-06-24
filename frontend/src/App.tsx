import { useEffect, useMemo, useState } from "react";
import { createApiClient } from "./api/client";
import type {
  BatchEvaluationRequest,
  BatchSummary,
  HealthResponse,
  Report,
  TraceEvent,
  UploadBatchEvaluationRequest,
  WorkflowRun
} from "./api/types";
import { AppShell } from "./components/AppShell";
import type { AppView } from "./components/AppShell";
import { BatchEvaluationPage } from "./pages/BatchEvaluationPage";
import { CandidateRunsPage } from "./pages/CandidateRunsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { RunDetailPage } from "./pages/RunDetailPage";
import "./styles/tokens.css";
import "./styles/app.css";

export default function App() {
  const api = useMemo(() => createApiClient(), []);
  const [activeView, setActiveView] = useState<AppView>("overview");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<TraceEvent[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refreshRuns() {
    return Promise.all([api.getHealth(), api.listRuns(), api.listBatches()])
      .then(([healthResponse, runList, batchList]) => {
        setHealth(healthResponse);
        setRuns(runList);
        setBatches(batchList);
        return runList;
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Unable to reach Agentic HR API");
        return [];
      });
  }

  useEffect(() => {
    refreshRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api]);

  async function runBatch(request: BatchEvaluationRequest) {
    setIsRunning(true);
    setError(null);
    try {
      await api.createBatchEvaluation(request);
      const latestRuns = await refreshRuns();
      const firstRun = latestRuns.find((run) => run.request_id.startsWith(`${request.request_id}-`));
      if (firstRun) {
        await selectRun(firstRun.request_id);
      } else {
        setActiveView("candidates");
      }
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Batch evaluation failed");
    } finally {
      setIsRunning(false);
    }
  }

  async function uploadBatch(request: UploadBatchEvaluationRequest) {
    setIsRunning(true);
    setError(null);
    try {
      await api.uploadBatchEvaluation(request);
      const latestRuns = await refreshRuns();
      const firstRun = latestRuns.find((run) => run.request_id.startsWith(`${request.request_id}-`));
      if (firstRun) {
        await selectRun(firstRun.request_id);
      } else {
        setActiveView("candidates");
      }
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Upload batch evaluation failed");
    } finally {
      setIsRunning(false);
    }
  }

  async function selectRun(requestId: string) {
    setError(null);
    try {
      const [run, trace, report] = await Promise.all([
        api.getRun(requestId),
        api.getTrace(requestId),
        api.getReport(requestId)
      ]);
      setSelectedRun(run);
      setSelectedTrace(trace);
      setSelectedReport(report);
      setActiveView("detail");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Unable to load run detail");
    }
  }

  async function submitReview(
    requestId: string,
    review: { decision: string; feedback: string; reviewer: string }
  ) {
    setError(null);
    try {
      await api.saveReview(requestId, review);
      await refreshRuns();
      if (selectedRun?.request_id === requestId) {
        await selectRun(requestId);
      }
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Unable to save review");
    }
  }

  async function sendReportEmail(request: { request_id: string; recipient: string; subject: string }) {
    return api.sendReportEmail(request);
  }

  async function deleteRun(requestId: string) {
    setError(null);
    try {
      await api.deleteRun(requestId);
      if (selectedRun?.request_id === requestId) {
        setSelectedRun(null);
        setSelectedTrace([]);
        setSelectedReport(null);
        setActiveView("candidates");
      }
      await refreshRuns();
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Unable to delete run");
    }
  }

  async function clearRuns() {
    setError(null);
    try {
      await api.clearRuns();
      setSelectedRun(null);
      setSelectedTrace([]);
      setSelectedReport(null);
      await refreshRuns();
      setActiveView("candidates");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Unable to clear records");
    }
  }

  function renderActiveView() {
    if (activeView === "evaluations") {
      return <BatchEvaluationPage isRunning={isRunning} onSubmit={runBatch} onUploadSubmit={uploadBatch} />;
    }
    if (activeView === "candidates") {
      return (
        <CandidateRunsPage
          runs={runs}
          batches={batches}
          onSelectRun={selectRun}
          onDeleteRun={deleteRun}
          onClearRuns={clearRuns}
        />
      );
    }
    if (activeView === "reviews") {
      return <ReviewQueuePage runs={runs} onSubmitReview={submitReview} />;
    }
    if (activeView === "detail") {
      return selectedRun ? (
        <RunDetailPage
          run={selectedRun}
          trace={selectedTrace}
          report={selectedReport}
          onSendReportEmail={sendReportEmail}
        />
      ) : (
        <CandidateRunsPage
          runs={runs}
          batches={batches}
          onSelectRun={selectRun}
          onDeleteRun={deleteRun}
          onClearRuns={clearRuns}
        />
      );
    }
    return (
      <DashboardPage
        health={health}
        runs={runs}
        batches={batches}
        error={error}
        onNavigate={setActiveView}
        onSelectRun={selectRun}
      />
    );
  }

  return (
    <AppShell
      activeView={activeView}
      health={health}
      queueLabel={health?.queue_backend ?? "queue"}
      selectedRunId={selectedRun?.request_id}
      onNavigate={setActiveView}
    >
      {error && activeView !== "overview" ? <div className="alert">{error}</div> : null}
      {renderActiveView()}
    </AppShell>
  );
}
