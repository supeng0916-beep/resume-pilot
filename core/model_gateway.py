from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal, Protocol
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv
from pydantic import BaseModel, Field


ModelProvider = Literal["openai", "openai_compatible", "ollama", "lmstudio", "disabled"]

DEFAULT_OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OLLAMA_CHAT_URL = "http://localhost:11434/v1/chat/completions"
DEFAULT_LMSTUDIO_CHAT_URL = "http://localhost:1234/v1/chat/completions"


class TokenUsage(BaseModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ChatResponse(BaseModel):
    content: str = Field(min_length=1)
    model: str
    provider: ModelProvider
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


@dataclass(frozen=True)
class ModelGatewayConfig:
    provider: ModelProvider
    model: str
    api_key: str = "local"
    base_url: str = DEFAULT_OPENAI_CHAT_URL
    timeout_seconds: float = 30.0
    ignore_proxy: bool = True
    temperature: float = 0.2


class GatewayHttpClient(Protocol):
    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        ...


class UrllibGatewayHttpClient:
    def __init__(self, *, ignore_proxy: bool = True) -> None:
        self.ignore_proxy = ignore_proxy

    def post(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if self.ignore_proxy else None
        try:
            open_request = opener.open if opener is not None else urllib.request.urlopen
            with open_request(request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Model gateway request failed: HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Model gateway request failed: {exc}") from exc


def normalize_openai_compatible_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        return base_url
    if not path:
        path = "/v1/chat/completions"
    elif path == "/v1":
        path = "/v1/chat/completions"
    else:
        path = f"{path}/chat/completions"
    return urlunparse(parsed._replace(path=path))


def _default_base_url(provider: ModelProvider) -> str:
    if provider == "ollama":
        return DEFAULT_OLLAMA_CHAT_URL
    if provider == "lmstudio":
        return DEFAULT_LMSTUDIO_CHAT_URL
    return DEFAULT_OPENAI_CHAT_URL


def load_model_gateway_config_from_env() -> ModelGatewayConfig | None:
    load_dotenv()
    enabled = os.getenv("HR_LLM_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        return None

    provider = os.getenv("HR_LLM_PROVIDER", "openai_compatible").lower()
    if provider not in {"openai", "openai_compatible", "ollama", "lmstudio"}:
        provider = "openai_compatible"
    typed_provider: ModelProvider = provider  # type: ignore[assignment]

    model = os.getenv("HR_LLM_MODEL")
    if not model:
        return None

    if typed_provider in {"ollama", "lmstudio"}:
        api_key = "local"
    else:
        api_key = os.getenv("HR_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key and typed_provider == "openai_compatible":
            api_key = "local"
        if not api_key:
            return None

    timeout = float(os.getenv("HR_LLM_TIMEOUT_SECONDS", "30"))
    ignore_proxy = os.getenv("HR_LLM_IGNORE_PROXY", "true").lower() not in {"0", "false", "no"}
    base_url = normalize_openai_compatible_url(os.getenv("HR_LLM_BASE_URL") or _default_base_url(typed_provider))
    return ModelGatewayConfig(
        provider=typed_provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=timeout,
        ignore_proxy=ignore_proxy,
    )


class OpenAICompatibleModelGateway:
    def __init__(self, *, client: GatewayHttpClient | None = None) -> None:
        self.client = client

    def chat(self, *, messages: list[dict[str, Any]], config: ModelGatewayConfig) -> ChatResponse:
        client = self.client or UrllibGatewayHttpClient(ignore_proxy=config.ignore_proxy)
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
        }
        response_payload = client.post(
            url=normalize_openai_compatible_url(config.base_url),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            timeout_seconds=config.timeout_seconds,
        )
        choices = response_payload.get("choices") or []
        if not choices:
            raise RuntimeError("Model gateway response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Model gateway response content is empty")
        usage = response_payload.get("usage") or {}
        return ChatResponse(
            content=content.strip(),
            model=config.model,
            provider=config.provider,
            token_usage=TokenUsage(
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
                total_tokens=int(usage.get("total_tokens") or 0),
            ),
        )


def chat_with_config(
    *,
    messages: list[dict[str, Any]],
    config: ModelGatewayConfig | None = None,
    gateway: OpenAICompatibleModelGateway | None = None,
) -> ChatResponse | None:
    model_config = config or load_model_gateway_config_from_env()
    if model_config is None:
        return None
    return (gateway or OpenAICompatibleModelGateway()).chat(messages=messages, config=model_config)
