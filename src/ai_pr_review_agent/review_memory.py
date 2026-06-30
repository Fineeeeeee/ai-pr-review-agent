from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .models import ReviewReport


def append_review_events(report: ReviewReport, memory_path: Path) -> int:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "rule_id": finding.rule_id,
            "file": finding.file_path,
            "line": finding.line_number,
            "severity": finding.severity,
            "feedback_status": "pending",
            "developer_action": "unknown",
        }
        for finding in report.findings
    ]
    with memory_path.open("a", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return len(events)


def load_review_events(memory_path: Path) -> list[dict[str, object]]:
    if not memory_path.exists():
        return []
    events = []
    with memory_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def summarize_review_events(events: list[dict[str, object]]) -> dict[str, object]:
    by_status = Counter(str(event.get("feedback_status", "unknown")) for event in events)
    by_rule = Counter(str(event.get("rule_id", "unknown")) for event in events)
    false_positive_by_rule = Counter(
        str(event.get("rule_id", "unknown"))
        for event in events
        if event.get("feedback_status") == "false_positive"
    )
    false_negative_by_rule = Counter(
        str(event.get("rule_id", "unknown"))
        for event in events
        if event.get("feedback_status") == "false_negative"
    )
    accepted_by_rule = Counter(
        str(event.get("rule_id", "unknown"))
        for event in events
        if event.get("feedback_status") == "accepted"
    )
    return {
        "total_events": len(events),
        "by_status": dict(sorted(by_status.items())),
        "by_rule": dict(sorted(by_rule.items())),
        "accepted_by_rule": dict(sorted(accepted_by_rule.items())),
        "false_positive_by_rule": dict(sorted(false_positive_by_rule.items())),
        "false_negative_by_rule": dict(sorted(false_negative_by_rule.items())),
        "rule_health": build_rule_health(events),
    }


def build_rule_health(events: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, Counter[str]] = {}
    for event in events:
        rule_id = str(event.get("rule_id", "unknown"))
        status = str(event.get("feedback_status", "unknown"))
        grouped.setdefault(rule_id, Counter())[status] += 1

    health: dict[str, dict[str, object]] = {}
    for rule_id, statuses in sorted(grouped.items()):
        reviewed_count = statuses["accepted"] + statuses["false_positive"] + statuses["false_negative"]
        false_positive_count = statuses["false_positive"]
        false_negative_count = statuses["false_negative"]
        false_positive_rate = round((false_positive_count / reviewed_count) * 100, 2) if reviewed_count else 0.0
        health[rule_id] = {
            "reviewed_count": reviewed_count,
            "accepted_count": statuses["accepted"],
            "false_positive_count": false_positive_count,
            "false_negative_count": false_negative_count,
            "false_positive_rate": false_positive_rate,
            "recommendation": recommend_rule_action(reviewed_count, false_positive_rate, false_negative_count),
        }
    return health


def recommend_rule_action(reviewed_count: int, false_positive_rate: float, false_negative_count: int) -> str:
    if reviewed_count == 0:
        return "collect_more_feedback"
    if false_negative_count > 0:
        return "expand_coverage"
    if false_positive_rate >= 50:
        return "watch"
    return "keep"
