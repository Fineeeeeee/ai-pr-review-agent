from __future__ import annotations

import hashlib

from .models import (
    AgentHarnessProfile,
    HarnessAgent,
    MemoryLayer,
    ObservabilityProfile,
    ResiliencePolicy,
    ReviewReport,
    SandboxPolicy,
)


def build_agent_harness(report: ReviewReport) -> AgentHarnessProfile:
    return AgentHarnessProfile(
        agents=[
            HarnessAgent("diff_parser_agent", "Parse git diff into files and added lines.", "diff_text", "ParsedDiff"),
            HarnessAgent("rule_review_agent", "Run deterministic security and quality rules.", "ParsedDiff", "findings"),
            HarnessAgent("impact_agent", "Find changed symbols and direct callers.", "diff_text + repo", "ImpactAnalysis"),
            HarnessAgent("context_agent", "Route files to full, focused, summary, or skip analysis.", "summary + findings", "ContextPlan"),
            HarnessAgent("llm_review_agent", "Optionally call DeepSeek with compressed context.", "ContextPlan + selected diff", "ai_review"),
        ],
        memory_layers=[
            MemoryLayer("working_memory", "Current diff, findings, context plan, and structured output.", "per_review"),
            MemoryLayer("review_memory", "JSONL feedback events for accepted, false positive, and false negative findings.", "append_only"),
            MemoryLayer("pattern_memory", "Recurring safe or noisy review patterns for future down-ranking.", "future_extension"),
        ],
        sandbox=SandboxPolicy(
            mode="read_only_default",
            allowed_operations=["read_diff", "read_repo_python_files", "write_report", "append_review_memory"],
            blocked_operations=["delete_files", "modify_source_without_user_request", "write_secrets", "change_ci_cd"],
        ),
        resilience=ResiliencePolicy(
            primary_path="local_rule_engine",
            fallbacks=["local_rule_engine", "markdown_json_sarif_output", "skip_deepseek_when_api_key_missing"],
            retryable_errors=["deepseek_timeout", "deepseek_rate_limit", "temporary_network_error"],
        ),
        observability=ObservabilityProfile(
            trace_id=build_trace_id(report),
            events=[
                "diff_parsed",
                "rules_executed",
                "context_plan_built",
                "impact_analyzed",
                "structured_output_rendered",
            ],
            metrics={
                "changed_files": len(report.summary.changed_files),
                "findings": len(report.findings),
                "added_lines": report.summary.total_added_lines,
            },
        ),
    )


def build_trace_id(report: ReviewReport) -> str:
    seed = "|".join(report.summary.changed_files) + f":{report.summary.finding_count}:{report.risk_level}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"review-{digest}"
