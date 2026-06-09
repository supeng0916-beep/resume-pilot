export interface WorkflowRun {
  request_id: string;
  current_step?: string | null;
  match_score?: number | null;
  risk_score?: number | null;
  human_review_status?: string | null;
  report?: string | null;
  created_at?: string;
  updated_at?: string;
  payload?: Record<string, unknown>;
  trace?: TraceEvent[];
}

export interface TraceEvent {
  id?: number;
  request_id?: string;
  node?: string | null;
  timestamp?: string | null;
  output_summary?: string | null;
  extra?: Record<string, unknown>;
}

export interface Report {
  request_id: string;
  markdown?: string | null;
  quality?: Record<string, unknown>;
  created_at?: string;
}

export interface Review {
  id: number;
  request_id: string;
  decision: string;
  feedback?: string | null;
  reviewer?: string | null;
  created_at?: string;
}

export interface HealthResponse {
  status: string;
  storage: string;
}
