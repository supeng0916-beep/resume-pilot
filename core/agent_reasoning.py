from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from core.model_gateway import (
    OpenAICompatibleModelGateway,
    ModelGatewayConfig,
    TokenUsage,
    chat_with_config,
)


class AgentReasoningPayload(BaseModel):
    findings: dict[str, Any] = Field(default_factory=dict)
    concerns: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class AgentReasoningResult:
    enabled: bool
    findings: dict[str, Any]
    concerns: list[str] = field(default_factory=list)
    provider_message: str = ""
    token_usage: TokenUsage | None = None
    model_name: str | None = None
    provider: str | None = None


def agent_llm_enabled() -> bool:
    return os.getenv("HR_AGENT_LLM_ENABLED", "false").lower() in {"1", "true", "yes"}


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


def _build_messages(
    *,
    agent_name: str,
    role: str,
    base_findings: dict[str, Any],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a production HR evaluation specialist agent. "
                "Use only the provided structured context. Do not invent experience, skills, employers, "
                "education, salary, or interview outcomes. Return strict JSON with keys: "
                "findings (object) and concerns (array of strings). Keep findings concise and evidence-bound."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "agent_name": agent_name,
                    "role": role,
                    "base_findings": base_findings,
                    "context": context,
                },
                ensure_ascii=False,
            ),
        },
    ]


def enrich_findings_with_llm(
    *,
    agent_name: str,
    role: str,
    base_findings: dict[str, Any],
    context: dict[str, Any],
    config: ModelGatewayConfig | None = None,
    gateway: OpenAICompatibleModelGateway | None = None,
) -> AgentReasoningResult:
    if not agent_llm_enabled():
        return AgentReasoningResult(
            enabled=False,
            findings=base_findings,
            provider_message="Agent LLM reasoning is disabled.",
        )

    try:
        response = chat_with_config(
            messages=_build_messages(
                agent_name=agent_name,
                role=role,
                base_findings=base_findings,
                context=context,
            ),
            config=config,
            gateway=gateway,
        )
        if response is None:
            return AgentReasoningResult(
                enabled=False,
                findings=base_findings,
                provider_message="Model gateway is not configured.",
            )
        payload = AgentReasoningPayload.model_validate(_extract_json_object(response.content))
    except (ValidationError, ValueError, RuntimeError) as exc:
        return AgentReasoningResult(
            enabled=True,
            findings=base_findings,
            provider_message=f"Agent LLM reasoning failed; used deterministic skill output: {exc}",
        )

    merged_findings = dict(base_findings)
    merged_findings.update(payload.findings)
    return AgentReasoningResult(
        enabled=True,
        findings=merged_findings,
        concerns=payload.concerns,
        provider_message="Agent LLM reasoning succeeded.",
        token_usage=response.token_usage,
        model_name=response.model,
        provider=response.provider,
    )
