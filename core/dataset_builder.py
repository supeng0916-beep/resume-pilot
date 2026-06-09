from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TRACKS = ("campus", "experienced", "intern")
MATCH_LABELS = ("strong_match", "partial_match", "weak_match")
EVIDENCE_QUALITIES = ("strong", "medium", "weak", "unsupported")


@dataclass(frozen=True)
class SyntheticDataset:
    candidates: list[dict[str, Any]]
    jobs: list[dict[str, Any]]
    labels: list[dict[str, Any]]


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            file.write("\n")
    return output_path


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    return [
        json.loads(line)
        for line in input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _build_jobs() -> list[dict[str, Any]]:
    return [
        {
            "jd_id": "jd_campus_ai",
            "title": "校招 AI 工程师",
            "track": "campus",
            "required_skills": ["Python", "机器学习", "SQL"],
            "bonus_skills": ["PyTorch", "LangChain"],
            "required_years": 0,
            "salary_min_k": 15,
            "salary_max_k": 25,
        },
        {
            "jd_id": "jd_backend_experienced",
            "title": "社招后端工程师",
            "track": "experienced",
            "required_skills": ["Python", "FastAPI", "Redis", "PostgreSQL"],
            "bonus_skills": ["Docker", "Kubernetes"],
            "required_years": 3,
            "salary_min_k": 25,
            "salary_max_k": 40,
        },
        {
            "jd_id": "jd_data_intern",
            "title": "数据分析实习生",
            "track": "intern",
            "required_skills": ["SQL", "Python", "Excel"],
            "bonus_skills": ["Tableau", "统计学"],
            "required_years": 0,
            "salary_min_k": 3,
            "salary_max_k": 8,
        },
    ]


def _candidate_for_job(index: int, job: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    required_skills = list(job["required_skills"])
    bonus_skills = list(job["bonus_skills"])
    skill_pool = [*required_skills, *bonus_skills, "Git", "Linux", "数据结构", "沟通协作"]
    matched_count = rng.randint(1, len(required_skills))
    skills = sorted(set(rng.sample(required_skills, matched_count) + rng.sample(skill_pool, rng.randint(1, 3))))
    years = max(0, int(rng.gauss(job["required_years"], 1.5)))
    if job["track"] == "campus":
        years = rng.choice([0, 0, 1])
    if job["track"] == "intern":
        years = 0

    project_skill = rng.choice(skills)
    evidence_quality = rng.choices(EVIDENCE_QUALITIES, weights=[4, 3, 2, 1], k=1)[0]
    parse_quality = round(rng.uniform(0.55, 0.99), 2)
    expected_salary = rng.randint(max(1, job["salary_min_k"] - 5), job["salary_max_k"] + 10)

    return {
        "candidate_id": f"cand_{index:04d}",
        "resume_id": f"resume_{index:04d}",
        "name": f"脱敏候选人{index:04d}",
        "track": job["track"] if rng.random() > 0.12 else "unknown",
        "education": rng.choice(["本科", "硕士", "大专"]),
        "major": rng.choice(["计算机科学与技术", "软件工程", "人工智能", "统计学", "信息管理"]),
        "years_experience": years,
        "skills": skills,
        "projects": [
            {
                "name": f"{job['title']}相关项目",
                "skills_used": [project_skill],
                "evidence_strength": evidence_quality,
                "description": f"在项目中使用 {project_skill} 完成核心模块。",
            }
        ],
        "expected_salary_k": expected_salary,
        "parse_quality_score": parse_quality,
    }


def _label_for(candidate: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    required = set(job["required_skills"])
    skills = set(candidate["skills"])
    coverage = len(required & skills) / max(len(required), 1)
    evidence_quality = candidate["projects"][0]["evidence_strength"]

    if coverage >= 0.75 and evidence_quality in {"strong", "medium"}:
        match_label = "strong_match"
    elif coverage >= 0.4:
        match_label = "partial_match"
    else:
        match_label = "weak_match"

    risk_labels: list[str] = []
    if candidate["parse_quality_score"] < 0.7:
        risk_labels.append("parse_low_quality")
    if candidate["expected_salary_k"] >= job["salary_max_k"] * 0.9:
        risk_labels.append("salary_pressure")
    if candidate["years_experience"] < job["required_years"]:
        risk_labels.append("experience_gap")
    if evidence_quality in {"weak", "unsupported"}:
        risk_labels.append("evidence_gap")
    if candidate["track"] == "unknown":
        risk_labels.append("track_unknown")

    return {
        "sample_id": f"case_{candidate['candidate_id'].split('_')[-1]}",
        "candidate_id": candidate["candidate_id"],
        "resume_id": candidate["resume_id"],
        "jd_id": job["jd_id"],
        "match_label": match_label,
        "needs_human_review": bool(risk_labels) or match_label == "weak_match",
        "risk_labels": risk_labels,
        "evidence_quality": evidence_quality,
        "label_reason": _label_reason(match_label, risk_labels),
    }


def _label_reason(match_label: str, risk_labels: list[str]) -> str:
    if risk_labels:
        return f"{match_label}，需关注：{', '.join(risk_labels)}"
    return f"{match_label}，核心技能和项目证据较完整。"


def generate_synthetic_dataset(*, count: int = 50, seed: int = 42) -> SyntheticDataset:
    rng = random.Random(seed)
    jobs = _build_jobs()
    candidates: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        job = jobs[(index - 1) % len(jobs)]
        candidate = _candidate_for_job(index, job, rng)
        candidates.append(candidate)
        labels.append(_label_for(candidate, job))
    return SyntheticDataset(candidates=candidates, jobs=jobs, labels=labels)


def append_annotation_record(
    path: str | Path,
    *,
    sample_id: str,
    resume_id: str,
    jd_id: str,
    corrected_candidate_profile: dict[str, Any],
    corrected_job_profile: dict[str, Any],
    labels: dict[str, Any],
    annotator: str,
    notes: str = "",
) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "sample_id": sample_id,
        "resume_id": resume_id,
        "jd_id": jd_id,
        "corrected_candidate_profile": corrected_candidate_profile,
        "corrected_job_profile": corrected_job_profile,
        "labels": labels,
        "annotation": {
            "annotator": annotator,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        file.write("\n")
    return record
