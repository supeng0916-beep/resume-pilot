from __future__ import annotations

from core.job_parser import parse_jd_text
from core.state import WorkflowState
from harness.trace import add_trace


def jd_extractor_node(state: WorkflowState) -> WorkflowState:
    jd_text = state.get("jd_text", "")
    job_profile = parse_jd_text(jd_text).model_dump()
    return {
        "job_profile": job_profile,
        "current_step": "jd_extractor",
        "trace": add_trace(state, "jd_extractor", "Extracted rule-based job profile."),
    }
