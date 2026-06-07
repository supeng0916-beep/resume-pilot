from __future__ import annotations

from typing import Literal

from core.state import WorkflowState


ValidationRoute = Literal["retry_resume_extractor", "continue_to_matcher", "fail_to_report"]


def route_after_validation(state: WorkflowState) -> ValidationRoute:
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 0)

    if not errors:
        return "continue_to_matcher"

    if retry_count <= max_retries:
        return "retry_resume_extractor"

    return "fail_to_report"
