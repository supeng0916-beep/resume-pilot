from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def validator_node(state: WorkflowState) -> WorkflowState:
    errors: list[str] = []
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}

    if not candidate.get("skills"):
        errors.append("candidate_profile.skills is required")
    if not isinstance(candidate.get("years_experience"), int):
        errors.append("candidate_profile.years_experience must be int")
    if not job.get("required_skills"):
        errors.append("job_profile.required_skills is required")

    return {
        "validation_errors": errors,
        "current_step": "validator",
        "trace": add_trace(
            state,
            "validator",
            "Validation passed." if not errors else f"Validation failed: {len(errors)} errors.",
            {"errors": errors},
        ),
    }
