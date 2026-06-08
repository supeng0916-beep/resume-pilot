from __future__ import annotations

import os

from dotenv import load_dotenv

from core.job_parser import parse_jd_text
from core.llm_extraction import extract_job_profile_with_llm
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


def jd_extractor_node(state: WorkflowState) -> WorkflowState:
    jd_text = state.get("jd_text", "")
    if _llm_extraction_enabled(state):
        llm_result = extract_job_profile_with_llm(jd_text)
        if llm_result.profile is not None:
            return {
                "job_profile": llm_result.profile,
                "llm_extraction_status": [
                    *state.get("llm_extraction_status", []),
                    llm_result.provider_message,
                ],
                "current_step": "jd_extractor",
                "trace": add_trace(state, "jd_extractor", llm_result.provider_message),
            }
    else:
        llm_result = None

    job_profile = parse_jd_text(jd_text).model_dump()
    status_updates = list(state.get("llm_extraction_status", []))
    if llm_result is not None:
        status_updates.append(llm_result.provider_message)
    return {
        "job_profile": job_profile,
        "llm_extraction_status": status_updates,
        "current_step": "jd_extractor",
        "trace": add_trace(state, "jd_extractor", "Extracted rule-based job profile."),
    }
