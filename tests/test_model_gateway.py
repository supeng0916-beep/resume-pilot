from __future__ import annotations

from core.model_gateway import (
    ChatResponse,
    ModelGatewayConfig,
    OpenAICompatibleModelGateway,
    TokenUsage,
    load_model_gateway_config_from_env,
    normalize_openai_compatible_url,
)


class FakeGatewayClient:
    def __init__(self, payload: dict):
        self.payload = payload
        self.requests = []

    def post(self, *, url: str, headers: dict[str, str], payload: dict, timeout_seconds: float) -> dict:
        self.requests.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.payload


def test_load_model_gateway_config_supports_ollama_openai_compatible_env(monkeypatch) -> None:
    monkeypatch.setenv("HR_LLM_ENABLED", "true")
    monkeypatch.setenv("HR_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("HR_LLM_MODEL", "qwen2.5:7b")
    monkeypatch.setenv("HR_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("HR_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = load_model_gateway_config_from_env()

    assert config is not None
    assert config.provider == "ollama"
    assert config.api_key == "local"
    assert config.model == "qwen2.5:7b"
    assert config.base_url == "http://localhost:11434/v1/chat/completions"


def test_openai_compatible_gateway_returns_content_and_token_usage() -> None:
    client = FakeGatewayClient(
        {
            "choices": [{"message": {"content": "structured answer"}}],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
            },
        }
    )
    gateway = OpenAICompatibleModelGateway(client=client)

    response = gateway.chat(
        messages=[{"role": "user", "content": "hello"}],
        config=ModelGatewayConfig(
            provider="openai_compatible",
            model="local-model",
            api_key="local",
            base_url="http://127.0.0.1:1234/v1",
        ),
    )

    assert response == ChatResponse(
        content="structured answer",
        model="local-model",
        provider="openai_compatible",
        token_usage=TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18),
    )
    assert client.requests[0]["url"] == "http://127.0.0.1:1234/v1/chat/completions"


def test_normalize_openai_compatible_url_accepts_chat_completion_url() -> None:
    assert (
        normalize_openai_compatible_url("http://localhost:1234/v1/chat/completions")
        == "http://localhost:1234/v1/chat/completions"
    )
