from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from core.llm_provider import (
    ChatCompletionClient,
    LLMConfig,
    OpenAICompatibleChatClient,
    load_llm_config_from_env,
)
from core.schemas import CandidateProfile, JobProfile


T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class LLMExtractionResult:
    enabled: bool
    profile: dict[str, Any] | None
    provider_message: str


def _json_schema_text(model: type[BaseModel]) -> str:
    return json.dumps(model.model_json_schema(), ensure_ascii=False)


def _extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        stripped = fenced.group(1).strip()

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end < start:
            raise ValueError("LLM response does not contain a JSON object")
        payload = json.loads(stripped[start : end + 1])

    if not isinstance(payload, dict):
        raise ValueError("LLM response JSON must be an object")
    return payload


def _validate_payload(payload: dict[str, Any], model: type[T]) -> dict[str, Any]:
    return model.model_validate(payload).model_dump()


def build_resume_extraction_messages(resume_text: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": (
                "你是严谨的招聘信息抽取助手。只根据简历原文抽取 CandidateProfile JSON，"
                "不要编造经历、项目、学历或技能。没有证据的字段使用 unknown、空数组或 null。"
                "candidate_track 只能是 campus、experienced、intern、unknown。"
                "skill_evidence 中的证据片段必须来自简历原文。只输出 JSON，不要输出解释。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "schema": _json_schema_text(CandidateProfile),
                    "resume_text": resume_text[:12000],
                },
                ensure_ascii=False,
            ),
        },
    ]


def build_jd_extraction_messages(jd_text: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": (
                "你是严谨的岗位 JD 抽取助手。只根据 JD 原文抽取 JobProfile JSON。"
                "required_skills 只放明确要求或强相关技能，nice_to_have 放加分项。"
                "recruitment_track 只能是 campus、experienced、intern、unknown。"
                "只输出 JSON，不要输出解释。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "schema": _json_schema_text(JobProfile),
                    "jd_text": jd_text[:12000],
                },
                ensure_ascii=False,
            ),
        },
    ]


def _extract_with_llm(
    *,
    messages: list[dict[str, Any]],
    model: type[T],
    label: str,
    config: LLMConfig | None = None,
    client: ChatCompletionClient | None = None,
) -> LLMExtractionResult:
    llm_config = config or load_llm_config_from_env()
    if llm_config is None:
        return LLMExtractionResult(
            enabled=False,
            profile=None,
            provider_message=f"{label} LLM 抽取未启用或配置不完整。",
        )

    chat_client = client or OpenAICompatibleChatClient()
    try:
        content = chat_client.complete(messages=messages, config=llm_config)
        payload = _extract_json_object(content)
        profile = _validate_payload(payload, model)
    except Exception as exc:
        return LLMExtractionResult(
            enabled=True,
            profile=None,
            provider_message=f"{label} LLM 抽取失败，已回退规则抽取：{exc}",
        )

    return LLMExtractionResult(
        enabled=True,
        profile=profile,
        provider_message=f"{label} LLM 结构化抽取成功。",
    )


def extract_resume_profile_with_llm(
    resume_text: str,
    *,
    config: LLMConfig | None = None,
    client: ChatCompletionClient | None = None,
) -> LLMExtractionResult:
    return _extract_with_llm(
        messages=build_resume_extraction_messages(resume_text),
        model=CandidateProfile,
        label="简历",
        config=config,
        client=client,
    )


def extract_job_profile_with_llm(
    jd_text: str,
    *,
    config: LLMConfig | None = None,
    client: ChatCompletionClient | None = None,
) -> LLMExtractionResult:
    return _extract_with_llm(
        messages=build_jd_extraction_messages(jd_text),
        model=JobProfile,
        label="JD",
        config=config,
        client=client,
    )
