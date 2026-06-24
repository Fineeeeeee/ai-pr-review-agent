from __future__ import annotations

import json

from .models import ReviewReport


def render_harness_manifest(report: ReviewReport) -> str:
    return json.dumps(
        {
            "report": {
                "risk_level": report.risk_level,
                "finding_count": report.summary.finding_count,
                "changed_files": report.summary.changed_files,
            },
            "agent_harness": report.agent_harness,
        },
        ensure_ascii=False,
        indent=2,
        default=lambda value: value.__dict__,
    )
