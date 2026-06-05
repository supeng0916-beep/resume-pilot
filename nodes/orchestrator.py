from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def orchestrator_node(state: WorkflowState) -> WorkflowState:
    return {
        "current_step": "orchestrator",
        "trace": add_trace(state, "orchestrator", "Routed demo request into document parsing."),
    }
