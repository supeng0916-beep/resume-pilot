from __future__ import annotations

from uuid import uuid4
from pathlib import Path

import fitz

from core.document_parser import clean_extracted_text, parse_pdf
from core.llm_provider import LLMEnhancementResult
from nodes.document_parser import document_parser_node


class FakeOCRProvider:
    name = "fake_ocr"

    def extract_text_from_pdf(self, file_path) -> str:
        return "姓名：李明\n硕士\n项目经历：使用 Python 和 PyTorch 完成图像分类模型。"


class SlowOCRProvider:
    name = "slow_ocr"

    def extract_text_from_pdf(self, file_path) -> str:
        import time

        time.sleep(0.2)
        return "姓名：慢 OCR"


class LowQualityOCRProvider:
    name = "low_quality_ocr"

    def extract_text_from_pdf(self, file_path) -> str:
        return "---- ////"


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
    assert parsed.meta.parse_quality_score > 0


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


def test_parse_pdf_marks_low_quality_ocr_for_review() -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"scan-{uuid4().hex}.pdf"
    _create_blank_pdf(pdf_path)

    parsed = parse_pdf(pdf_path, ocr_provider=LowQualityOCRProvider())

    assert parsed.meta.parser == "pymupdf+low_quality_ocr"
    assert parsed.meta.needs_ocr is True
    assert "ocr_low_quality" in parsed.meta.parse_quality_flags


def test_parse_pdf_falls_back_to_vision_llm_after_ocr_timeout(monkeypatch) -> None:
    output_dir = Path("data/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"scan-{uuid4().hex}.pdf"
    _create_blank_pdf(pdf_path)
    monkeypatch.setenv("HR_OCR_TIMEOUT_SECONDS", "0.01")

    def fake_vision(file_path):
        return LLMEnhancementResult(
            enabled=True,
            content="姓名：王强\n本科\n项目经历：使用 Python 完成推荐系统。",
            provider_message="Vision LLM PDF 解析已生成。",
        )

    monkeypatch.setattr("core.document_parser.extract_pdf_text_with_vision_llm", fake_vision)

    parsed = parse_pdf(pdf_path, ocr_provider=SlowOCRProvider())

    assert parsed.meta.parser == "pymupdf+vision_llm"
    assert parsed.meta.needs_ocr is False
    assert "王强" in parsed.text


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
