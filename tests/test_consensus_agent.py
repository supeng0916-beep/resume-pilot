from __future__ import annotations

from nodes.consensus_agent import consensus_agent_node


def test_consensus_agent_summarizes_multi_agent_outputs_and_conflicts() -> None:
    result = consensus_agent_node(
        {
            "agent_outputs": {
                "candidate_analyst": {
                    "status": "success",
                    "confidence": 0.8,
                    "findings": {"strengths": ["Python", "FastAPI"], "gaps": []},
                    "concerns": [],
                },
                "evidence_auditor": {
                    "status": "success",
                    "confidence": 0.55,
                    "findings": {"unsupported_skills": ["Redis"]},
                    "concerns": ["Redis lacks direct evidence."],
                },
                "critic_agent": {
                    "status": "success",
                    "confidence": 0.7,
                    "findings": {"conflicts": ["Skill Redis is matched but weakly evidenced."]},
                    "concerns": ["Manual review should verify Redis depth."],
                },
            },
            "match_score": 78.0,
            "risk_score": 0.42,
            "trace": [],
        }
    )

    recommendation = result["final_recommendation"]

    assert recommendation["recommendation"] == "need_more_info"
    assert recommendation["consensus_confidence"] == 0.68
    assert "Skill Redis is matched but weakly evidenced." in recommendation["conflicts"]
    assert "Manual review should verify Redis depth." in recommendation["open_concerns"]
