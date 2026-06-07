from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping


SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class QualityCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReportQualityResult:
    passed: bool
    score: float
    checks: list[QualityCheck]
    missing_requirements: list[str]
    warnings: list[str]

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "checks": [check.__dict__ for check in self.checks],
            "missing_requirements": self.missing_requirements,
            "warnings": self.warnings,
        }


def _extract_sections(report: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(report))
    sections: dict[str, str] = {}

    for index, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report)
        sections[section_name] = report[start:end].strip()

    return sections


def _has_non_empty_section(sections: Mapping[str, str], section_name: str) -> bool:
    return bool(sections.get(section_name, "").strip())


def _has_meaningful_bullet(section_text: str) -> bool:
    bullet_lines = [line.strip() for line in section_text.splitlines() if line.strip().startswith("-")]
    return any("暂无" not in line and len(line.removeprefix("-").strip()) >= 4 for line in bullet_lines)


def evaluate_report_quality(report: str | None) -> ReportQualityResult:
    report_text = report or ""
    sections = _extract_sections(report_text)
    checks = [
        QualityCheck(
            name="candidate_summary",
            passed=_has_non_empty_section(sections, "候选人摘要"),
            detail="报告需要包含候选人摘要，帮助招聘官快速理解评估对象。",
        ),
        QualityCheck(
            name="scoring_conclusion",
            passed=_has_non_empty_section(sections, "评分结论")
            and "匹配分" in sections.get("评分结论", "")
            and "人工审批建议" in sections.get("评分结论", ""),
            detail="报告需要说明匹配分、评分轨道和人工审批建议。",
        ),
        QualityCheck(
            name="evidence_citations",
            passed=_has_meaningful_bullet(sections.get("证据引用", "")),
            detail="报告需要引用至少一条可核验的技能或项目证据。",
        ),
        QualityCheck(
            name="risk_points",
            passed=_has_meaningful_bullet(sections.get("风险点", "")),
            detail="报告需要列出风险点；无显著风险时也应说明仍需人工核实。",
        ),
        QualityCheck(
            name="interview_questions",
            passed=_has_meaningful_bullet(sections.get("建议面试问题", "")),
            detail="报告需要给出可用于下一轮面试的追问问题。",
        ),
        QualityCheck(
            name="human_review_note",
            passed=_has_non_empty_section(sections, "人工复核提示"),
            detail="报告需要提醒人工复核候选人类型、置信度和判断依据。",
        ),
    ]

    missing = [check.name for check in checks if not check.passed]
    score = round(sum(check.passed for check in checks) / len(checks), 4)
    warnings = []
    if "暂无结构化证据引用" in report_text:
        warnings.append("报告没有结构化证据引用，可能削弱可解释性。")
    if "unknown" in sections.get("评分结论", ""):
        warnings.append("评分轨道仍为 unknown，建议人工确认候选人投递类型。")

    return ReportQualityResult(
        passed=not missing,
        score=score,
        checks=checks,
        missing_requirements=missing,
        warnings=warnings,
    )


def evaluate_workflow_result(result: Mapping[str, object]) -> ReportQualityResult:
    report = result.get("report")
    return evaluate_report_quality(report if isinstance(report, str) else None)
