from __future__ import annotations

from core.schemas import CandidateProfile, EvidenceSpan, SkillEvidence
from core.state import WorkflowState
from harness.trace import add_trace


def resume_extractor_node(state: WorkflowState) -> WorkflowState:
    retry_count = state.get("retry_count", 0)
    should_force_invalid = state.get("force_invalid_candidate_always") or (
        state.get("force_invalid_candidate_once") and retry_count == 0
    )

    if should_force_invalid:
        candidate_profile = {
            "name": "张三",
            "education": "本科",
            "years_experience": "five",
            "skills": ["Python", "FastAPI"],
            "expected_salary": "30k CNY/month",
            "current_status": "在职",
        }
        return {
            "candidate_profile": candidate_profile,
            "current_step": "resume_extractor",
            "trace": add_trace(
                state,
                "resume_extractor",
                "Extracted intentionally invalid mock candidate profile.",
            ),
        }

    candidate_profile = CandidateProfile(
        name="张三",
        education="本科",
        years_experience=5,
        skills=["Python", "FastAPI", "PostgreSQL", "Redis", "LLM 应用"],
        expected_salary="30k CNY/month",
        current_status="在职",
        work_experiences=["5 年 Python 后端开发经验，参与过 LLM 应用和数据平台项目。"],
        skill_evidence=[
            SkillEvidence(
                skill="FastAPI",
                evidence_strength="strong",
                evidence=[
                    EvidenceSpan(
                        source="resume",
                        section="project_experience",
                        text="参与过 LLM 应用项目，负责 Python/FastAPI 后端接口开发。",
                        page=1,
                        confidence=0.85,
                    )
                ],
            ),
            SkillEvidence(
                skill="Redis",
                evidence_strength="medium",
                evidence=[
                    EvidenceSpan(
                        source="resume",
                        section="work_experience",
                        text="熟悉 Redis，并在数据平台项目中参与缓存相关开发。",
                        page=1,
                        confidence=0.72,
                    )
                ],
            ),
        ],
    ).model_dump()
    return {
        "candidate_profile": candidate_profile,
        "current_step": "resume_extractor",
        "trace": add_trace(
            state,
            "resume_extractor",
            "Re-extracted corrected mock candidate profile."
            if retry_count
            else "Extracted mock candidate profile.",
        ),
    }
