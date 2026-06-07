from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from core.schemas import DocumentMeta


MIN_TEXT_LENGTH_FOR_TEXT_PDF = 50


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


def parse_pdf(file_path: str | Path) -> ParsedDocument:
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
        meta = DocumentMeta(
            file_name=path.name,
            page_count=document.page_count,
            parser="pymupdf",
            needs_ocr=len(cleaned_text) < MIN_TEXT_LENGTH_FOR_TEXT_PDF,
            text_length=len(cleaned_text),
        )

    return ParsedDocument(text=cleaned_text, meta=meta)


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
        ),
    )
