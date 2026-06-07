from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RecruitmentTrack = Literal["campus", "experienced", "intern", "unknown"]
EvidenceStrength = Literal["weak", "medium", "strong", "unsupported"]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DocumentMeta(StrictBaseModel):
    file_name: str | None = None
    page_count: int = Field(ge=0)
    parser: str = Field(min_length=1)
    needs_ocr: bool = False
    text_length: int = Field(ge=0)


class EvidenceSpan(StrictBaseModel):
    source: Literal["resume", "jd", "human_feedback", "memory"]
    section: str = Field(min_length=1)
    text: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    confidence: float = Field(default=1.0, ge=0, le=1)


class SkillEvidence(StrictBaseModel):
    skill: str = Field(min_length=1)
    evidence_strength: EvidenceStrength = "unsupported"
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class ScoringRubric(StrictBaseModel):
    track: RecruitmentTrack
    weights: dict[str, float] = Field(min_length=1)
    rationale: str = Field(min_length=1)

    @field_validator("weights")
    @classmethod
    def weights_must_be_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        negative_dimensions = [name for name, weight in value.items() if weight < 0]
        if negative_dimensions:
            raise ValueError(f"weights must be non-negative: {negative_dimensions}")
        return value

    @model_validator(mode="after")
    def weights_must_have_positive_total(self) -> "ScoringRubric":
        if sum(self.weights.values()) <= 0:
            raise ValueError("weights must have a positive total")
        return self


class CandidateProfile(StrictBaseModel):
    name: str = Field(min_length=1)
    education: str = Field(min_length=1)
    years_experience: int = Field(ge=0, le=60)
    skills: list[str] = Field(min_length=1)
    expected_salary: str = Field(min_length=1)
    current_status: str | None = None
    candidate_track: RecruitmentTrack = "unknown"
    track_confidence: float = Field(default=0.0, ge=0, le=1)
    track_reason: str | None = None
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    major: str | None = None
    internships: list[str] = Field(default_factory=list)
    campus_projects: list[str] = Field(default_factory=list)
    work_experiences: list[str] = Field(default_factory=list)
    skill_evidence: list[SkillEvidence] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def skills_must_not_contain_empty_values(cls, value: list[str]) -> list[str]:
        cleaned = [skill.strip() for skill in value if skill.strip()]
        if not cleaned:
            raise ValueError("skills must contain at least one non-empty skill")
        return cleaned


class JobProfile(StrictBaseModel):
    title: str = Field(min_length=1)
    required_years: int = Field(ge=0, le=60)
    required_skills: list[str] = Field(min_length=1)
    nice_to_have: list[str] = Field(default_factory=list)
    salary_range: str | None = None
    recruitment_track: RecruitmentTrack = "unknown"

    @field_validator("required_skills", "nice_to_have")
    @classmethod
    def skill_lists_must_be_clean(cls, value: list[str]) -> list[str]:
        return [skill.strip() for skill in value if skill.strip()]


class MatchBreakdown(StrictBaseModel):
    skill_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)


class EvaluationReport(StrictBaseModel):
    recommendation: Literal["advance", "reject", "revise", "need_more_info"]
    summary: str = Field(min_length=1)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_interview_questions: list[str] = Field(default_factory=list)
