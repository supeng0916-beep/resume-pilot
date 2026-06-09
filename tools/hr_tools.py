from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core.control_cabin import save_batch_report
from core.document_parser import parse_pdf
from core.email_sender import send_report_email
from core.job_parser import parse_jd_text
from core.resume_parser import parse_resume_text
from harness.batch_runner import resume_inputs_from_paths, run_batch_evaluation


ToolCallable = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class HRTool:
    name: str
    description: str
    callable: ToolCallable


def parse_resume_pdf_tool(file_path: str, *, use_ocr: bool = True) -> dict[str, Any]:
    parsed = parse_pdf(file_path, use_ocr=use_ocr)
    return {
        "resume_text": parsed.text,
        "document_meta": parsed.meta.model_dump(),
    }


def extract_resume_profile_tool(resume_text: str) -> dict[str, Any]:
    return {
        "candidate_profile": parse_resume_text(resume_text).model_dump(),
    }


def extract_jd_profile_tool(jd_text: str) -> dict[str, Any]:
    return {
        "job_profile": parse_jd_text(jd_text).model_dump(),
    }


def run_batch_evaluation_tool(
    resume_paths: list[str],
    *,
    jd_text: str,
    request_id: str = "tool-batch-run",
    feedback_memory_path: str | None = None,
    risk_model_path: str | None = None,
) -> dict[str, Any]:
    return run_batch_evaluation(
        resume_inputs_from_paths(resume_paths),
        jd_text=jd_text,
        request_id=request_id,
        feedback_memory_path=feedback_memory_path,
        risk_model_path=risk_model_path,
    )


def save_batch_report_tool(
    batch_result: dict[str, Any],
    *,
    request_id: str,
    report_dir: str = "data/test_outputs",
) -> dict[str, Any]:
    report_path = save_batch_report(
        batch_result,
        request_id=request_id,
        report_dir=Path(report_dir),
    )
    return {"report_path": str(report_path)}


def send_report_email_tool(
    *,
    recipient: str,
    subject: str,
    report_markdown: str,
    attachment_name: str = "batch_report.md",
) -> dict[str, Any]:
    result = send_report_email(
        recipient=recipient,
        subject=subject,
        report_markdown=report_markdown,
        attachment_name=attachment_name,
    )
    return {
        "sent": result.sent,
        "message": result.message,
    }


HR_TOOLS: dict[str, HRTool] = {
    "parse_resume_pdf": HRTool(
        name="parse_resume_pdf",
        description="Parse a resume PDF into text and document metadata, using OCR fallback when available.",
        callable=parse_resume_pdf_tool,
    ),
    "extract_resume_profile": HRTool(
        name="extract_resume_profile",
        description="Extract a structured candidate profile from resume text.",
        callable=extract_resume_profile_tool,
    ),
    "extract_jd_profile": HRTool(
        name="extract_jd_profile",
        description="Extract a structured job profile from JD text.",
        callable=extract_jd_profile_tool,
    ),
    "run_batch_evaluation": HRTool(
        name="run_batch_evaluation",
        description="Evaluate multiple resume PDF paths against one JD and return ranking/report results.",
        callable=run_batch_evaluation_tool,
    ),
    "save_batch_report": HRTool(
        name="save_batch_report",
        description="Persist a batch Markdown report to disk.",
        callable=save_batch_report_tool,
    ),
    "send_report_email": HRTool(
        name="send_report_email",
        description="Send a batch Markdown report to an HR mailbox when SMTP is configured.",
        callable=send_report_email_tool,
    ),
}


def list_hr_tools() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
        }
        for tool in HR_TOOLS.values()
    ]


def get_hr_tool(name: str) -> HRTool:
    try:
        return HR_TOOLS[name]
    except KeyError as exc:
        raise KeyError(f"unknown HR tool: {name}") from exc
