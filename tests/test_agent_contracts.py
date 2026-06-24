from __future__ import annotations

from core.agent_contracts import AgentResult, TokenUsage, record_agent_result


def test_record_agent_result_updates_agent_outputs_and_metrics() -> None:
    state = {
        "agent_outputs": {},
        "agent_metrics": {},
    }
    result = AgentResult(
        agent_name="candidate_analyst",
        role="candidate_profile_review",
        status="success",
        findings={"strengths": ["Python"]},
        evidence_refs=[],
        confidence=0.82,
        concerns=[],
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        duration_ms=123,
    )

    updates = record_agent_result(state, result)

    assert updates["agent_outputs"]["candidate_analyst"]["findings"] == {"strengths": ["Python"]}
    assert updates["agent_metrics"]["candidate_analyst"]["duration_ms"] == 123
    assert updates["agent_metrics"]["candidate_analyst"]["token_usage"]["total_tokens"] == 15


def test_agent_result_rejects_invalid_confidence() -> None:
    try:
        AgentResult(
            agent_name="risk_agent",
            role="risk_review",
            status="success",
            findings={},
            evidence_refs=[],
            confidence=1.5,
            concerns=[],
            duration_ms=1,
        )
    except ValueError as exc:
        assert "less than or equal to 1" in str(exc)
    else:
        raise AssertionError("AgentResult should reject confidence above 1")
