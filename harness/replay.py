from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.evaluator import evaluate_workflow_result


DEFAULT_REPLAY_DIR = "data/replay_cases"


def _compact_trace(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "node": item.get("node"),
            "output_summary": item.get("output_summary"),
            "extra": item.get("extra", {}),
        }
        for item in result.get("trace", [])
        if isinstance(item, dict)
    ]


def build_replay_case(
    *,
    initial_state: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    report_quality = result.get("report_quality")
    if report_quality is None:
        report_quality = evaluate_workflow_result(result).as_dict()

    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request_id": result.get("request_id") or initial_state.get("request_id"),
        "input": {
            "resume_file_path": initial_state.get("resume_file_path"),
            "resume_text": initial_state.get("resume_text"),
            "jd_text": initial_state.get("jd_text"),
            "human_decision": initial_state.get("human_decision"),
            "human_feedback": initial_state.get("human_feedback"),
            "feedback_memory_path": initial_state.get("feedback_memory_path"),
            "max_retries": initial_state.get("max_retries"),
            "force_invalid_candidate_once": initial_state.get("force_invalid_candidate_once", False),
            "force_invalid_candidate_always": initial_state.get("force_invalid_candidate_always", False),
        },
        "observed": {
            "current_step": result.get("current_step"),
            "match_score": result.get("match_score"),
            "risk_score": result.get("risk_score"),
            "human_review_status": result.get("human_review_status"),
            "retry_count": result.get("retry_count"),
            "errors": result.get("errors", []),
            "validation_errors": result.get("validation_errors", []),
            "report_quality": report_quality,
            "trace": _compact_trace(result),
        },
    }


def save_replay_case(
    replay_case: dict[str, Any],
    *,
    replay_dir: str | Path = DEFAULT_REPLAY_DIR,
) -> Path:
    output_dir = Path(replay_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    request_id = str(replay_case.get("request_id") or "replay").replace("\\", "_").replace("/", "_")
    created_at = str(replay_case.get("created_at") or datetime.now(timezone.utc).isoformat())
    timestamp = created_at.replace(":", "").replace(".", "").replace("+", "Z")
    output_path = output_dir / f"{request_id}_{timestamp}.json"
    output_path.write_text(
        json.dumps(replay_case, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def load_replay_case(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def initial_state_from_replay_case(replay_case: dict[str, Any]) -> dict[str, Any]:
    replay_input = replay_case.get("input") or {}
    state = {
        "request_id": replay_case.get("request_id"),
        "resume_file_path": replay_input.get("resume_file_path"),
        "resume_text": replay_input.get("resume_text") or "",
        "jd_text": replay_input.get("jd_text") or "",
        "document_meta": None,
        "candidate_profile": None,
        "job_profile": None,
        "scoring_rubric": None,
        "validation_errors": [],
        "retry_count": 0,
        "max_retries": replay_input.get("max_retries") or 3,
        "match_score": None,
        "match_breakdown": None,
        "risk_score": None,
        "risk_factors": [],
        "report": None,
        "human_decision": replay_input.get("human_decision"),
        "human_feedback": replay_input.get("human_feedback"),
        "human_review_required": False,
        "human_review_status": None,
        "persist_human_feedback": False,
        "feedback_memory_path": replay_input.get("feedback_memory_path"),
        "feedback_memory_record": None,
        "feedback_memory_records": [],
        "feedback_memory_summaries": [],
        "current_step": "replay_initialized",
        "errors": [],
        "trace": [],
    }

    if replay_input.get("force_invalid_candidate_once"):
        state["force_invalid_candidate_once"] = True
    if replay_input.get("force_invalid_candidate_always"):
        state["force_invalid_candidate_always"] = True
    return state


def compare_replay_result(
    *,
    replay_case: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    observed = replay_case.get("observed") or {}
    checks = {
        "current_step": result.get("current_step") == observed.get("current_step"),
        "human_review_status": result.get("human_review_status") == observed.get("human_review_status"),
        "match_score": result.get("match_score") == observed.get("match_score"),
        "risk_score": result.get("risk_score") == observed.get("risk_score"),
        "report_quality_passed": evaluate_workflow_result(result).passed
        == (observed.get("report_quality") or {}).get("passed"),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
    }
