from __future__ import annotations

from statistics import mean
from typing import Any

from core.job_parser import parse_jd_text
from core.resume_parser import parse_resume_text


DEFAULT_CANDIDATE_FIELDS = [
    "name",
    "education",
    "years_experience",
    "expected_salary",
    "candidate_track",
]
DEFAULT_JOB_FIELDS = ["title", "required_years", "recruitment_track"]


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _field_accuracy(predicted: dict[str, Any], golden: dict[str, Any], fields: list[str]) -> float:
    scored_fields = [field for field in fields if field in golden]
    if not scored_fields:
        return 0.0
    correct = sum(1 for field in scored_fields if _normalize(predicted.get(field)) == _normalize(golden.get(field)))
    return round(correct / len(scored_fields), 4)


def _skill_f1(predicted_skills: list[str] | None, golden_skills: list[str] | None) -> float:
    predicted = {_normalize(skill) for skill in predicted_skills or [] if _normalize(skill)}
    golden = {_normalize(skill) for skill in golden_skills or [] if _normalize(skill)}
    if not predicted and not golden:
        return 1.0
    if not predicted or not golden:
        return 0.0
    true_positive = len(predicted & golden)
    precision = true_positive / len(predicted)
    recall = true_positive / len(golden)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def _evaluate_profile(
    *,
    predicted: dict[str, Any],
    golden: dict[str, Any],
    fields: list[str],
    skill_key: str,
) -> dict[str, Any]:
    return {
        "field_accuracy": _field_accuracy(predicted, golden, fields),
        "skill_f1": _skill_f1(predicted.get(skill_key), golden.get(skill_key)),
    }


def evaluate_extraction_case(
    *,
    case_id: str,
    resume_text: str,
    jd_text: str,
    golden_candidate: dict[str, Any],
    golden_job: dict[str, Any],
    llm_candidate: dict[str, Any] | None = None,
    llm_job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rule_candidate = parse_resume_text(resume_text).model_dump()
    rule_job = parse_jd_text(jd_text).model_dump()
    llm_candidate = llm_candidate or {}
    llm_job = llm_job or {}

    return {
        "case_id": case_id,
        "candidate": {
            "rule": _evaluate_profile(
                predicted=rule_candidate,
                golden=golden_candidate,
                fields=DEFAULT_CANDIDATE_FIELDS,
                skill_key="skills",
            ),
            "llm": _evaluate_profile(
                predicted=llm_candidate,
                golden=golden_candidate,
                fields=DEFAULT_CANDIDATE_FIELDS,
                skill_key="skills",
            ),
        },
        "job": {
            "rule": _evaluate_profile(
                predicted=rule_job,
                golden=golden_job,
                fields=DEFAULT_JOB_FIELDS,
                skill_key="required_skills",
            ),
            "llm": _evaluate_profile(
                predicted=llm_job,
                golden=golden_job,
                fields=DEFAULT_JOB_FIELDS,
                skill_key="required_skills",
            ),
        },
    }


def _avg(results: list[dict[str, Any]], path: tuple[str, str, str]) -> float:
    values = [float(result[path[0]][path[1]][path[2]]) for result in results]
    return round(mean(values), 4) if values else 0.0


def render_extraction_eval_report(results: list[dict[str, Any]]) -> str:
    metrics = {
        "candidate_rule_field_accuracy": _avg(results, ("candidate", "rule", "field_accuracy")),
        "candidate_llm_field_accuracy": _avg(results, ("candidate", "llm", "field_accuracy")),
        "candidate_rule_skill_f1": _avg(results, ("candidate", "rule", "skill_f1")),
        "candidate_llm_skill_f1": _avg(results, ("candidate", "llm", "skill_f1")),
        "job_rule_field_accuracy": _avg(results, ("job", "rule", "field_accuracy")),
        "job_llm_field_accuracy": _avg(results, ("job", "llm", "field_accuracy")),
        "job_rule_skill_f1": _avg(results, ("job", "rule", "skill_f1")),
        "job_llm_skill_f1": _avg(results, ("job", "llm", "skill_f1")),
    }
    lines = [
        "# LLM Extraction Eval Report",
        "",
        "## Aggregate Metrics",
        *[f"- {name}: {value}" for name, value in metrics.items()],
        "",
        "## Cases",
    ]
    for result in results:
        lines.append(
            "- {case_id}: candidate(rule={cr}, llm={cl}), job(rule={jr}, llm={jl})".format(
                case_id=result["case_id"],
                cr=result["candidate"]["rule"]["field_accuracy"],
                cl=result["candidate"]["llm"]["field_accuracy"],
                jr=result["job"]["rule"]["field_accuracy"],
                jl=result["job"]["llm"]["field_accuracy"],
            )
        )
    return "\n".join(lines)
