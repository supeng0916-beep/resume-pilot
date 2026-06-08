from __future__ import annotations

from core import ocr


class FakeProvider:
    name = "fake"

    def extract_text_from_pdf(self, file_path) -> str:
        return "text"


def test_get_default_ocr_provider_reuses_cached_instance(monkeypatch) -> None:
    created = []

    class FakeProviderFactory(FakeProvider):
        def __init__(self) -> None:
            created.append("created")

    monkeypatch.setattr(ocr, "_DEFAULT_OCR_PROVIDER", None)
    monkeypatch.setattr(ocr, "EasyOCRProvider", FakeProviderFactory)
    monkeypatch.setattr(ocr, "PaddleOCRProvider", FakeProviderFactory)

    first = ocr.get_default_ocr_provider()
    second = ocr.get_default_ocr_provider()

    assert first is second
    assert created == ["created"]
