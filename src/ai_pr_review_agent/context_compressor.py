from __future__ import annotations

from collections import defaultdict

from .models import ContextPlan, FileContextStrategy, Finding, ReviewSummary


SEVERITY_SCORE = {"low": 10, "medium": 40, "high": 70, "critical": 100}
SECURITY_RULES = {"secret_literal", "sql_interpolation", "unsafe_eval", "shell_execution"}


def build_context_plan(summary: ReviewSummary, findings: list[Finding]) -> ContextPlan:
    findings_by_file: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        findings_by_file[finding.file_path].append(finding)

    strategies = [
        build_file_strategy(path, findings_by_file.get(path, []), summary.added_lines_by_file.get(path, 0))
        for path in summary.changed_files
    ]
    strategies.sort(key=lambda item: item.risk_score, reverse=True)

    return ContextPlan(
        total_files=len(summary.changed_files),
        total_added_lines=summary.total_added_lines,
        modules=sorted({top_level_module(path) for path in summary.changed_files}),
        file_strategies=strategies,
    )


def build_file_strategy(path: str, findings: list[Finding], added_lines: int) -> FileContextStrategy:
    risk_score = max((SEVERITY_SCORE.get(finding.severity, 0) for finding in findings), default=0)
    normalized = path.replace("\\", "/").lower()

    if any(finding.rule_id in SECURITY_RULES for finding in findings):
        return FileContextStrategy(path, added_lines, risk_score, "full", "high_risk_finding")
    if is_low_risk_path(normalized):
        return FileContextStrategy(path, added_lines, risk_score, "skip", "low_risk_file_type")
    if findings:
        return FileContextStrategy(path, added_lines, risk_score, "focused", "has_review_finding")
    return FileContextStrategy(path, added_lines, risk_score, "summary", "no_high_risk_signal")

def top_level_module(path: str) -> str:
    normalized = path.replace("\\", "/")
    return normalized.split("/", 1)[0] if "/" in normalized else "."


def is_low_risk_path(path: str) -> bool:
    return path.endswith((".md", ".txt", ".css", ".scss", ".json", ".yml", ".yaml"))
