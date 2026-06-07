from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import CandidateProfile, DocumentMeta, JobProfile, MatchBreakdown


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


def test_match_breakdown_score_bounds() -> None:
    with pytest.raises(ValidationError):
        MatchBreakdown(
            skill_score=120,
            experience_score=100,
            matched_skills=["Python"],
        )
