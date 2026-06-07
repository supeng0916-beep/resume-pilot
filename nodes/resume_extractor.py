from __future__ import annotations

from core.schemas import CandidateProfile
from core.state import WorkflowState
from harness.trace import add_trace


def resume_extractor_node(state: WorkflowState) -> WorkflowState:
    candidate_profile = CandidateProfile(
        name="张三",
        education="本科",
        years_experience=5,
        skills=["Python", "FastAPI", "PostgreSQL", "Redis", "LLM 应用"],
        expected_salary="30k CNY/month",
        current_status="在职",
    ).model_dump()
    return {
        "candidate_profile": candidate_profile,
        "current_step": "resume_extractor",
        "trace": add_trace(state, "resume_extractor", "Extracted mock candidate profile."),
    }
