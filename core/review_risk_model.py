from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


REVIEW_RISK_FEATURES = [
    "required_skill_coverage",
    "parse_quality_gap",
    "salary_pressure",
    "experience_gap",
    "evidence_gap",
    "track_unknown",
    "weak_match",
]


def _index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if row.get(key) is not None}


def _evidence_gap(label: dict[str, Any]) -> float:
    quality = label.get("evidence_quality")
    if quality == "strong":
        return 0.0
    if quality == "medium":
        return 0.25
    if quality == "weak":
        return 0.7
    return 1.0


def _feature_row(candidate: dict[str, Any], job: dict[str, Any], label: dict[str, Any]) -> dict[str, float]:
    required_skills = set(job.get("required_skills") or [])
    candidate_skills = set(candidate.get("skills") or [])
    coverage = len(required_skills & candidate_skills) / max(len(required_skills), 1)

    salary_max = float(job.get("salary_max_k") or 0)
    expected_salary = float(candidate.get("expected_salary_k") or 0)
    salary_pressure = 0.0
    if salary_max > 0:
        salary_pressure = max(0.0, min(1.0, (expected_salary - salary_max * 0.85) / (salary_max * 0.35)))

    required_years = float(job.get("required_years") or 0)
    candidate_years = float(candidate.get("years_experience") or 0)
    experience_gap = 0.0
    if required_years > 0:
        experience_gap = max(0.0, min(1.0, (required_years - candidate_years) / required_years))

    return {
        "required_skill_coverage": round(coverage, 4),
        "parse_quality_gap": round(max(0.0, 1.0 - float(candidate.get("parse_quality_score") or 0)), 4),
        "salary_pressure": round(salary_pressure, 4),
        "experience_gap": round(experience_gap, 4),
        "evidence_gap": round(_evidence_gap(label), 4),
        "track_unknown": 1.0 if candidate.get("track") == "unknown" else 0.0,
        "weak_match": 1.0 if label.get("match_label") == "weak_match" else 0.0,
    }


def build_review_risk_rows(
    candidates: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_id = _index_by(candidates, "candidate_id")
    jobs_by_id = _index_by(jobs, "jd_id")
    rows: list[dict[str, Any]] = []
    for label in labels:
        candidate = candidates_by_id.get(str(label.get("candidate_id")))
        job = jobs_by_id.get(str(label.get("jd_id")))
        if not candidate or not job:
            continue
        rows.append(
            {
                "sample_id": label.get("sample_id"),
                "candidate_id": label.get("candidate_id"),
                "jd_id": label.get("jd_id"),
                "features": _feature_row(candidate, job, label),
                "label": 1.0 if label.get("needs_human_review") else 0.0,
            }
        )
    return rows


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def train_review_risk_model(
    rows: list[dict[str, Any]],
    *,
    epochs: int = 60,
    learning_rate: float = 0.05,
) -> dict[str, Any]:
    weights = {name: 0.0 for name in REVIEW_RISK_FEATURES}
    bias = 0.0
    for _ in range(epochs):
        for row in rows:
            features = row["features"]
            logit = bias + sum(weights[name] * float(features.get(name, 0.0)) for name in REVIEW_RISK_FEATURES)
            prediction = _sigmoid(logit)
            error = prediction - float(row["label"])
            bias -= learning_rate * error
            for name in REVIEW_RISK_FEATURES:
                weights[name] -= learning_rate * error * float(features.get(name, 0.0))

    return {
        "model_type": "review_risk_logistic_v1",
        "target": "needs_human_review",
        "feature_order": REVIEW_RISK_FEATURES,
        "bias": round(bias, 6),
        "weights": {name: round(value, 6) for name, value in weights.items()},
        "training": {
            "rows": len(rows),
            "epochs": epochs,
            "learning_rate": learning_rate,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "data_source": "synthetic_or_annotated_jsonl",
            "disclaimer": "Predicts manual-review need only; not a hiring decision model.",
        },
    }


def predict_review_risk_score(model: dict[str, Any], features: dict[str, float]) -> float:
    logit = float(model.get("bias", 0.0))
    weights = model.get("weights") or {}
    for name in model.get("feature_order") or REVIEW_RISK_FEATURES:
        logit += float(weights.get(name, 0.0)) * float(features.get(name, 0.0))
    return round(_sigmoid(logit), 4)


def evaluate_classifier(model: dict[str, Any], rows: list[dict[str, Any]], *, threshold: float = 0.5) -> dict[str, float]:
    tp = fp = tn = fn = 0
    for row in rows:
        prediction = predict_review_risk_score(model, row["features"]) >= threshold
        label = bool(row["label"])
        if prediction and label:
            tp += 1
        elif prediction and not label:
            fp += 1
        elif not prediction and not label:
            tn += 1
        else:
            fn += 1

    total = max(tp + fp + tn + fn, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    positive_rate = (tp + fn) / total
    return {
        "accuracy": round((tp + tn) / total, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "positive_rate": round(positive_rate, 4),
        "threshold": threshold,
        "rows": float(total),
    }


def render_model_card(model: dict[str, Any], metrics: dict[str, float]) -> str:
    weights = model.get("weights") or {}
    weight_lines = [
        f"- `{name}`: {weights.get(name, 0.0)}"
        for name in model.get("feature_order") or REVIEW_RISK_FEATURES
    ]
    return "\n".join(
        [
            "# 人工复核风险模型",
            "",
            "## 用途",
            "",
            "该模型预测候选人评估结果是否需要人工重点复核，不用于自动录用或淘汰候选人。",
            "",
            "## 目标",
            "",
            f"- Target: `{model.get('target')}`",
            f"- Model type: `{model.get('model_type')}`",
            "",
            "## 训练数据",
            "",
            f"- Rows: {model.get('training', {}).get('rows')}",
            f"- Data source: {model.get('training', {}).get('data_source')}",
            "",
            "## 指标",
            "",
            f"- Accuracy: {metrics.get('accuracy')}",
            f"- Precision: {metrics.get('precision')}",
            f"- Recall: {metrics.get('recall')}",
            f"- F1: {metrics.get('f1')}",
            "",
            "## 特征权重",
            "",
            *weight_lines,
            "",
            "## 合规边界",
            "",
            "该模型只用于排序人工复核优先级，最终招聘判断必须由人工完成。",
        ]
    )
