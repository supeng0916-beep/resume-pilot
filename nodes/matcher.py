from __future__ import annotations

from core.state import WorkflowState
from harness.trace import add_trace


def matcher_node(state: WorkflowState) -> WorkflowState:
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    candidate_skills = set(candidate.get("skills", []))
    required_skills = set(job.get("required_skills", []))

    matched_skills = sorted(candidate_skills & required_skills)
    skill_score = len(matched_skills) / max(len(required_skills), 1)
    experience_score = 1.0 if candidate.get("years_experience", 0) >= job.get("required_years", 0) else 0.5
    match_score = round((skill_score * 0.7 + experience_score * 0.3) * 100, 2)

    match_breakdown = {
        "skill_score": round(skill_score * 100, 2),
        "experience_score": round(experience_score * 100, 2),
        "matched_skills": matched_skills,
    }

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
