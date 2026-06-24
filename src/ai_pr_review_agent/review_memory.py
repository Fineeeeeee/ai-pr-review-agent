from __future__ import annotations

import json
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
