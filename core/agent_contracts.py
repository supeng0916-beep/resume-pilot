from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from core.model_gateway import TokenUsage
from core.schemas import EvidenceSpan
from core.state import WorkflowState


AgentStatus = Literal["success", "failed", "skipped"]


class AgentResult(BaseModel):
    agent_name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    status: AgentStatus
    findings: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    concerns: list[str] = Field(default_factory=list)
    token_usage: TokenUsage | None = None
    duration_ms: int = Field(default=0, ge=0)
    model_name: str | None = None
    provider: str | None = None


def record_agent_result(state: WorkflowState, result: AgentResult) -> WorkflowState:
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_metrics = dict(state.get("agent_metrics") or {})

    payload = result.model_dump()
    payload.update(result.findings)
    agent_outputs[result.agent_name] = payload
    agent_metrics[result.agent_name] = {
        "status": result.status,
        "confidence": result.confidence,
        "duration_ms": result.duration_ms,
        "token_usage": result.token_usage.model_dump() if result.token_usage else None,
        "model_name": result.model_name,
        "provider": result.provider,
    }
    return {
        "agent_outputs": agent_outputs,
        "agent_metrics": agent_metrics,
    }
