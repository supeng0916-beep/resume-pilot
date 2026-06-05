from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def risk_evaluator_node(state: WorkflowState) -> WorkflowState:
    match_score = state.get("match_score") or 0
    risk_score = 0.18 if match_score >= 85 else 0.35
    risk_factors = ["期望薪资处于岗位预算上沿，需要面试确认稳定性。"]

    return {
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "current_step": "risk_evaluator",
        "trace": add_trace(
            state,
            "risk_evaluator",
            f"Estimated mock risk score: {risk_score}.",
            {"risk_factors": risk_factors},
        ),
    }
