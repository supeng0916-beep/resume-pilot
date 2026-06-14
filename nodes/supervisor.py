from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


DEFAULT_ACTIVE_AGENTS = [
    "candidate_analyst",
    "job_analyst",
    "memory_agent",
    "reporting_agent",
]


def supervisor_node(state: WorkflowState) -> WorkflowState:
    request_type = state.get("request_type") or "candidate_evaluation"
    plan = {
        "request_type": request_type,
        "objective": "Produce an explainable candidate evaluation with human-review checkpoints.",
        "ordered_agents": list(DEFAULT_ACTIVE_AGENTS),
        "handoff_rules": {
            "validation_failure": "retry_resume_extractor_or_fail_report",
            "high_risk_or_missing_context": "human_review",
        },
    }
    return {
        "request_type": request_type,
        "active_agents": list(DEFAULT_ACTIVE_AGENTS),
        "supervisor_plan": plan,
        "current_step": "supervisor",
        "trace": add_trace(
            state,
            "supervisor",
            "Supervisor agent planned the evaluation and activated specialist agents.",
            plan,
        ),
    }
