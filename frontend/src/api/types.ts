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

export interface BatchResumeRequest {
  candidate_id: string;
  resume_text?: string;
  resume_file_path?: string;
}

export interface BatchEvaluationRequest {
  request_id: string;
  resumes: BatchResumeRequest[];
  jd_text?: string;
  risk_model_path?: string;
  enable_llm_structured_extraction?: boolean;
  enable_llm_report_enhancement?: boolean;
}

export interface UploadBatchEvaluationRequest {
  request_id: string;
  files: File[];
  jd_text?: string;
  risk_model_path?: string;
  enable_llm_structured_extraction?: boolean;
  enable_llm_report_enhancement?: boolean;
}

export interface RankedCandidate {
  candidate_id: string;
  request_id: string;
  name?: string;
  track?: string;
  match_score?: number | null;
  risk_score?: number | null;
  rank_score?: number | null;
  evidence_confidence?: number | null;
  review_reasons?: string[];
}

export interface BatchEvaluationResult {
  request_id: string;
  candidate_count: number;
  ranked_candidates: RankedCandidate[];
  batch_report: string;
}

export interface HealthResponse {
  status: string;
  storage: string;
}
