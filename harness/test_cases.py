from __future__ import annotations

from core.state import WorkflowState


def sample_candidate_case() -> WorkflowState:
    return {
        "request_id": "demo-001",
        "resume_file_path": "data/examples/demo_resume.pdf",
        "resume_text": "",
        "jd_text": (
            "招聘高级 Python 后端工程师，要求 3 年以上经验，熟悉 FastAPI、"
            "PostgreSQL、Redis，有 LLM 应用开发经验优先。"
        ),
        "document_meta": None,
        "candidate_profile": None,
        "job_profile": None,
        "scoring_rubric": None,
        "validation_errors": [],
        "retry_count": 0,
        "max_retries": 3,
        "match_score": None,
        "match_breakdown": None,
        "risk_score": None,
        "risk_factors": [],
        "risk_features": None,
        "risk_model_path": None,
        "risk_model_used": None,
        "report": None,
        "human_decision": None,
        "human_feedback": None,
        "human_review_required": False,
        "human_review_status": None,
        "persist_human_feedback": False,
        "feedback_memory_path": None,
        "feedback_memory_record": None,
        "feedback_memory_records": [],
        "feedback_memory_summaries": [],
        "current_step": "initialized",
        "errors": [],
        "trace": [],
    }


def sample_retry_repair_case() -> WorkflowState:
    state = sample_candidate_case()
    state["request_id"] = "demo-retry-repair"
    state["force_invalid_candidate_once"] = True
    return state


def sample_retry_exhaustion_case() -> WorkflowState:
    state = sample_candidate_case()
    state["request_id"] = "demo-retry-exhaustion"
    state["force_invalid_candidate_always"] = True
    state["max_retries"] = 1
    return state
