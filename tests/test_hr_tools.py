from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import fitz

from tools.hr_tools import (
    extract_jd_profile_tool,
    extract_resume_profile_tool,
    get_hr_tool,
    list_hr_tools,
    parse_resume_pdf_tool,
    run_batch_evaluation_tool,
    save_batch_report_tool,
    send_report_email_tool,
)


def _create_text_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_hr_tools_registry_lists_callable_tools() -> None:
    tools = list_hr_tools()

    assert "parse_resume_pdf" in {tool["name"] for tool in tools}
    assert get_hr_tool("extract_jd_profile").callable is extract_jd_profile_tool


def test_extract_jd_profile_tool_returns_structured_job() -> None:
    result = extract_jd_profile_tool("校招 AI 工程师，要求 Python、PyTorch、机器学习。")

    assert result["job_profile"]["recruitment_track"] == "campus"
    assert "Python" in result["job_profile"]["required_skills"]


def test_extract_resume_profile_tool_returns_structured_candidate() -> None:
    result = extract_resume_profile_tool("姓名：李明\n本科\n项目经历：使用 Python 和 PyTorch 完成图像分类。")

    assert result["candidate_profile"]["name"] == "李明"
    assert "Python" in result["candidate_profile"]["skills"]


def test_parse_resume_pdf_tool_returns_text_and_meta() -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"tool-resume-{uuid4().hex}.pdf"
    _create_text_pdf(
        pdf_path,
        "Candidate Li Ming has Python PyTorch machine learning project experience.",
    )

    result = parse_resume_pdf_tool(str(pdf_path), use_ocr=False)

    assert "Python" in result["resume_text"]
    assert result["document_meta"]["parser"] == "pymupdf"


def test_run_batch_evaluation_tool_and_save_report_tool() -> None:
    batch_result = run_batch_evaluation_tool(
        [],
        jd_text="校招 AI 工程师，要求 Python。",
        request_id="tool-empty-batch",
    )
    saved = save_batch_report_tool(
        batch_result,
        request_id="tool-empty-batch",
        report_dir="data/test_outputs",
    )

    assert batch_result["candidate_count"] == 0
    assert Path(saved["report_path"]).exists()


def test_send_report_email_tool_skips_without_smtp_config(monkeypatch) -> None:
    for key in [
        "HR_SMTP_HOST",
        "HR_SMTP_USERNAME",
        "HR_SMTP_PASSWORD",
        "HR_SMTP_FROM",
    ]:
        monkeypatch.delenv(key, raising=False)

    result = send_report_email_tool(
        recipient="hr@example.com",
        subject="报告",
        report_markdown="# 批量候选人评估汇总",
    )

    assert result["sent"] is False
