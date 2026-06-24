from __future__ import annotations

from core.schemas import EvaluationReport
from core.state import WorkflowState


RECOMMENDATION_LABELS = {
    "advance": "建议进入下一轮",
    "reject": "暂不建议推进",
    "revise": "建议重写/复核报告",
    "need_more_info": "建议补充信息",
}


def _choose_recommendation(match_score: float, risk_score: float | None) -> str:
    if match_score >= 75 and (risk_score is None or risk_score < 0.5):
        return "advance"
    if match_score >= 55:
        return "need_more_info"
    return "reject"


def _build_strengths(state: WorkflowState) -> list[str]:
    match_breakdown = state.get("match_breakdown") or {}
    matched_skills = match_breakdown.get("matched_skills", [])
    strengths: list[str] = []

    if matched_skills:
        strengths.append(f"匹配到岗位关键技能：{', '.join(matched_skills)}。")

    dimension_scores = match_breakdown.get("dimension_scores", {})
    strong_dimensions = [
        name for name, score in dimension_scores.items() if isinstance(score, (int, float)) and score >= 80
    ]
    if strong_dimensions:
        strengths.append(f"高分维度：{', '.join(strong_dimensions)}。")

    return strengths or ["暂未发现明确高置信度匹配亮点。"]


def _build_risks(state: WorkflowState) -> list[str]:
    risks = list(state.get("risk_factors", []))
    match_breakdown = state.get("match_breakdown") or {}

    missing_evidence = [
        note for note in match_breakdown.get("evidence_notes", []) if "暂未找到项目证据" in note
    ]
    if missing_evidence:
        risks.append("部分技能仅出现在技能列表中，缺少项目经历支撑，需要面试核实。")

    if (state.get("match_score") or 0) < 60:
        risks.append("总体匹配分偏低，需要确认岗位要求与候选人经历是否一致。")

    return risks or ["当前未发现显著流程级风险，但仍需人工复核。"]


