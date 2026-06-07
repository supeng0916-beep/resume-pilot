from __future__ import annotations

from core.rubrics import infer_candidate_track, select_scoring_rubric
from core.schemas import CandidateProfile, JobProfile


def test_infer_experienced_track_from_work_years() -> None:
    candidate = CandidateProfile(
        name="王五",
        education="大专",
        years_experience=6,
        skills=["Python", "Redis"],
        expected_salary="28k CNY/month",
    )
    job = JobProfile(
        title="后端工程师",
        required_years=3,
        required_skills=["Python"],
    )

    track, confidence, reason = infer_candidate_track(candidate, job)

    assert track == "experienced"
    assert confidence >= 0.8
    assert "工作" in reason


def test_infer_campus_track_from_graduation_and_projects() -> None:
    candidate = CandidateProfile(
        name="赵六",
        education="本科",
        years_experience=0,
        skills=["Python", "SQL"],
        expected_salary="面议",
        graduation_year=2026,
        campus_projects=["校园二手交易平台"],
    )
    job = JobProfile(
        title="校招后端工程师",
        required_years=0,
        required_skills=["Python"],
    )

    track, confidence, reason = infer_candidate_track(candidate, job)

    assert track == "campus"
    assert confidence >= 0.7
    assert "校园项目" in reason


def test_job_recruitment_track_overrides_candidate_inference() -> None:
    candidate = CandidateProfile(
        name="孙七",
        education="本科",
        years_experience=3,
        skills=["Python"],
        expected_salary="25k CNY/month",
    )
    job = JobProfile(
        title="实习后端工程师",
        required_years=0,
        required_skills=["Python"],
        recruitment_track="intern",
    )

    track, confidence, reason = infer_candidate_track(candidate, job)

    assert track == "intern"
    assert confidence == 0.95
    assert "JD" in reason


def test_select_scoring_rubric_returns_track_specific_weights() -> None:
    rubric = select_scoring_rubric("experienced")

    assert rubric.track == "experienced"
    assert rubric.weights["project_depth"] > rubric.weights["salary_stability"]
