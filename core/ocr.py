from __future__ import annotations

import os
from uuid import uuid4
from dataclasses import dataclass
from pathlib import Path
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


_DEFAULT_OCR_PROVIDER: OCRProvider | None = None


def _ocr_render_dir() -> Path:
    base_dir = Path("data/test_outputs/ocr_tmp")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


class PaddleOCRProvider:
    name = "paddleocr"

    def __init__(self, *, lang: str = "ch", dpi: int = 200, cache_dir: str | Path = "data/model_cache") -> None:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        resolved_cache = str(cache_path.resolve())
        os.environ["PADDLE_PDX_CACHE_HOME"] = str((cache_path / "paddlex").resolve())
        os.environ["HOME"] = resolved_cache
        os.environ["USERPROFILE"] = resolved_cache
        os.environ["MPLCONFIGDIR"] = str((cache_path / "matplotlib").resolve())

        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OCRUnavailableError(
                "PaddleOCR is not installed. Install paddleocr to enable local OCR."
            ) from exc

        self._ocr = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
        self._dpi = dpi

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        page_texts: list[str] = []
        zoom = self._dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        tmp_path = _ocr_render_dir()
        run_id = uuid4().hex
        with fitz.open(file_path) as document:
            for page_index, page in enumerate(document, start=1):
                image_path = tmp_path / f"{run_id}-page-{page_index}.png"
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image_path.write_bytes(pixmap.tobytes("png"))
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


class EasyOCRProvider:
    name = "easyocr"

    def __init__(self, *, languages: list[str] | None = None, dpi: int = 200, cache_dir: str | Path = "data/model_cache") -> None:
        try:
            import easyocr
        except ImportError as exc:
            raise OCRUnavailableError("EasyOCR is not installed.") from exc

        cache_path = Path(cache_dir)
        model_storage = cache_path / "easyocr"
        model_storage.mkdir(parents=True, exist_ok=True)
        self._reader = easyocr.Reader(
            languages or ["ch_sim", "en"],
            gpu=False,
            model_storage_directory=str(model_storage.resolve()),
            user_network_directory=str((model_storage / "user_network").resolve()),
            verbose=False,
        )
        self._dpi = dpi

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        page_texts: list[str] = []
        zoom = self._dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        tmp_path = _ocr_render_dir()
        run_id = uuid4().hex
        with fitz.open(file_path) as document:
            for page_index, page in enumerate(document, start=1):
                image_path = tmp_path / f"{run_id}-page-{page_index}.png"
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image_path.write_bytes(pixmap.tobytes("png"))
                lines = self._reader.readtext(str(image_path), detail=0, paragraph=False)
                page_texts.append("\n".join(str(line) for line in lines))

        return "\n\n".join(text for text in page_texts if text.strip()).strip()


def get_default_ocr_provider() -> OCRProvider | None:
    global _DEFAULT_OCR_PROVIDER
    if _DEFAULT_OCR_PROVIDER is not None:
        return _DEFAULT_OCR_PROVIDER

    for provider_cls in (EasyOCRProvider, PaddleOCRProvider):
        try:
            _DEFAULT_OCR_PROVIDER = provider_cls()
            return _DEFAULT_OCR_PROVIDER
        except (OCRUnavailableError, Exception):
            continue
    return None
