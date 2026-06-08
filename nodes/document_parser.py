from __future__ import annotations

from pathlib import Path

from core.document_parser import mock_parsed_resume, parse_pdf
from core.schemas import DocumentMeta
from core.state import WorkflowState
from harness.trace import add_trace


def document_parser_node(state: WorkflowState) -> WorkflowState:
    provided_resume_text = state.get("resume_text", "").strip()
    if provided_resume_text:
        document_meta = DocumentMeta(
            file_name=None,
            page_count=0,
            parser="provided_text",
            needs_ocr=False,
            text_length=len(provided_resume_text),
        )
        return {
            "resume_text": provided_resume_text,
            "document_meta": document_meta.model_dump(),
            "current_step": "document_parser",
            "trace": add_trace(
                state,
                "document_parser",
                "Used provided resume text.",
                {
                    "parser": document_meta.parser,
                    "text_length": document_meta.text_length,
                    "needs_ocr": document_meta.needs_ocr,
                },
            ),
        }

    resume_file_path = state.get("resume_file_path")
    used_fallback = not resume_file_path or not Path(resume_file_path).exists()

    parsed_document = (
        mock_parsed_resume(resume_file_path)
        if used_fallback
        else parse_pdf(resume_file_path)
    )

    return {
        "resume_text": parsed_document.text,
        "document_meta": parsed_document.meta.model_dump(),
        "current_step": "document_parser",
        "trace": add_trace(
            state,
            "document_parser",
            "Used mock resume text because PDF file was not found."
            if used_fallback
            else "Parsed resume PDF into resume_text.",
            {
                "parser": parsed_document.meta.parser,
                "text_length": parsed_document.meta.text_length,
                "needs_ocr": parsed_document.meta.needs_ocr,
            },
        ),
    }
