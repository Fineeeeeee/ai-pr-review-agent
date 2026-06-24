from __future__ import annotations

from .models import (
    Finding,
    ImpactAnalysis,
    ReviewComment,
    ReviewSummary,
    StructuredReviewOutput,
)


RISK_SCORE = {"low": 20, "medium": 50, "high": 80, "critical": 100}


def build_structured_output(
    risk_level: str,
    summary: ReviewSummary,
    findings: list[Finding],
    test_plan_zh: list[str],
    impact_analysis: ImpactAnalysis,
) -> StructuredReviewOutput:
    return StructuredReviewOutput(
        risk_level=risk_level,
        risk_score=RISK_SCORE.get(risk_level, 0),
        risk_reasons=[finding.title_zh for finding in findings],
        affected_files=summary.changed_files,
        review_comments=[finding_to_comment(finding) for finding in findings],
        test_coverage_gaps=[
            item for item in test_plan_zh if "测试" in item and ("补充" in item or "覆盖" in item)
        ],
        impact_analysis=impact_analysis,
        auto_approve_eligible=is_auto_approve_eligible(risk_level, findings, summary),
    )


def finding_to_comment(finding: Finding) -> ReviewComment:
    return ReviewComment(
        file=finding.file_path,
        line=finding.line_number,
        severity=finding.severity.upper(),
        rule_id=finding.rule_id,
        message=finding.message_zh,
        message_en=finding.message,
        suggested_fix=finding.recommendation_zh,
    )


def is_auto_approve_eligible(
    risk_level: str,
    findings: list[Finding],
    summary: ReviewSummary,
) -> bool:
    if risk_level != "low":
        return False
    if findings:
        return False
    if not summary.test_files_changed and summary.total_added_lines > 0:
        return False
    return True
