from __future__ import annotations

from pathlib import Path

from .checks import run_static_checks
from .agent_harness import build_agent_harness
from .context_compressor import build_context_plan
from .diff_parser import parse_unified_diff
from .impact_analysis import analyze_impact
from .models import ReviewReport, ReviewSummary
from .structured_output import build_structured_output


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def review_diff(diff_text: str, repo_path: Path | None = None) -> ReviewReport:
    parsed = parse_unified_diff(diff_text)
    findings = run_static_checks(parsed)
    summary = ReviewSummary(
        changed_files=[file.path for file in parsed.files],
        total_added_lines=sum(len(file.added_lines) for file in parsed.files),
        finding_count=len(findings),
        test_files_changed=parsed.has_tests,
        added_lines_by_file={file.path: len(file.added_lines) for file in parsed.files},
    )
    risk_level = calculate_risk_level([finding.severity for finding in findings])
    test_plan = build_test_plan(summary, risk_level)
    test_plan_zh = build_test_plan_zh(summary, risk_level)
    impact_analysis = analyze_impact(diff_text, repo_path=repo_path)
    context_plan = build_context_plan(summary, findings)
    structured_output = build_structured_output(
        risk_level=risk_level,
        summary=summary,
        findings=findings,
        test_plan_zh=test_plan_zh,
        impact_analysis=impact_analysis,
    )
    report = ReviewReport(
        risk_level=risk_level,
        summary=summary,
        findings=findings,
        test_plan=test_plan,
        test_plan_zh=test_plan_zh,
        context_plan=context_plan,
        impact_analysis=impact_analysis,
        structured_output=structured_output,
        agent_harness=None,  # type: ignore[arg-type]
    )
    return report.__class__(
        risk_level=report.risk_level,
        summary=report.summary,
        findings=report.findings,
        test_plan=report.test_plan,
        test_plan_zh=report.test_plan_zh,
        context_plan=report.context_plan,
        impact_analysis=report.impact_analysis,
        structured_output=report.structured_output,
        agent_harness=build_agent_harness(report),
    )


def calculate_risk_level(severities: list[str]) -> str:
    if not severities:
        return "low"
    if "critical" in severities:
        return "critical"
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"


def build_test_plan(summary: ReviewSummary, risk_level: str) -> list[str]:
    if not summary.changed_files:
        return ["No changed files were detected in the provided diff."]

    plan = [
        "Run the fastest unit tests that cover the changed files.",
        "Review each finding and add a regression test for confirmed defects.",
    ]
    if not summary.test_files_changed:
        plan.append("Add a focused test file or update an existing one before merge.")
    if RISK_ORDER[risk_level] >= RISK_ORDER["high"]:
        plan.append("Run security-focused checks and manually inspect all high-risk lines.")
    return plan


def build_test_plan_zh(summary: ReviewSummary, risk_level: str) -> list[str]:
    if not summary.changed_files:
        return ["没有在输入的 diff 中检测到变更文件。"]

    plan = [
        "运行覆盖变更文件的最快单元测试。",
        "逐条确认审查发现，并为确认的问题补充回归测试。",
    ]
    if not summary.test_files_changed:
        plan.append("为变更行为补充聚焦测试，或更新已有测试后再合并。")
    if RISK_ORDER[risk_level] >= RISK_ORDER["high"]:
        plan.append("运行安全相关检查，并人工复核所有高风险代码行。")
    return plan
