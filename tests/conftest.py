from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_llm_by_default(monkeypatch) -> None:
    monkeypatch.setenv("HR_LLM_ENABLED", "false")
    monkeypatch.setenv("HR_SMTP_HOST", "")
    monkeypatch.setenv("HR_SMTP_USERNAME", "")
    monkeypatch.setenv("HR_SMTP_PASSWORD", "")
    monkeypatch.setenv("HR_SMTP_FROM", "")
