from __future__ import annotations

import concurrent.futures
import os
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from dotenv import load_dotenv

from core.llm_provider import extract_pdf_text_with_vision_llm
from core.ocr import OCRProvider, get_default_ocr_provider
from core.schemas import DocumentMeta


MIN_TEXT_LENGTH_FOR_TEXT_PDF = 50
MIN_TEXT_LENGTH_FOR_USABLE_PARSE = 20
DEFAULT_OCR_TIMEOUT_SECONDS = 12.0


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    meta: DocumentMeta


def clean_extracted_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\x00", "").splitlines()]
    cleaned_lines: list[str] = []
    previous_blank = False

    for line in lines:
        if not line:
            if not previous_blank:
                cleaned_lines.append("")
            previous_blank = True
            continue

        cleaned_lines.append(line)
        previous_blank = False

    return "\n".join(cleaned_lines).strip()


def assess_parse_quality(text: str) -> tuple[float, list[str]]:
    cleaned = clean_extracted_text(text)
    flags: list[str] = []
    if len(cleaned) < MIN_TEXT_LENGTH_FOR_USABLE_PARSE:
        flags.append("text_too_short")

    meaningful_chars = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]", cleaned)
    meaningful_ratio = len(meaningful_chars) / max(len(cleaned), 1)
    if cleaned and meaningful_ratio < 0.35:
        flags.append("low_meaningful_char_ratio")

    resume_markers = ["姓名", "教育", "学历", "项目", "实习", "工作", "技能", "Python"]
    marker_hits = sum(1 for marker in resume_markers if marker.lower() in cleaned.lower())
    if marker_hits == 0:
        flags.append("missing_resume_markers")

    score = 0.2
    if len(cleaned) >= MIN_TEXT_LENGTH_FOR_USABLE_PARSE:
        score += 0.3
    score += min(0.3, marker_hits * 0.1)
    if meaningful_ratio >= 0.35:
        score += 0.2
    return round(max(0.0, min(1.0, score)), 4), flags


def _ocr_timeout_seconds() -> float:
    load_dotenv()
    return float(os.getenv("HR_OCR_TIMEOUT_SECONDS", str(DEFAULT_OCR_TIMEOUT_SECONDS)))


def _extract_ocr_with_timeout(provider: OCRProvider, path: Path, timeout_seconds: float) -> tuple[str, str | None]:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(provider.extract_text_from_pdf, path)
    try:
        return future.result(timeout=timeout_seconds), None
    except concurrent.futures.TimeoutError:
        future.cancel()
        return "", f"OCR timed out after {timeout_seconds:g}s"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _build_meta(
    *,
    path: Path,
    page_count: int,
    parser: str,
    needs_ocr: bool,
    text: str,
    extra_flags: list[str] | None = None,
) -> DocumentMeta:
    quality_score, quality_flags = assess_parse_quality(text)
    return DocumentMeta(
        file_name=path.name,
        page_count=page_count,
        parser=parser,
        needs_ocr=needs_ocr,
        text_length=len(text),
        parse_quality_score=quality_score,
        parse_quality_flags=[*(extra_flags or []), *quality_flags],
    )


def parse_pdf(
    file_path: str | Path,
    *,
    ocr_provider: OCRProvider | None = None,
    use_ocr: bool = True,
) -> ParsedDocument:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file does not exist: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {path.suffix}")

    page_texts: list[str] = []
    with fitz.open(path) as document:
        for page in document:
            page_texts.append(page.get_text("text"))

        raw_text = "\n".join(page_texts)
        cleaned_text = clean_extracted_text(raw_text)
        page_count = document.page_count

    if len(cleaned_text) >= MIN_TEXT_LENGTH_FOR_TEXT_PDF:
        meta = _build_meta(
            path=path,
            page_count=page_count,
            parser="pymupdf",
            needs_ocr=False,
            text=cleaned_text,
        )
        return ParsedDocument(text=cleaned_text, meta=meta)

    fallback_text = cleaned_text
    fallback_parser = "pymupdf"
    fallback_flags: list[str] = []
    provider = None
    if use_ocr:
        provider = ocr_provider if ocr_provider is not None else get_default_ocr_provider()
    if provider is not None:
        try:
            raw_ocr_text, timeout_message = _extract_ocr_with_timeout(provider, path, _ocr_timeout_seconds())
            ocr_text = clean_extracted_text(raw_ocr_text)
            if ocr_text:
                fallback_text = ocr_text
                fallback_parser = f"pymupdf+{provider.name}"
                meta = _build_meta(
                    path=path,
                    page_count=page_count,
                    parser=fallback_parser,
                    needs_ocr=False,
                    text=ocr_text,
                    extra_flags=["ocr_low_quality"] if assess_parse_quality(ocr_text)[0] < 0.55 else None,
                )
                if meta.parse_quality_score >= 0.55:
                    return ParsedDocument(text=ocr_text, meta=meta)
                fallback_flags = ["ocr_low_quality"]
            elif timeout_message:
                fallback_flags.append(timeout_message)
        except Exception:
            pass

    vision_result = extract_pdf_text_with_vision_llm(path)
    vision_text = clean_extracted_text(vision_result.content)
    if vision_text:
        meta = _build_meta(
            path=path,
            page_count=page_count,
            parser="pymupdf+vision_llm",
            needs_ocr=False,
            text=vision_text,
        )
        return ParsedDocument(text=vision_text, meta=meta)

    meta = _build_meta(
        path=path,
        page_count=page_count,
        parser=fallback_parser,
        needs_ocr=True,
        text=fallback_text,
        extra_flags=[*fallback_flags, *([vision_result.provider_message] if vision_result.enabled else [])],
    )

    return ParsedDocument(text=fallback_text, meta=meta)


def mock_parsed_resume(file_name: str | None = None) -> ParsedDocument:
    text = (
        "候选人：张三。5 年 Python 后端开发经验，熟悉 FastAPI、PostgreSQL、Redis，"
        "参与过 LLM 应用和数据平台项目。期望薪资 30k，当前在职，学历本科。"
    )
    return ParsedDocument(
        text=text,
        meta=DocumentMeta(
            file_name=file_name,
            page_count=1,
            parser="mock",
            needs_ocr=False,
            text_length=len(text),
            parse_quality_score=1.0,
        ),
    )
