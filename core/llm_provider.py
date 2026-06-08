from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

from core.state import WorkflowState

try:
    import fitz
except ImportError:  # pragma: no cover - PyMuPDF is a project dependency.
    fitz = None


DEFAULT_OPENAI_COMPATIBLE_CHAT_URL = "https://api.openai.com/v1/chat/completions"


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str
    base_url: str = DEFAULT_OPENAI_COMPATIBLE_CHAT_URL
    timeout_seconds: float = 30.0
    ignore_proxy: bool = True


@dataclass(frozen=True)
class LLMEnhancementResult:
    enabled: bool
    content: str
    provider_message: str


class ChatCompletionClient(Protocol):
    def complete(self, *, messages: list[dict[str, Any]], config: LLMConfig) -> str:
        ...


class OpenAICompatibleChatClient:
    def complete(self, *, messages: list[dict[str, Any]], config: LLMConfig) -> str:
        payload = json.dumps(
            {
                "model": config.model,
                "messages": messages,
                "temperature": 0.2,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            normalize_chat_completions_url(config.base_url),
            data=payload,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if config.ignore_proxy else None
        try:
            open_request = opener.open if opener is not None else urllib.request.urlopen
            with open_request(request, timeout=config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        choices = response_payload.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response has no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LLM response content is empty")
        return content.strip()


def normalize_chat_completions_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        return base_url
    if not path or path == "/v1":
        path = f"{path}/chat/completions" if path else "/chat/completions"
    else:
        path = f"{path}/chat/completions"
    return urlunparse(parsed._replace(path=path))


def load_llm_config_from_env() -> LLMConfig | None:
    load_dotenv()
    enabled = os.getenv("HR_LLM_ENABLED", "false").lower() in {"1", "true", "yes"}
    if not enabled:
        return None

    api_key = os.getenv("HR_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("HR_LLM_MODEL")
    if not api_key or not model:
        return None

    timeout = float(os.getenv("HR_LLM_TIMEOUT_SECONDS", "30"))
    ignore_proxy = os.getenv("HR_LLM_IGNORE_PROXY", "true").lower() not in {"0", "false", "no"}
    return LLMConfig(
        api_key=api_key,
        model=model,
        base_url=normalize_chat_completions_url(os.getenv("HR_LLM_BASE_URL") or DEFAULT_OPENAI_COMPATIBLE_CHAT_URL),
        timeout_seconds=timeout,
        ignore_proxy=ignore_proxy,
    )


def build_report_enhancement_messages(state: WorkflowState, base_report: str) -> list[dict[str, Any]]:
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}

    user_content = {
        "candidate": {
            "name": candidate.get("name"),
            "track": candidate.get("candidate_track"),
            "skills": candidate.get("skills"),
            "education": candidate.get("education"),
            "years_experience": candidate.get("years_experience"),
        },
        "job": job,
        "match_score": state.get("match_score"),
        "risk_score": state.get("risk_score"),
        "matched_skills": match_breakdown.get("matched_skills"),
        "evidence_notes": match_breakdown.get("evidence_notes"),
        "base_report": base_report,
    }
    return [
        {
            "role": "system",
            "content": (
                "你是谨慎的招聘评估助手。只能基于给定结构化信息和报告内容补充建议，"
                "不得编造候选人没有提供的经历。输出中文 Markdown，包含三个小节："
                "LLM 辅助摘要、建议追问、人工复核提醒。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(user_content, ensure_ascii=False),
        },
    ]


def generate_report_llm_enhancement(
    state: WorkflowState,
    base_report: str,
    *,
    config: LLMConfig | None = None,
    client: ChatCompletionClient | None = None,
) -> LLMEnhancementResult:
    llm_config = config or load_llm_config_from_env()
    if llm_config is None:
        return LLMEnhancementResult(
            enabled=False,
            content="",
            provider_message="LLM 未启用或配置不完整。",
        )

    chat_client = client or OpenAICompatibleChatClient()
    try:
        content = chat_client.complete(
            messages=build_report_enhancement_messages(state, base_report),
            config=llm_config,
        )
    except Exception as exc:
        return LLMEnhancementResult(
            enabled=True,
            content="",
            provider_message=f"LLM 增强失败，已保留确定性报告：{exc}",
        )

    return LLMEnhancementResult(
        enabled=True,
        content=content,
        provider_message="LLM 增强已生成。",
    )


def render_pdf_pages_as_data_urls(
    file_path: str | Path,
    *,
    max_pages: int = 3,
    dpi: int = 160,
) -> list[str]:
    if fitz is None:
        raise RuntimeError("PyMuPDF is required to render PDF pages for vision LLM parsing.")

    data_urls: list[str] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(file_path) as document:
        for page in list(document)[:max_pages]:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_base64 = base64.b64encode(pixmap.tobytes("png")).decode("ascii")
            data_urls.append(f"data:image/png;base64,{image_base64}")
    return data_urls


def build_pdf_vision_messages(data_urls: list[str]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "请从这些 PDF 页面截图中提取简历原文。尽量保持姓名、教育背景、技能、项目经历、"
                "实习/工作经历、奖项证书等信息完整。只输出可用于结构化解析的纯文本，不要编造。"
            ),
        }
    ]
    for data_url in data_urls:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": data_url},
            }
        )
    return [
        {
            "role": "system",
            "content": "你是严谨的简历 OCR/视觉解析助手，只能转写图片中可见内容。",
        },
        {
            "role": "user",
            "content": content,
        },
    ]


def extract_pdf_text_with_vision_llm(
    file_path: str | Path,
    *,
    config: LLMConfig | None = None,
    client: ChatCompletionClient | None = None,
    max_pages: int | None = None,
) -> LLMEnhancementResult:
    llm_config = config or load_llm_config_from_env()
    if llm_config is None:
        return LLMEnhancementResult(
            enabled=False,
            content="",
            provider_message="Vision LLM 未启用或配置不完整。",
        )

    page_limit = max_pages or int(os.getenv("HR_LLM_PDF_MAX_PAGES", "3"))
    chat_client = client or OpenAICompatibleChatClient()
    try:
        data_urls = render_pdf_pages_as_data_urls(file_path, max_pages=page_limit)
        content = chat_client.complete(
            messages=build_pdf_vision_messages(data_urls),
            config=llm_config,
        )
    except Exception as exc:
        return LLMEnhancementResult(
            enabled=True,
            content="",
            provider_message=f"Vision LLM PDF 解析失败：{exc}",
        )

    return LLMEnhancementResult(
        enabled=True,
        content=content,
        provider_message="Vision LLM PDF 解析已生成。",
    )
