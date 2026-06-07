from __future__ import annotations

import json
from pathlib import Path

from core.feedback_memory import jd_fingerprint
from harness.runner import run_evaluation


def test_jd_fingerprint_is_stable_for_whitespace_changes() -> None:
    first = jd_fingerprint("招聘 Python 工程师，要求 FastAPI 和 Redis")
    second = jd_fingerprint("  招聘   Python 工程师，要求 FastAPI 和 Redis  ")

    assert first == second


def test_human_feedback_memory_is_persisted_by_job_context() -> None:
    memory_path = Path("data/test_outputs/review_feedback_test.json")

    result = run_evaluation(
        request_id="memory-test",
        human_decision="need_more_info",
        human_feedback="该 JD 更看重 Redis 项目实战，请下一轮重点追问缓存设计细节。",
        persist_human_feedback=True,
        feedback_memory_path=str(memory_path),
    )

    records = json.loads(memory_path.read_text(encoding="utf-8"))
    record = records[-1]

    assert result["feedback_memory_record"] == record
    assert record["request_id"] == "memory-test"
    assert record["job"]["title"] == "Python 后端工程师"
    assert record["job"]["jd_fingerprint"]
    assert record["evaluation"]["rubric_track"] == "experienced"
    assert record["human_review"]["decision"] == "need_more_info"
    assert "Redis 项目实战" in record["human_review"]["feedback"]
