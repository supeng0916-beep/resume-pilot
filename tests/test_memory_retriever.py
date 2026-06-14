from __future__ import annotations

import json
from pathlib import Path

from core.feedback_memory import jd_fingerprint
from graph.workflow import build_workflow
from harness.test_cases import sample_candidate_case


def test_memory_retriever_reads_job_specific_feedback() -> None:
    state = sample_candidate_case()
    memory_path = Path("data/test_outputs/memory_retrieval_test.json")
    state["feedback_memory_path"] = str(memory_path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(
        json.dumps(
            [
                {
                    "request_id": "old-python-backend-case",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "job": {
                        "title": "Python 后端工程师",
                        "recruitment_track": "experienced",
                        "jd_fingerprint": jd_fingerprint(state["jd_text"]),
                    },
                    "candidate": {
                        "track": "experienced",
                        "track_confidence": 0.9,
                    },
                    "evaluation": {
                        "match_score": 82,
                        "risk_score": 0.2,
                        "rubric_track": "experienced",
                    },
                    "human_review": {
                        "decision": "need_more_info",
                        "feedback": "该岗位更看重 Redis 项目实战，请重点追问缓存设计。",
                    },
                },
                {
                    "request_id": "old-campus-case",
                    "created_at": "2026-01-02T00:00:00+00:00",
                    "job": {
                        "title": "算法实习生",
                        "recruitment_track": "intern",
                        "jd_fingerprint": "other",
                    },
                    "human_review": {
                        "decision": "approve",
                        "feedback": "该实习岗位更关注论文复现。",
                    },
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = build_workflow().invoke(state)

    assert len(result["feedback_memory_records"]) == 1
    assert "Redis 项目实战" in result["feedback_memory_summaries"][0]
    assert "历史 HR 反馈参考" in result["report"]
    assert "不直接参与自动评分" in result["report"]
    assert any(item["node"] == "memory_retriever" for item in result["trace"])
    assert result["agent_outputs"]["memory_agent"]["memory_count"] == 1
