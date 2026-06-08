from __future__ import annotations

from harness.batch_runner import BatchResumeInput, calculate_rank_score, run_batch_evaluation


def test_calculate_rank_score_rewards_evidence_and_penalizes_risk() -> None:
    result = {
        "match_score": 80,
        "risk_score": 0.2,
        "candidate_profile": {
            "skill_evidence": [
                {"skill": "Python", "evidence_strength": "strong"},
                {"skill": "Redis", "evidence_strength": "unsupported"},
            ]
        },
    }

    assert calculate_rank_score(result) == 59.0


def test_run_batch_evaluation_ranks_candidates_and_builds_report() -> None:
    jd_text = "招聘 Python 后端工程师，要求熟悉 Python、FastAPI、Redis，有 3 年以上经验。"
    resumes = [
        BatchResumeInput(
            candidate_id="backend-strong",
            resume_text=(
                "姓名：李强\n本科\n5 年 Python 后端开发经验。"
                "项目经历：负责 FastAPI 服务开发，使用 Redis 做缓存优化。"
                "期望薪资：30k"
            ),
        ),
        BatchResumeInput(
            candidate_id="frontend-weak",
            resume_text=(
                "姓名：王敏\n本科\n1 年前端开发经验。"
                "技能：JavaScript、Vue。期望薪资：unknown"
            ),
        ),
    ]

    result = run_batch_evaluation(resumes, jd_text=jd_text, request_id="batch-test")

    assert result["candidate_count"] == 2
    assert result["ranked_candidates"][0]["candidate_id"] == "backend-strong"
    assert result["ranked_candidates"][0]["request_id"].startswith("batch-test-")
    assert result["ranked_candidates"][0]["rank_score"] > result["ranked_candidates"][1]["rank_score"]
    assert "批量候选人评估汇总" in result["batch_report"]
    assert "候选人排名" in result["batch_report"]
    assert "技能覆盖矩阵" in result["batch_report"]
    assert len(result["results"]) == 2
    assert result["results"][0]["document_meta"]["parser"] == "provided_text"


def test_run_batch_evaluation_reports_progress_events() -> None:
    events = []
    resumes = [
        BatchResumeInput(
            candidate_id="candidate-a",
            resume_text="姓名：李明\n本科\n项目经历：使用 Python 完成数据分析。",
        )
    ]

    run_batch_evaluation(
        resumes,
        jd_text="校招数据分析工程师，要求 Python。",
        request_id="progress-test",
        progress_callback=lambda index, total, resume, status: events.append(
            (index, total, resume.candidate_id, status)
        ),
    )

    assert events == [
        (1, 1, "candidate-a", "started"),
        (1, 1, "candidate-a", "completed"),
    ]


def test_batch_report_does_not_recommend_ocr_failed_candidates() -> None:
    summaries = [
        {
            "candidate_id": "scan-only",
            "name": "未知候选人",
            "rank_score": 30,
            "match_score": 41,
            "risk_score": 0.47,
            "evidence_confidence": 0,
            "matched_skills": [],
            "needs_ocr": True,
            "review_reasons": ["PDF 需要 OCR，当前文本解析不可用"],
            "errors": [],
        }
    ]

    from harness.batch_runner import render_batch_report

    report = render_batch_report(summaries, jd_text="校招 AI 工程师")

    assert "暂无可直接推荐候选人" in report
    assert "PDF 需要 OCR" in report
