from __future__ import annotations

from core.schemas import CandidateProfile, JobProfile, RecruitmentTrack, ScoringRubric


DEFAULT_RUBRICS: dict[RecruitmentTrack, ScoringRubric] = {
    "campus": ScoringRubric(
        track="campus",
        weights={
            "education_major_match": 0.20,
            "project_internship": 0.25,
            "skill_foundation": 0.20,
            "learning_evidence": 0.15,
            "portfolio_research": 0.10,
            "motivation_stability": 0.10,
        },
        rationale="校招更关注专业基础、项目/实习经历、学习能力和潜力证据。",
    ),
    "experienced": ScoringRubric(
        track="experienced",
        weights={
            "skill_match": 0.30,
            "years_experience": 0.15,
            "project_depth": 0.25,
            "business_impact": 0.15,
            "domain_match": 0.10,
            "salary_stability": 0.05,
        },
        rationale="社招更关注技能匹配、相关年限、项目复杂度、职责深度和业务成果。",
    ),
    "intern": ScoringRubric(
        track="intern",
        weights={
            "skill_foundation": 0.25,
            "project_practice": 0.25,
            "learning_evidence": 0.20,
            "communication_execution": 0.15,
            "availability_match": 0.15,
        },
        rationale="实习更关注基础能力、项目实践、学习能力、执行潜力和时间匹配。",
    ),
    "unknown": ScoringRubric(
        track="unknown",
        weights={
            "skill_match": 0.30,
            "project_or_experience": 0.30,
            "education_or_foundation": 0.20,
            "risk_review": 0.20,
        },
        rationale="候选人轨道不明确时使用保守混合权重，并提示人工确认。",
    ),
}


def infer_candidate_track(
    candidate: CandidateProfile,
    job: JobProfile,
) -> tuple[RecruitmentTrack, float, str]:
    if job.recruitment_track != "unknown":
        return job.recruitment_track, 0.95, "岗位 JD 明确指定招聘轨道。"

    if candidate.candidate_track != "unknown":
        return candidate.candidate_track, candidate.track_confidence or 0.80, (
            candidate.track_reason or "候选人信息中已给出招聘轨道。"
        )

    if candidate.years_experience >= 1 or candidate.work_experiences:
        return "experienced", 0.85, "候选人具备正式工作年限或工作经历。"

    if candidate.internships or candidate.campus_projects or candidate.graduation_year:
        return "campus", 0.75, "候选人缺少正式工作经历，主要证据来自校园项目、实习或毕业信息。"

    return "unknown", 0.40, "候选人轨道无法可靠判断，需要人工确认。"


def select_scoring_rubric(track: RecruitmentTrack) -> ScoringRubric:
    return DEFAULT_RUBRICS[track]
