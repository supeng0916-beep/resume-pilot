import type {
  BatchEvaluationRequest,
  BatchEvaluationResult,
  HealthResponse,
  Report,
  Review,
  TraceEvent,
  WorkflowRun
} from "./types";

export interface ApiClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
}

export interface ApiClient {
  getHealth(): Promise<HealthResponse>;
  listRuns(): Promise<WorkflowRun[]>;
  getRun(requestId: string): Promise<WorkflowRun>;
  getTrace(requestId: string): Promise<TraceEvent[]>;
  getReport(requestId: string): Promise<Report>;
  listReviews(): Promise<Review[]>;
  createBatchEvaluation(request: BatchEvaluationRequest): Promise<BatchEvaluationResult>;
  saveReview(
    requestId: string,
    review: { decision: string; feedback?: string; reviewer?: string }
  ): Promise<Review>;
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

function endpoint(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

export function createApiClient(options: ApiClientOptions = {}): ApiClient {
  const baseUrl = options.baseUrl ?? "/api";
  const fetchImpl = options.fetchImpl ?? fetch;

  return {
    async getHealth() {
      return readJson<HealthResponse>(await fetchImpl(endpoint(baseUrl, "/health")));
    },
    async listRuns() {
      const payload = await readJson<{ runs: WorkflowRun[] }>(await fetchImpl(endpoint(baseUrl, "/runs")));
      return payload.runs;
    },
    async getRun(requestId: string) {
      return readJson<WorkflowRun>(await fetchImpl(endpoint(baseUrl, `/runs/${encodeURIComponent(requestId)}`)));
    },
    async getTrace(requestId: string) {
      const payload = await readJson<{ trace: TraceEvent[] }>(
        await fetchImpl(endpoint(baseUrl, `/traces/${encodeURIComponent(requestId)}`))
      );
      return payload.trace;
    },
    async getReport(requestId: string) {
      return readJson<Report>(await fetchImpl(endpoint(baseUrl, `/reports/${encodeURIComponent(requestId)}`)));
    },
    async listReviews() {
      const payload = await readJson<{ reviews: Review[] }>(await fetchImpl(endpoint(baseUrl, "/reviews")));
      return payload.reviews;
    },
    async createBatchEvaluation(request) {
      return readJson<BatchEvaluationResult>(
        await fetchImpl(endpoint(baseUrl, "/batch-evaluations"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request)
        })
      );
    },
    async saveReview(requestId, review) {
      return readJson<Review>(
        await fetchImpl(endpoint(baseUrl, `/reviews/${encodeURIComponent(requestId)}`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(review)
        })
      );
    }
  };
}
