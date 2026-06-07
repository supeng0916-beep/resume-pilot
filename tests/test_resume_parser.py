from __future__ import annotations

from core.resume_parser import parse_resume_text


def test_parse_resume_text_extracts_core_candidate_fields() -> None:
    profile = parse_resume_text(
        "候选人：张三。5 年 Python 后端开发经验，熟悉 FastAPI、PostgreSQL、Redis，"
        "参与过 LLM 应用和数据平台项目。期望薪资 30k，当前在职，学历本科。"
    )

    assert profile.name == "张三"
    assert profile.education == "本科"
    assert profile.years_experience == 5
    assert profile.expected_salary == "30k CNY/month"
    assert profile.current_status == "在职"
    assert set(profile.skills) >= {"Python", "FastAPI", "PostgreSQL", "Redis", "LLM"}
    assert profile.work_experiences


def test_parse_resume_text_supports_campus_style_resume() -> None:
    profile = parse_resume_text(
        "姓名：李四。本科，2026届应届生。校园项目：使用 Python 和 MySQL "
        "开发课程管理系统。期望薪资 面议。"
    )

    assert profile.name == "李四"
    assert profile.education == "本科"
    assert profile.years_experience == 0
    assert "Python" in profile.skills
    assert "MySQL" in profile.skills
    assert profile.current_status == "应届"


def test_parse_resume_text_separates_projects_and_internships_from_work_experience() -> None:
    profile = parse_resume_text(
        "苏鹏\n2025-04 至今 泰莱大学 应用计算机（数据科学方向）| 硕士\n"
        "项目经历\n智图寻宝——基于CNN算法的智能商品识别系统|独立开发者\n"
        "项目描述: 基于 PyTorch 和 Flask 开发计算机视觉系统。\n"
        "会计助理（实习） | 某建筑工程有限公司\n"
        "技能标签: Python, Streamlit, Feature Engineering, Data Pipeline"
    )

    assert profile.current_status == "在读"
    assert profile.work_experiences == []
    assert profile.campus_projects
    assert profile.internships
    assert set(profile.skills) >= {"Python", "PyTorch", "Flask", "Streamlit"}


def test_parse_resume_text_creates_skill_evidence() -> None:
    profile = parse_resume_text(
        "姓名：王五。负责使用 Redis 优化热点数据缓存，熟悉 Docker 部署。"
    )

    evidence_by_skill = {item.skill: item for item in profile.skill_evidence}

    assert evidence_by_skill["Redis"].evidence_strength == "strong"
    assert evidence_by_skill["Redis"].evidence
    assert evidence_by_skill["Docker"].evidence_strength in {"medium", "strong"}
