from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

import fitz


class OCRProvider(Protocol):
    name: str

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        ...


@dataclass(frozen=True)
class OCRResult:
    text: str
    provider_name: str


class OCRUnavailableError(RuntimeError):
    pass


class PaddleOCRProvider:
    name = "paddleocr"

    def __init__(self, *, lang: str = "ch", dpi: int = 200) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OCRUnavailableError(
                "PaddleOCR is not installed. Install paddleocr to enable local OCR."
            ) from exc

        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        self._dpi = dpi

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        page_texts: list[str] = []
        zoom = self._dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with fitz.open(file_path) as document:
                for page_index, page in enumerate(document, start=1):
                    image_path = tmp_path / f"page-{page_index}.png"
                    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                    pixmap.save(image_path)
                    page_texts.append(self._extract_text_from_image(image_path))

        return "\n\n".join(text for text in page_texts if text.strip()).strip()

    def _extract_text_from_image(self, image_path: Path) -> str:
        result = self._ocr.ocr(str(image_path), cls=True)
        lines: list[str] = []
        for page_result in result or []:
            for item in page_result or []:
                if len(item) >= 2 and isinstance(item[1], (list, tuple)) and item[1]:
                    lines.append(str(item[1][0]))
        return "\n".join(lines)


def get_default_ocr_provider() -> OCRProvider | None:
    try:
        return PaddleOCRProvider()
    except OCRUnavailableError:
        return None
