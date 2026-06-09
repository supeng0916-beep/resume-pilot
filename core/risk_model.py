from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from core.state import WorkflowState


DEFAULT_RISK_MODEL_PATH = "models/risk_model.json"


def extract_salary_number(value: str | None) -> float | None:
    if not value or value == "unknown":
        return None
    match = re.search(r"([\d.]+)\s*(k|K|万)?", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "万":
        return number * 10
    return number


def extract_salary_range(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    match = re.search(r"([\d.]+)\s*k?\s*-\s*([\d.]+)\s*k?", value, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def extract_risk_features(state: WorkflowState) -> dict[str, float]:
    match_score = float(state.get("match_score") or 0)
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}

    expected_salary = extract_salary_number(candidate.get("expected_salary"))
    salary_range = extract_salary_range(job.get("salary_range"))
    salary_unknown = 1.0 if expected_salary is None else 0.0
    salary_pressure = 0.0
    if expected_salary is not None and salary_range is not None:
        _, upper = salary_range
        if upper > 0:
            salary_pressure = max(0.0, min(1.0, (expected_salary - upper * 0.9) / (upper * 0.3)))

    years_experience = float(candidate.get("years_experience") or 0)
    required_years = float(job.get("required_years") or 0)
    experience_gap = 0.0
    if required_years > 0:
        experience_gap = max(0.0, min(1.0, (required_years - years_experience) / required_years))

    evidence_notes = match_breakdown.get("evidence_notes", [])
    matched_skills = match_breakdown.get("matched_skills", [])
    evidence_gap = 0.0
    if matched_skills:
        weak_notes = [note for note in evidence_notes if "暂未找到项目证据" in note or "unsupported" in note]
        evidence_gap = min(1.0, len(weak_notes) / len(matched_skills))

    return {
        "match_gap": max(0.0, min(1.0, (100.0 - match_score) / 100.0)),
        "salary_unknown": salary_unknown,
        "salary_pressure": salary_pressure,
        "experience_gap": experience_gap,
        "evidence_gap": evidence_gap,
        "track_unknown": 1.0 if candidate.get("candidate_track", "unknown") == "unknown" else 0.0,
    }


def load_risk_model(path: str | Path) -> dict[str, Any] | None:
    model_path = Path(path)
    if not model_path.exists():
        return None
    model = json.loads(model_path.read_text(encoding="utf-8"))
    if model.get("model_type") not in {"logistic_risk_v1", "review_risk_logistic_v1"}:
        raise ValueError(f"unsupported risk model type: {model.get('model_type')}")
    return model


def predict_risk_score(model: dict[str, Any], features: dict[str, float]) -> float:
    weights = model.get("weights", {})
    feature_order = model.get("feature_order", list(weights.keys()))
    logit = float(model.get("bias", 0.0))
    for feature_name in feature_order:
        logit += float(weights.get(feature_name, 0.0)) * float(features.get(feature_name, 0.0))
    return round(1.0 / (1.0 + math.exp(-logit)), 2)


def build_model_risk_factors(features: dict[str, float]) -> list[str]:
    factors: list[str] = []
    if features["salary_unknown"] >= 1:
        factors.append("候选人期望薪资未知，需要人工确认薪资预期和到岗时间。")
    if features["salary_pressure"] >= 0.8:
        factors.append("候选人期望薪资接近或高于岗位预算上限，需要确认 offer 接受可能性。")
    if features["experience_gap"] >= 0.5:
        factors.append("候选人相关年限低于岗位要求，需面试确认项目深度和职责边界。")
    if features["evidence_gap"] >= 0.5:
        factors.append("部分技能缺少项目证据支撑，需要面试核实是否存在关键词堆砌。")
    if features["track_unknown"] >= 1:
        factors.append("候选人投递类型仍不明确，需要 HR 确认校招、社招或实习轨道。")
    if not factors:
        factors.append("模型未识别出显著流程级风险，仍建议通过面试核实关键项目证据。")
    return factors
