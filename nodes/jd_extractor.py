from __future__ import annotations

import re

from core.schemas import JobProfile
from core.skills import extract_known_skills
from core.state import WorkflowState
from harness.trace import add_trace


def _extract_required_years(jd_text: str) -> int:
    match = re.search(r"(\d+)\s*年", jd_text)
    if not match:
        return 3
    return int(match.group(1))


def _extract_skills(jd_text: str) -> list[str]:
    skills = extract_known_skills(jd_text)
    return skills or ["Python", "FastAPI", "PostgreSQL", "Redis"]


def _extract_title(jd_text: str) -> str:
    if "实习" in jd_text:
        return "实习数据科学工程师" if "数据" in jd_text else "实习后端工程师"
    if "校招" in jd_text or "应届" in jd_text:
        if "数据" in jd_text:
            return "校招数据科学工程师"
        return "校招后端工程师"
    if "数据" in jd_text and "工程师" in jd_text:
        return "数据科学工程师"
    if "Python" in jd_text and "后端" in jd_text:
        return "Python 后端工程师"
    return "高级 Python 后端工程师"


def _extract_recruitment_track(jd_text: str) -> str:
    if "实习" in jd_text:
        return "intern"
    if "校招" in jd_text or "应届" in jd_text:
        return "campus"
    if "社招" in jd_text:
        return "experienced"
    return "unknown"


def jd_extractor_node(state: WorkflowState) -> WorkflowState:
    jd_text = state.get("jd_text", "")
    job_profile = JobProfile(
        title=_extract_title(jd_text),
        required_years=_extract_required_years(jd_text),
        required_skills=_extract_skills(jd_text),
        nice_to_have=["LLM 应用开发"],
        salary_range="25k-35k CNY/month",
        recruitment_track=_extract_recruitment_track(jd_text),
    ).model_dump()
    return {
        "job_profile": job_profile,
        "current_step": "jd_extractor",
        "trace": add_trace(state, "jd_extractor", "Extracted rule-based job profile."),
    }
