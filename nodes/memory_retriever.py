from __future__ import annotations

from core.agent_contracts import AgentResult, record_agent_result
from core.feedback_memory import (
    DEFAULT_FEEDBACK_MEMORY_PATH,
    retrieve_feedback_records,
    summarize_feedback_records,
)
from core.state import WorkflowState
from harness.trace import add_trace


def memory_retriever_node(state: WorkflowState) -> WorkflowState:
    memory_path = state.get("feedback_memory_path") or DEFAULT_FEEDBACK_MEMORY_PATH
    records = retrieve_feedback_records(state, path=memory_path)
    summaries = summarize_feedback_records(records)
    findings = {
        "memory_path": memory_path,
        "memory_count": len(records),
        "used_feedback_memory": bool(summaries),
    }
    agent_result = AgentResult(
        agent_name="memory_agent",
        role="historical_feedback_retrieval",
        status="success",
        findings=findings,
        evidence_refs=[],
        confidence=0.75 if summaries else 0.35,
        concerns=[] if summaries else ["No historical feedback memory found for this job context."],
    )
    agent_updates = record_agent_result(state, agent_result)

    if summaries:
        output_summary = f"Retrieved {len(summaries)} job-specific human feedback memories."
    else:
        output_summary = "No job-specific human feedback memory found."

    return {
        "feedback_memory_records": records,
        "feedback_memory_summaries": summaries,
        **agent_updates,
        "current_step": "memory_retriever",
        "trace": add_trace(
            state,
            "memory_retriever",
            output_summary,
            {
                "memory_path": memory_path,
                "record_count": len(records),
            },
        ),
    }
