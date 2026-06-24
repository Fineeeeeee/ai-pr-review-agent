from __future__ import annotations

import json

from .models import Finding, ReviewReport


SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
}


def render_sarif(report: ReviewReport) -> str:
    rules = {finding.rule_id: finding for finding in report.findings}
    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "AI PR Review Agent",
                        "informationUri": "https://github.com/local/ai-pr-review-agent",
                        "rules": [rule_to_sarif(rule_id, finding) for rule_id, finding in rules.items()],
                    }
                },
                "results": [finding_to_sarif(finding) for finding in report.findings],
            }
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def rule_to_sarif(rule_id: str, finding: Finding) -> dict[str, object]:
    return {
        "id": rule_id,
        "name": finding.title,
        "shortDescription": {"text": finding.title},
        "fullDescription": {"text": finding.message},
        "help": {"text": finding.recommendation},
    }


def finding_to_sarif(finding: Finding) -> dict[str, object]:
    line = finding.line_number if finding.line_number > 0 else 1
    return {
        "ruleId": finding.rule_id,
        "level": SEVERITY_TO_LEVEL.get(finding.severity, "warning"),
        "message": {"text": f"{finding.title_zh}: {finding.message_zh}"},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file_path},
                    "region": {"startLine": line},
                }
            }
        ],
        "properties": {
            "severity": finding.severity,
            "recommendation": finding.recommendation_zh,
        },
    }
