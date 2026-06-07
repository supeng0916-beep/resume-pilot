from __future__ import annotations

from typing import Any, TypedDict


class WorkflowState(TypedDict, total=False):
    request_id: str
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

    report: str | None
    human_decision: str | None
    human_feedback: str | None
    human_review_required: bool
    human_review_status: str | None

    current_step: str
    errors: list[str]
    trace: list[dict[str, Any]]

    force_invalid_candidate_once: bool
    force_invalid_candidate_always: bool
