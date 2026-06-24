from __future__ import annotations

from typing import Any


def analyze_candidate_profile_skill(candidate: dict[str, Any]) -> dict[str, Any]:
    skills = list(candidate.get("skills", []))
    experiences = list(candidate.get("work_experiences", []))
    projects = list(candidate.get("campus_projects", []))

    strengths: list[str] = []
    if skills:
        strengths.append(f"Primary skill stack includes {', '.join(skills[:4])}.")
    if experiences:
        strengths.append("Has prior work experience that can support behavioral interviewing.")
    if projects:
        strengths.append("Has project evidence available for technical deep-dive questions.")

    gaps: list[str] = []
    if not candidate.get("expected_salary"):
        gaps.append("Expected salary is missing and should be confirmed in review.")
    if not experiences and not projects:
        gaps.append("Limited concrete project/work evidence extracted from the resume.")

    return {
        "profile_focus": candidate.get("candidate_track", "unknown"),
        "strengths": strengths or ["Need richer candidate evidence before final recommendation."],
        "gaps": gaps,
    }


def analyze_job_profile_skill(job: dict[str, Any]) -> dict[str, Any]:
    required_skills = list(job.get("required_skills", []))
    preferred_skills = list(job.get("preferred_skills", []))
    title = job.get("title") or "unknown"

    priorities: list[str] = []
    if required_skills:
        priorities.append(f"Required skill focus: {', '.join(required_skills[:4])}.")
    if preferred_skills:
        priorities.append(f"Preferred differentiators: {', '.join(preferred_skills[:3])}.")

    return {
        "job_title": title,
        "priorities": priorities or ["Clarify hiring manager priorities before final decision."],
        "recruitment_track": job.get("recruitment_track", "unknown"),
    }