def _build_questions(state: WorkflowState) -> list[str]:
    candidate = state.get("candidate_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}
    track = match_breakdown.get("track", "unknown")
    matched_skills = match_breakdown.get("matched_skills", [])

    questions: list[str] = []
    if matched_skills:
        questions.append(f"请候选人选择一个项目，说明其中如何实际使用 {matched_skills[0]}。")
    if track == "campus":
        questions.append("请候选人说明最能代表其工程能力的课程项目、实习或个人项目。")
        questions.append("请候选人解释项目中遇到的最大技术困难，以及如何定位和解决。")
    elif track == "experienced":
        questions.append("请候选人说明最近一段工作经历中的职责边界、技术决策和业务结果。")
        questions.append("请候选人举例说明一次线上问题、性能问题或复杂协作问题的处理过程。")
    else:
        questions.append("请面试官先确认候选人投递类型：校招、社招或实习。")

    if candidate.get("expected_salary") in {None, "unknown"}:
        questions.append("请补充确认候选人的期望薪资和到岗时间。")

    return questions


def _build_memory_reference_lines(state: WorkflowState) -> list[str]:
    summaries = state.get("feedback_memory_summaries", [])
    if not summaries:
        return ["暂无同岗位或相似 JD 的历史人工反馈。"]
    return [
        f"{summary}（仅作为人工复核参考，不直接参与自动评分）"
        for summary in summaries
    ]


def _build_agent_collaboration_lines(state: WorkflowState) -> list[str]:
    lines: list[str] = []
    candidate_insights = state.get("candidate_insights") or {}
    job_insights = state.get("job_insights") or {}
    final_recommendation = state.get("final_recommendation") or {}
    agent_outputs = state.get("agent_outputs") or {}
    evidence_audit = agent_outputs.get("evidence_auditor") or {}
    critic = agent_outputs.get("critic_agent") or {}

    for item in candidate_insights.get("strengths", [])[:2]:
        lines.append(f"Candidate Analyst：{item}")
    for item in candidate_insights.get("gaps", [])[:2]:
        lines.append(f"Candidate Analyst Gap：{item}")
    for item in job_insights.get("priorities", [])[:2]:
        lines.append(f"Job Analyst：{item}")
    evidence_findings = evidence_audit.get("findings", {}) if isinstance(evidence_audit, dict) else {}
    unsupported_skills = evidence_findings.get("unsupported_skills", []) if isinstance(evidence_findings, dict) else []
    if unsupported_skills:
        lines.append(f"Evidence Auditor：{', '.join(unsupported_skills)} 缺少直接简历证据。")
    critic_findings = critic.get("findings", {}) if isinstance(critic, dict) else {}
    critic_conflicts = critic_findings.get("conflicts", []) if isinstance(critic_findings, dict) else []
    for item in critic_conflicts[:2]:
        lines.append(f"Critic Agent：{item}")
    if final_recommendation.get("consensus_confidence") is not None:
        lines.append(f"Consensus Agent：多 Agent 一致置信度 {final_recommendation['consensus_confidence']}。")
    if final_recommendation.get("rationale"):
        lines.append(f"Final Recommendation：{final_recommendation['rationale']}")

    return lines or ["Supervisor 已完成任务编排，并将结果汇总到最终评估中。"]


def build_report_model(state: WorkflowState) -> EvaluationReport:
    candidate = state.get("candidate_profile") or {}
    job = state.get("job_profile") or {}
    match_score = float(state.get("match_score") or 0)
    risk_score = state.get("risk_score")
    recommendation = _choose_recommendation(match_score, risk_score)

    summary = (
        f"候选人 {candidate.get('name', '未知候选人')} 投递岗位「{job.get('title', '未知岗位')}」，"
        f"当前匹配分为 {match_score}，风险分为 {risk_score if risk_score is not None else '未知'}。"
    )

    return EvaluationReport(
        recommendation=recommendation,
        summary=summary,
        strengths=_build_strengths(state),
        risks=_build_risks(state),
        suggested_interview_questions=_build_questions(state),
    )


def render_markdown_report(state: WorkflowState) -> str:
    report = build_report_model(state)
    candidate = state.get("candidate_profile") or {}
    match_breakdown = state.get("match_breakdown") or {}
    scoring_rubric = state.get("scoring_rubric") or {}
    evidence_notes = match_breakdown.get("evidence_notes", [])

    sections = [
        "# 招聘评估报告",
        "## 候选人摘要",
        report.summary,
        "",
        "## 评分结论",
        f"- 评分轨道：{scoring_rubric.get('track', 'unknown')}",
        f"- 评分说明：{scoring_rubric.get('rationale', '暂无')}",
        f"- 匹配分：{state.get('match_score')}",
        f"- 风险分：{state.get('risk_score')}",
        f"- 人工审批建议：{RECOMMENDATION_LABELS[report.recommendation]}",
        "",
        "## 匹配亮点",
        *[f"- {item}" for item in report.strengths],
        "",
        "## 风险点",
        *[f"- {item}" for item in report.risks],
        "",
        "## 证据引用",
        *[
            f"- {item}"
            for item in (evidence_notes or ["暂无结构化证据引用。"])
        ],
        "",
        "## 建议面试问题",
        *[f"- {item}" for item in report.suggested_interview_questions],
        "",
        "## 历史 HR 反馈参考",
        *[f"- {item}" for item in _build_memory_reference_lines(state)],
        "",
        "## Agent 协作摘要",
        *[f"- {item}" for item in _build_agent_collaboration_lines(state)],
        "",
        "## 人工复核提示",
        f"- 候选人类型判断：{candidate.get('candidate_track', 'unknown')}，置信度 {candidate.get('track_confidence', 0)}。",
        f"- 判断依据：{candidate.get('track_reason') or '暂无'}",
    ]

    return "\n".join(sections)
