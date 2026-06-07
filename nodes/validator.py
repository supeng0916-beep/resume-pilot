from __future__ import annotations

from pydantic import ValidationError

from core.schemas import CandidateProfile, DocumentMeta, JobProfile, ScoringRubric
from core.state import WorkflowState
from harness.trace import add_trace


def _format_validation_error(prefix: str, error: ValidationError) -> list[str]:
    messages: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        messages.append(f"{prefix}.{location}: {item['msg']}")
    return messages


def validator_node(state: WorkflowState) -> WorkflowState:
    errors: list[str] = []
    updates: WorkflowState = {}

    try:
        updates["candidate_profile"] = CandidateProfile.model_validate(
            state.get("candidate_profile")
        ).model_dump()
    except ValidationError as error:
        errors.extend(_format_validation_error("candidate_profile", error))

    try:
        updates["job_profile"] = JobProfile.model_validate(state.get("job_profile")).model_dump()
    except ValidationError as error:
        errors.extend(_format_validation_error("job_profile", error))

    document_meta = state.get("document_meta")
    if document_meta is not None:
        try:
            updates["document_meta"] = DocumentMeta.model_validate(document_meta).model_dump()
        except ValidationError as error:
            errors.extend(_format_validation_error("document_meta", error))

    scoring_rubric = state.get("scoring_rubric")
    if scoring_rubric is not None:
        try:
            updates["scoring_rubric"] = ScoringRubric.model_validate(scoring_rubric).model_dump()
        except ValidationError as error:
            errors.extend(_format_validation_error("scoring_rubric", error))

    retry_count = state.get("retry_count", 0)
    if errors:
        retry_count += 1

    updates.update({
        "validation_errors": errors,
        "retry_count": retry_count,
        "current_step": "validator",
        "trace": add_trace(
            state,
            "validator",
            "Validation passed."
            if not errors
            else f"Validation failed: {len(errors)} errors. Retry count is {retry_count}.",
            {"errors": errors, "retry_count": retry_count},
        ),
    })
    return updates
