from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import (
    CandidateProfile,
    DocumentMeta,
    EvidenceSpan,
    JobProfile,
    MatchBreakdown,
    ScoringRubric,
    SkillEvidence,
)


def test_candidate_profile_accepts_valid_data() -> None:
    profile = CandidateProfile(
        name="张三",
        education="本科",
        years_experience=5,
        skills=["Python", " FastAPI "],
        expected_salary="30k CNY/month",
        current_status="在职",
    )

    assert profile.skills == ["Python", "FastAPI"]


def test_candidate_profile_rejects_invalid_experience_type() -> None:
    with pytest.raises(ValidationError):
        CandidateProfile(
            name="张三",
            education="本科",
            years_experience="five",
            skills=["Python"],
            expected_salary="30k CNY/month",
        )


def test_job_profile_requires_skills() -> None:
    with pytest.raises(ValidationError):
        JobProfile(
            title="高级 Python 后端工程师",
            required_years=3,
            required_skills=[],
        )


def test_document_meta_tracks_ocr_need() -> None:
    meta = DocumentMeta(
        file_name="resume.pdf",
        page_count=2,
        parser="mock",
        needs_ocr=False,
        text_length=1200,
    )

    assert meta.needs_ocr is False
    assert meta.parse_quality_score == 0.0
    assert meta.parse_quality_flags == []


def test_match_breakdown_score_bounds() -> None:
    with pytest.raises(ValidationError):
        MatchBreakdown(
            skill_score=120,
            experience_score=100,
            matched_skills=["Python"],
        )


def test_candidate_profile_supports_campus_track_without_work_experience() -> None:
    profile = CandidateProfile(
        name="李四",
        education="本科",
        years_experience=0,
        skills=["Python", "SQL"],
        expected_salary="面议",
        candidate_track="campus",
        track_confidence=0.9,
        track_reason="无正式工作经历，主要包含校园项目和实习经历",
        graduation_year=2026,
        campus_projects=["校园二手交易平台"],
    )

    assert profile.candidate_track == "campus"
    assert profile.work_experiences == []
    assert profile.campus_projects == ["校园二手交易平台"]


def test_skill_evidence_tracks_source_snippet() -> None:
    evidence = SkillEvidence(
        skill="Redis",
        evidence_strength="strong",
        evidence=[
            EvidenceSpan(
                source="resume",
                section="project_experience",
                text="使用 Redis 缓存热点数据，并通过 TTL 策略降低数据库压力。",
                page=1,
                confidence=0.88,
            )
        ],
    )

    assert evidence.evidence_strength == "strong"
    assert evidence.evidence[0].source == "resume"


def test_scoring_rubric_rejects_zero_total_weight() -> None:
    with pytest.raises(ValidationError):
        ScoringRubric(
            track="experienced",
            weights={"skill_match": 0, "project_depth": 0},
            rationale="invalid zero-weight rubric",
        )


def test_scoring_rubric_accepts_experienced_track_weights() -> None:
    rubric = ScoringRubric(
        track="experienced",
        weights={
            "skill_match": 0.3,
            "years_experience": 0.15,
            "project_depth": 0.25,
            "business_impact": 0.15,
            "domain_match": 0.1,
            "salary_stability": 0.05,
        },
        rationale="社招更关注技能匹配、项目复杂度和业务成果。",
    )

    assert rubric.track == "experienced"
    assert rubric.weights["project_depth"] == 0.25
