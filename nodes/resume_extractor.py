from __future__ import annotations

from core.resume_parser import parse_resume_text
from core.state import WorkflowState
from harness.trace import add_trace


def resume_extractor_node(state: WorkflowState) -> WorkflowState:
    retry_count = state.get("retry_count", 0)
    should_force_invalid = state.get("force_invalid_candidate_always") or (
        state.get("force_invalid_candidate_once") and retry_count == 0
    )

    if should_force_invalid:
        candidate_profile = {
            "name": "张三",
            "education": "本科",
            "years_experience": "five",
            "skills": ["Python", "FastAPI"],
            "expected_salary": "30k CNY/month",
            "current_status": "在职",
        }
        return {
            "candidate_profile": candidate_profile,
            "current_step": "resume_extractor",
            "trace": add_trace(
                state,
                "resume_extractor",
                "Extracted intentionally invalid mock candidate profile.",
            ),
        }

    candidate_profile = parse_resume_text(state.get("resume_text", "")).model_dump()
    return {
        "candidate_profile": candidate_profile,
        "current_step": "resume_extractor",
        "trace": add_trace(
            state,
            "resume_extractor",
            "Re-extracted corrected rule-based candidate profile."
            if retry_count
            else "Extracted rule-based candidate profile.",
        ),
    }
