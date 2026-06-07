from __future__ import annotations

from core.schemas import MatchBreakdown
from core.state import WorkflowState
from harness.trace import add_trace


def _weighted_score(dimension_scores: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights.values())
    if total_weight <= 0:
        return 0.0
    weighted_total = sum(dimension_scores.get(name, 0.0) * weight for name, weight in weights.items())
    return round(weighted_total / total_weight, 2)


def _skill_score(candidate: dict, job: dict) -> tuple[float, list[str]]:
    candidate_skills = set(candidate.get("skills", []))
    required_skills = set(job.get("required_skills", []))
    matched_skills = sorted(candidate_skills & required_skills)
    score = round(len(matched_skills) / max(len(required_skills), 1) * 100, 2)
    return score, matched_skills


def _experience_score(candidate: dict, job: dict) -> float:
    required_years = job.get("required_years", 0)
    years = candidate.get("years_experience", 0)
    if required_years == 0:
        return 100.0
    return round(min(years / required_years, 1.0) * 100, 2)


def _evidence_notes(candidate: dict, matched_skills: list[str]) -> list[str]:
    strength_labels = {
        "strong": "强",
        "medium": "中",
        "weak": "弱",
        "unsupported": "未支持",
    }
    evidence_by_skill = {
        item.get("skill", "").lower(): item
        for item in candidate.get("skill_evidence", [])
    }
    notes: list[str] = []
    for skill in matched_skills:
        evidence = evidence_by_skill.get(skill.lower())
        if not evidence:
            notes.append(f"{skill}: 仅在技能列表中出现，暂未找到项目证据。")
            continue
        strength = strength_labels.get(evidence.get("evidence_strength"), "未知")
        notes.append(f"{skill}: 简历中存在{strength}证据。")
    return notes


def _dimension_scores(
    track: str,
    candidate: dict,
    job: dict,
    skill_score: float,
    experience_score: float,
) -> dict[str, float]:
    has_projects = bool(candidate.get("campus_projects") or candidate.get("work_experiences"))
    has_internships = bool(candidate.get("internships"))
    has_evidence = bool(candidate.get("skill_evidence"))

    if track == "campus":
        project_score = 85.0 if has_projects or has_internships else 45.0
        return {
            "education_major_match": 75.0 if candidate.get("education") else 40.0,
            "project_internship": project_score,
            "skill_foundation": skill_score,
            "learning_evidence": 70.0 if has_projects else 50.0,
            "portfolio_research": 60.0 if has_projects else 35.0,
            "motivation_stability": 65.0,
        }

    if track == "experienced":
        project_depth = 85.0 if candidate.get("work_experiences") else 60.0
        return {
            "skill_match": skill_score,
            "years_experience": experience_score,
            "project_depth": project_depth,
            "business_impact": 70.0 if has_evidence else 50.0,
            "domain_match": 70.0,
            "salary_stability": 75.0,
        }

    if track == "intern":
        return {
            "skill_foundation": skill_score,
            "project_practice": 80.0 if has_projects else 45.0,
            "learning_evidence": 70.0 if has_projects else 55.0,
            "communication_execution": 60.0,
            "availability_match": 65.0,
        }

    return {
        "skill_match": skill_score,
        "project_or_experience": 75.0 if has_projects else 45.0,
        "education_or_foundation": 65.0,
        "risk_review": 50.0,
    }


def matcher_node(state: WorkflowState) -> WorkflowState:
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    scoring_rubric = state.get("scoring_rubric") or {}
    weights = scoring_rubric.get("weights", {})
    track = scoring_rubric.get("track", candidate.get("candidate_track", "unknown"))

    skill_score, matched_skills = _skill_score(candidate, job)
    experience_score = _experience_score(candidate, job)
    dimension_scores = _dimension_scores(track, candidate, job, skill_score, experience_score)
    match_score = _weighted_score(dimension_scores, weights)

    match_breakdown = MatchBreakdown(
        skill_score=skill_score,
        experience_score=experience_score,
        matched_skills=matched_skills,
        track=track,
        rubric_weights=weights,
        dimension_scores=dimension_scores,
        evidence_notes=_evidence_notes(candidate, matched_skills),
    ).model_dump()

    return {
        "match_score": match_score,
        "match_breakdown": match_breakdown,
        "current_step": "matcher",
        "trace": add_trace(
            state,
            "matcher",
            f"Calculated match score: {match_score}.",
            match_breakdown,
        ),
    }
