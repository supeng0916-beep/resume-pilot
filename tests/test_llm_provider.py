from __future__ import annotations

from core.llm_provider import (
    LLMConfig,
    build_report_enhancement_messages,
    generate_report_llm_enhancement,
    load_llm_config_from_env,
)


class FakeChatClient:
    def complete(self, *, messages, config) -> str:
        assert config.model == "fake-model"
        assert messages[0]["role"] == "system"
        return "### LLM 辅助摘要\n候选人需要进一步核实项目深度。"


class FailingChatClient:
    def complete(self, *, messages, config) -> str:
        raise RuntimeError("network down")


def _state() -> dict:
    return {
        "candidate_profile": {
            "name": "李明",
            "candidate_track": "campus",
            "skills": ["Python", "PyTorch"],
            "education": "本科",
            "years_experience": 0,
        },
        "job_profile": {
            "title": "校招 AI 工程师",
            "required_skills": ["Python", "PyTorch"],
        },
        "match_score": 78,
        "risk_score": 0.2,
        "match_breakdown": {
            "matched_skills": ["Python", "PyTorch"],
            "evidence_notes": ["Python 有项目证据"],
        },
    }


def test_load_llm_config_requires_enable_flag(monkeypatch) -> None:
    monkeypatch.setenv("HR_LLM_API_KEY", "secret")
    monkeypatch.setenv("HR_LLM_MODEL", "fake-model")
    monkeypatch.setenv("HR_LLM_ENABLED", "false")

    assert load_llm_config_from_env() is None


def test_load_llm_config_reads_enabled_env(monkeypatch) -> None:
    monkeypatch.setenv("HR_LLM_ENABLED", "true")
    monkeypatch.setenv("HR_LLM_API_KEY", "secret")
    monkeypatch.setenv("HR_LLM_MODEL", "fake-model")
    monkeypatch.setenv("HR_LLM_BASE_URL", "https://llm.example.com/v1/chat/completions")

    config = load_llm_config_from_env()

    assert config is not None
    assert config.model == "fake-model"
    assert config.base_url == "https://llm.example.com/v1/chat/completions"


def test_build_report_enhancement_messages_include_report_context() -> None:
    messages = build_report_enhancement_messages(_state(), "# 招聘评估报告")

    assert messages[0]["role"] == "system"
    assert "招聘评估报告" in messages[1]["content"]


def test_generate_report_llm_enhancement_uses_client() -> None:
    result = generate_report_llm_enhancement(
        _state(),
        "# 招聘评估报告",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=FakeChatClient(),
    )

    assert result.enabled is True
    assert "LLM 辅助摘要" in result.content


def test_generate_report_llm_enhancement_keeps_base_report_on_failure() -> None:
    result = generate_report_llm_enhancement(
        _state(),
        "# 招聘评估报告",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=FailingChatClient(),
    )

    assert result.enabled is True
    assert result.content == ""
    assert "已保留确定性报告" in result.provider_message
