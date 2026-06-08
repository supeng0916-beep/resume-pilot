from __future__ import annotations

from uuid import uuid4
from pathlib import Path

import fitz

from core.document_parser import clean_extracted_text, parse_pdf
from nodes.document_parser import document_parser_node


class FakeOCRProvider:
    name = "fake_ocr"

    def extract_text_from_pdf(self, file_path) -> str:
        return "姓名：李明\n硕士\n项目经历：使用 Python 和 PyTorch 完成图像分类模型。"


def _create_text_pdf(path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def _create_blank_pdf(path) -> None:
    document = fitz.open()
    document.new_page()
    document.save(path)
    document.close()


def test_parse_pdf_extracts_text_and_meta() -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"resume-{uuid4().hex}.pdf"
    _create_text_pdf(
        pdf_path,
        "Candidate Zhang San has 5 years Python FastAPI Redis experience.",
    )

    parsed = parse_pdf(pdf_path)

    assert "Python" in parsed.text
    assert parsed.meta.file_name == pdf_path.name
    assert parsed.meta.page_count == 1
    assert parsed.meta.parser == "pymupdf"
    assert parsed.meta.needs_ocr is False
    assert parsed.meta.text_length > 50


def test_clean_extracted_text_collapses_repeated_blank_lines() -> None:
    cleaned = clean_extracted_text("A\n\n\n B \x00\n\nC")

    assert cleaned == "A\n\nB\n\nC"


def test_parse_pdf_marks_image_only_pdf_as_needing_ocr_without_provider() -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"scan-{uuid4().hex}.pdf"
    _create_blank_pdf(pdf_path)

    parsed = parse_pdf(pdf_path, use_ocr=False)

    assert parsed.text == ""
    assert parsed.meta.parser == "pymupdf"
    assert parsed.meta.needs_ocr is True
    assert parsed.meta.text_length == 0


def test_parse_pdf_uses_ocr_provider_for_image_only_pdf() -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"scan-{uuid4().hex}.pdf"
    _create_blank_pdf(pdf_path)

    parsed = parse_pdf(pdf_path, ocr_provider=FakeOCRProvider())

    assert "PyTorch" in parsed.text
    assert parsed.meta.parser == "pymupdf+fake_ocr"
    assert parsed.meta.needs_ocr is False
    assert parsed.meta.text_length > 0


def test_document_parser_node_uses_mock_fallback_when_pdf_missing() -> None:
    result = document_parser_node(
        {
            "resume_file_path": "data/examples/missing_resume.pdf",
            "trace": [],
        }
    )

    assert result["document_meta"]["parser"] == "mock"
    assert result["document_meta"]["needs_ocr"] is False
    assert "张三" in result["resume_text"]
    assert "mock resume" in result["trace"][0]["output_summary"]
