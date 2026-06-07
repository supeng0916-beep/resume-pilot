from __future__ import annotations

from harness.runner import run_evaluation


def test_run_evaluation_accepts_cli_like_inputs() -> None:
    result = run_evaluation(
        resume_file_path="data/examples/missing_resume.pdf",
        jd_text="招聘 Python 工程师，要求熟悉 FastAPI 和 Redis。",
        request_id="test-cli-inputs",
    )

    assert result["request_id"] == "test-cli-inputs"
    assert result["document_meta"]["parser"] == "mock"
    assert result["jd_text"] == "招聘 Python 工程师，要求熟悉 FastAPI 和 Redis。"
    assert result["job_profile"]["required_skills"] == ["Python", "FastAPI", "Redis"]
    assert result["report"]
