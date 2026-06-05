from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def jd_extractor_node(state: WorkflowState) -> WorkflowState:
    job_profile = {
        "title": "高级 Python 后端工程师",
        "required_years": 3,
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        "nice_to_have": ["LLM 应用开发"],
        "salary_range": "25k-35k CNY/month",
    }
    return {
        "job_profile": job_profile,
        "current_step": "jd_extractor",
        "trace": add_trace(state, "jd_extractor", "Extracted mock job profile."),
    }
