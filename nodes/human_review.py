from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


ALLOWED_HUMAN_DECISIONS = {"approve", "reject", "revise", "need_more_info"}


def human_review_node(state: WorkflowState) -> WorkflowState:
    decision = state.get("human_decision")
    feedback = state.get("human_feedback")

    if decision is None:
        status = "pending_review"
        output_summary = "Waiting for human review before final decision."
        errors = list(state.get("errors", []))
    elif decision not in ALLOWED_HUMAN_DECISIONS:
        status = "invalid_review_decision"
        output_summary = f"Rejected invalid human review decision: {decision}."
        errors = list(state.get("errors", []))
        errors.append(f"Invalid human_decision: {decision}")
    else:
        status = f"reviewed_{decision}"
        output_summary = f"Recorded human review decision: {decision}."
        errors = list(state.get("errors", []))

    return {
        "human_review_required": decision is None or status == "invalid_review_decision",
        "human_review_status": status,
        "errors": errors,
        "current_step": "human_review",
        "trace": add_trace(
            state,
            "human_review",
            output_summary,
            {
                "decision": decision,
                "status": status,
                "has_feedback": bool(feedback),
            },
        ),
    }
