from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def job_analyst_node(state: WorkflowState) -> WorkflowState:
    job = state.get("job_profile") or {}
    required_skills = list(job.get("required_skills", []))
    preferred_skills = list(job.get("preferred_skills", []))
    title = job.get("title") or "unknown"

    priorities: list[str] = []
    if required_skills:
        priorities.append(f"Required skill focus: {', '.join(required_skills[:4])}.")
    if preferred_skills:
        priorities.append(f"Preferred differentiators: {', '.join(preferred_skills[:3])}.")

    insight = {
        "job_title": title,
        "priorities": priorities or ["Clarify hiring manager priorities before final decision."],
        "recruitment_track": job.get("recruitment_track", "unknown"),
    }
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_outputs["job_analyst"] = insight

    return {
        "job_insights": insight,
        "agent_outputs": agent_outputs,
        "current_step": "job_analyst",
        "trace": add_trace(
            state,
            "job_analyst",
            "Job analyst agent converted the JD into evaluation priorities.",
            insight,
        ),
    }
