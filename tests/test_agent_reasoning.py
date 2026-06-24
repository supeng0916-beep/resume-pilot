from __future__ import annotations

from core.agent_reasoning import enrich_findings_with_llm
from core.model_gateway import ChatResponse, ModelGatewayConfig, TokenUsage


class FakeGateway:
    def chat(self, *, messages, config):
        return ChatResponse(
            content='{"findings": {"interview_probes": ["Ask about Redis production depth."]}, "concerns": ["Redis evidence is thin."]}',
            model=config.model,
            provider=config.provider,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=8, total_tokens=18),
        )


def test_agent_reasoning_enriches_findings_with_schema_guarded_llm(monkeypatch) -> None:
    monkeypatch.setenv("HR_AGENT_LLM_ENABLED", "true")
    result = enrich_findings_with_llm(
        agent_name="candidate_analyst",
        role="candidate_profile_review",
        base_findings={"strengths": ["Python"], "gaps": []},
        context={"candidate": {"skills": ["Python", "Redis"]}},
        config=ModelGatewayConfig(
            provider="ollama",
            model="qwen3:1.7b",
            base_url="http://localhost:11434/v1",
        ),
        gateway=FakeGateway(),
    )

    assert result.enabled is True
    assert result.findings["strengths"] == ["Python"]
    assert result.findings["interview_probes"] == ["Ask about Redis production depth."]
    assert result.concerns == ["Redis evidence is thin."]
    assert result.model_name == "qwen3:1.7b"
    assert result.provider == "ollama"
    assert result.token_usage.total_tokens == 18


def test_agent_reasoning_falls_back_when_agent_llm_is_disabled(monkeypatch) -> None:
    monkeypatch.setenv("HR_AGENT_LLM_ENABLED", "false")
    result = enrich_findings_with_llm(
        agent_name="candidate_analyst",
        role="candidate_profile_review",
        base_findings={"strengths": ["Python"], "gaps": []},
        context={},
        config=ModelGatewayConfig(provider="ollama", model="qwen3:1.7b"),
        gateway=FakeGateway(),
    )

    assert result.enabled is False
    assert result.findings == {"strengths": ["Python"], "gaps": []}
    assert result.concerns == []
