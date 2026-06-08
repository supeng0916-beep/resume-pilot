from __future__ import annotations

import os

from dotenv import load_dotenv

from core.llm_extraction import extract_resume_profile_with_llm
from core.resume_parser import parse_resume_text
from core.state import WorkflowState
from harness.trace import add_trace


def _llm_extraction_enabled(state: WorkflowState) -> bool:
    state_value = state.get("enable_llm_structured_extraction")
    if state_value is not None:
        return bool(state_value)
    load_dotenv()
    return os.getenv("HR_LLM_STRUCTURED_EXTRACTION_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }


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

    resume_text = state.get("resume_text", "")
    if _llm_extraction_enabled(state):
        llm_result = extract_resume_profile_with_llm(resume_text)
        if llm_result.profile is not None:
            return {
                "candidate_profile": llm_result.profile,
                "llm_extraction_status": [
                    *state.get("llm_extraction_status", []),
                    llm_result.provider_message,
                ],
                "current_step": "resume_extractor",
                "trace": add_trace(
                    state,
                    "resume_extractor",
                    llm_result.provider_message,
                ),
            }
    else:
        llm_result = None

    candidate_profile = parse_resume_text(resume_text).model_dump()
    status_updates = list(state.get("llm_extraction_status", []))
    if llm_result is not None:
        status_updates.append(llm_result.provider_message)
    return {
        "candidate_profile": candidate_profile,
        "llm_extraction_status": status_updates,
        "current_step": "resume_extractor",
        "trace": add_trace(
            state,
            "resume_extractor",
            "Re-extracted corrected rule-based candidate profile."
            if retry_count
            else "Extracted rule-based candidate profile.",
        ),
    }
