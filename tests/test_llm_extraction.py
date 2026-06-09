from __future__ import annotations

import json

from core.llm_extraction import (
    build_jd_extraction_messages,
    build_resume_extraction_messages,
    extract_job_profile_with_llm,
    extract_resume_profile_with_llm,
)
from core.llm_provider import LLMConfig


class ResumeExtractionClient:
    def complete(self, *, messages, config) -> str:
        assert config.model == "fake-model"
        assert messages[0]["role"] == "system"
        return json.dumps(
            {
                "name": "李明",
                "education": "本科",
                "years_experience": 0,
                "skills": ["Python", "PyTorch"],
                "expected_salary": "面议",
                "current_status": "应届",
                "candidate_track": "campus",
                "track_confidence": 0.8,
                "track_reason": "简历提到应届生和校园项目",
                "graduation_year": 2026,
                "major": "计算机科学",
                "internships": [],
                "campus_projects": ["使用 PyTorch 完成图像识别项目"],
                "work_experiences": [],
                "skill_evidence": [
                    {
                        "skill": "PyTorch",
                        "evidence_strength": "strong",
                        "evidence": [
                            {
                                "source": "resume",
                                "section": "项目经历",
                                "text": "使用 PyTorch 完成图像识别项目",
                                "page": 1,
                                "confidence": 0.9,
                            }
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )


class FencedJobExtractionClient:
    def complete(self, *, messages, config) -> str:
        payload = {
            "title": "校招 AI 工程师",
            "required_years": 0,
            "required_skills": ["Python", "PyTorch"],
            "nice_to_have": ["LLM 应用"],
            "salary_range": None,
            "recruitment_track": "campus",
        }
        return "```json\n" + json.dumps(payload, ensure_ascii=False) + "\n```"


class InvalidExtractionClient:
    def complete(self, *, messages, config) -> str:
        return "not json"


class TimeoutExtractionClient:
    def complete(self, *, messages, config) -> str:
        raise TimeoutError("read operation timed out")


def test_build_resume_extraction_messages_include_schema_and_text() -> None:
    messages = build_resume_extraction_messages("姓名：李明。项目经历：Python。")

    assert "CandidateProfile" in messages[1]["content"]
    assert "姓名：李明" in messages[1]["content"]


def test_build_jd_extraction_messages_include_schema_and_text() -> None:
    messages = build_jd_extraction_messages("校招 AI 工程师，要求 Python。")

    assert "JobProfile" in messages[1]["content"]
    assert "校招 AI 工程师" in messages[1]["content"]


def test_extract_resume_profile_with_llm_validates_candidate_schema() -> None:
    result = extract_resume_profile_with_llm(
        "姓名：李明。本科应届生，使用 PyTorch 完成图像识别项目。",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=ResumeExtractionClient(),
    )

    assert result.enabled is True
    assert result.profile is not None
    assert result.profile["candidate_track"] == "campus"
    assert result.profile["skill_evidence"][0]["evidence_strength"] == "strong"


def test_extract_job_profile_with_llm_accepts_fenced_json() -> None:
    result = extract_job_profile_with_llm(
        "校招 AI 工程师，要求 Python 和 PyTorch。",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=FencedJobExtractionClient(),
    )

    assert result.enabled is True
    assert result.profile is not None
    assert result.profile["required_skills"] == ["Python", "PyTorch"]


def test_extract_resume_profile_with_llm_returns_failure_without_profile() -> None:
    result = extract_resume_profile_with_llm(
        "姓名：李明。",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=InvalidExtractionClient(),
    )

    assert result.enabled is True
    assert result.profile is None
    assert "已回退规则抽取" in result.provider_message


def test_extract_resume_profile_with_llm_returns_failure_on_timeout() -> None:
    result = extract_resume_profile_with_llm(
        "候选人 Alice，Python FastAPI 项目。",
        config=LLMConfig(api_key="secret", model="fake-model"),
        client=TimeoutExtractionClient(),
    )

    assert result.enabled is True
    assert result.profile is None
    assert "已回退规则抽取" in result.provider_message
    assert "timed out" in result.provider_message
