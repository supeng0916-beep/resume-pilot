from __future__ import annotations

import re

from core.schemas import CandidateProfile, EvidenceSpan, SkillEvidence
from core.skills import SKILL_ALIASES, extract_known_skills


EDUCATION_LEVELS = ["博士", "硕士", "本科", "大专", "高中"]


def _extract_name(text: str) -> str:
    patterns = [
        r"(?:候选人|姓名)[:：]\s*([\u4e00-\u9fa5A-Za-z ]{2,30})",
        r"^([\u4e00-\u9fa5]{2,4})\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip(" 。,，")
    return "未知候选人"


def _extract_education(text: str) -> str:
    for level in EDUCATION_LEVELS:
        if level in text:
            return level
    return "未知"


def _extract_years_experience(text: str) -> int:
    patterns = [
        r"(\d+)\s*年(?:以上)?\s*(?:Python|后端|前端|工作|开发|经验)",
        r"(\d+)\s*年(?:以上)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 0


def _extract_expected_salary(text: str) -> str:
    match = re.search(r"期望薪资\s*[:：]?\s*([\d.]+\s*[kK]|[\d.]+\s*万)", text)
    if not match:
        return "unknown"
    value = match.group(1).replace(" ", "")
    if value.lower().endswith("k"):
        return f"{value.lower()} CNY/month"
    return f"{value} CNY/month"


def _extract_current_status(text: str) -> str | None:
    if "离职" in text:
        return "离职"
    if "在职" in text:
        return "在职"
    if "至今" in text and any(keyword in text for keyword in ["大学", "硕士", "本科"]):
        return "在读"
    if "应届" in text:
        return "应届"
    return None


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。；;\n]", text)
    return [part.strip() for part in parts if part.strip()]


def _extract_work_experiences(text: str) -> list[str]:
    sentences = _split_sentences(text)
    experiences = [
        sentence
        for sentence in sentences
        if any(keyword in sentence for keyword in ["工作经历", "工作经验", "开发经验", "任职", "全职"])
        and "实习" not in sentence
    ]
    return experiences[:5]


def _extract_internships(text: str) -> list[str]:
    sentences = _split_sentences(text)
    return [sentence for sentence in sentences if "实习" in sentence][:5]


def _extract_campus_projects(text: str) -> list[str]:
    sentences = _split_sentences(text)
    projects = [
        sentence
        for sentence in sentences
        if any(keyword in sentence for keyword in ["项目经历", "项目描述", "独立开发者", "校园项目"])
    ]
    return projects[:5]


def _extract_graduation_year(text: str) -> int | None:
    if "至今" in text and "硕士" in text:
        return None
    years = [int(year) for year in re.findall(r"(20\d{2})[-年]", text)]
    if not years:
        return None
    return max(years)


def _snippet_for_skill(text: str, skill: str) -> str:
    matched_alias = next(
        (alias for alias in SKILL_ALIASES.get(skill, [skill]) if alias.lower() in text.lower()),
        skill,
    )
    index = text.lower().find(matched_alias.lower())
    if index < 0:
        return ""
    start = max(index - 35, 0)
    end = min(index + len(matched_alias) + 45, len(text))
    return text[start:end].strip()


def _evidence_strength(snippet: str) -> str:
    if any(keyword in snippet for keyword in ["负责", "项目", "开发", "设计", "优化", "使用"]):
        return "strong"
    if any(keyword in snippet for keyword in ["熟悉", "掌握", "了解"]):
        return "medium"
    return "weak"


def _extract_skill_evidence(text: str, skills: list[str]) -> list[SkillEvidence]:
    evidence_items: list[SkillEvidence] = []
    for skill in skills:
        snippet = _snippet_for_skill(text, skill)
        if not snippet:
            evidence_items.append(SkillEvidence(skill=skill, evidence_strength="unsupported"))
            continue

        evidence_items.append(
            SkillEvidence(
                skill=skill,
                evidence_strength=_evidence_strength(snippet),
                evidence=[
                    EvidenceSpan(
                        source="resume",
                        section="resume_text",
                        text=snippet,
                        page=1,
                        confidence=0.65,
                    )
                ],
            )
        )
    return evidence_items


def parse_resume_text(text: str) -> CandidateProfile:
    skills = extract_known_skills(text)
    if not skills:
        skills = ["unknown"]

    return CandidateProfile(
        name=_extract_name(text),
        education=_extract_education(text),
        years_experience=_extract_years_experience(text),
        skills=skills,
        expected_salary=_extract_expected_salary(text),
        current_status=_extract_current_status(text),
        graduation_year=_extract_graduation_year(text),
        internships=_extract_internships(text),
        campus_projects=_extract_campus_projects(text),
        work_experiences=_extract_work_experiences(text),
        skill_evidence=_extract_skill_evidence(text, skills),
    )
