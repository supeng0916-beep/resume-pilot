from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DocumentMeta(StrictBaseModel):
    file_name: str | None = None
    page_count: int = Field(ge=0)
    parser: str = Field(min_length=1)
    needs_ocr: bool = False
    text_length: int = Field(ge=0)


class CandidateProfile(StrictBaseModel):
    name: str = Field(min_length=1)
    education: str = Field(min_length=1)
    years_experience: int = Field(ge=0, le=60)
    skills: list[str] = Field(min_length=1)
    expected_salary: str = Field(min_length=1)
    current_status: str | None = None

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
