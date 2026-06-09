from __future__ import annotations

from harness.llm_eval import evaluate_extraction_case, render_extraction_eval_report


def test_extraction_eval_compares_rule_llm_and_golden_profiles() -> None:
    golden_candidate = {
        "name": "Alice",
        "education": "Bachelor",
        "years_experience": 0,
        "skills": ["Python", "FastAPI"],
        "expected_salary": "20k CNY/month",
        "candidate_track": "campus",
    }
    llm_candidate = {
        **golden_candidate,
        "skills": ["Python", "FastAPI", "Redis"],
    }

    result = evaluate_extraction_case(
        case_id="case-001",
        resume_text="Alice uses Python and FastAPI in a campus project.",
        jd_text="Backend engineer requires Python and FastAPI.",
        golden_candidate=golden_candidate,
        golden_job={
            "title": "Backend Engineer",
            "required_years": 0,
            "required_skills": ["Python", "FastAPI"],
            "recruitment_track": "campus",
        },
        llm_candidate=llm_candidate,
        llm_job={
            "title": "Backend Engineer",
            "required_years": 0,
            "required_skills": ["Python", "FastAPI"],
            "recruitment_track": "campus",
        },
    )

    assert result["case_id"] == "case-001"
    assert result["candidate"]["llm"]["field_accuracy"] > result["candidate"]["rule"]["field_accuracy"]
    assert result["candidate"]["llm"]["skill_f1"] == 0.8


def test_extraction_eval_report_contains_aggregate_metrics() -> None:
    result = evaluate_extraction_case(
        case_id="case-001",
        resume_text="Python FastAPI",
        jd_text="Python FastAPI",
        golden_candidate={"name": "Alice", "skills": ["Python", "FastAPI"]},
        golden_job={"title": "Backend", "required_skills": ["Python", "FastAPI"]},
        llm_candidate={"name": "Alice", "skills": ["Python", "FastAPI"]},
        llm_job={"title": "Backend", "required_skills": ["Python", "FastAPI"]},
    )

    report = render_extraction_eval_report([result])

    assert "# LLM Extraction Eval Report" in report
    assert "candidate_llm_field_accuracy" in report
    assert "case-001" in report
