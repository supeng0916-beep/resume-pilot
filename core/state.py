from __future__ import annotations

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    request_id: str
    request_type: str | None
    resume_file_path: str | None
    resume_text: str
    jd_text: str
    document_meta: dict[str, Any] | None

    candidate_profile: dict[str, Any] | None
    job_profile: dict[str, Any] | None
    scoring_rubric: dict[str, Any] | None

    validation_errors: list[str]
    retry_count: int
    max_retries: int

    match_score: float | None
    match_breakdown: dict[str, Any] | None

    risk_score: float | None
    risk_factors: list[str]
    risk_features: dict[str, Any] | None
    risk_model_path: str | None
    risk_model_used: str | None

    report: str | None
    llm_enhancement_status: str | None
    enable_llm_report_enhancement: bool | None
    enable_llm_structured_extraction: bool | None
    llm_extraction_status: list[str]
    human_decision: str | None
    human_feedback: str | None
    human_review_required: bool
    human_review_status: str | None
    persist_human_feedback: bool
    feedback_memory_path: str | None
    use_feedback_memory: bool
    feedback_memory_record: dict[str, Any] | None
    feedback_memory_records: list[dict[str, Any]]
    feedback_memory_summaries: list[str]
    active_agents: list[str]
    supervisor_plan: dict[str, Any] | None
    supervisor_decisions: list[dict[str, Any]]
    agent_outputs: dict[str, Any]
    agent_metrics: dict[str, Any]
    specialist_execution: dict[str, Any] | None
    candidate_insights: dict[str, Any] | None
    job_insights: dict[str, Any] | None
    final_recommendation: dict[str, Any] | None

    current_step: str
    errors: list[str]
    trace: list[dict[str, Any]]

    force_invalid_candidate_once: bool
    force_invalid_candidate_always: bool
