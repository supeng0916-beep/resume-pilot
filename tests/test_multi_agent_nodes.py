from __future__ import annotations

from nodes.critic_agent import critic_agent_node
from nodes.evidence_auditor import evidence_auditor_node


def test_evidence_auditor_flags_matched_skills_without_resume_evidence() -> None:
    result = evidence_auditor_node(
        {
            "candidate_profile": {
                "skills": ["Python", "Redis"],
                "skill_evidence": [
                    {
                        "skill": "Python",
                        "evidence_strength": "strong",
                        "evidence": [],
                    }
                ],
            },
            "match_breakdown": {"matched_skills": ["Python", "Redis"]},
            "agent_outputs": {},
            "agent_metrics": {},
            "trace": [],
        }
    )

    audit = result["agent_outputs"]["evidence_auditor"]

    assert audit["findings"]["supported_skills"] == ["Python"]
    assert audit["findings"]["unsupported_skills"] == ["Redis"]
    assert audit["confidence"] == 0.5


def test_critic_agent_detects_high_score_with_evidence_gaps() -> None:
    result = critic_agent_node(
        {
            "match_score": 86.0,
            "risk_score": 0.2,
            "agent_outputs": {
                "evidence_auditor": {
                    "findings": {"unsupported_skills": ["Redis"]},
                    "concerns": ["Redis lacks direct evidence."],
                    "confidence": 0.5,
                }
            },
            "agent_metrics": {},
            "trace": [],
        }
    )

    critic = result["agent_outputs"]["critic_agent"]

    assert "High match score depends on skills with weak evidence." in critic["findings"]["conflicts"]
    assert critic["status"] == "success"
    assert critic["confidence"] == 0.65
