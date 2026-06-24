from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AddedLine:
    file_path: str
    new_line_number: int
    content: str


@dataclass(frozen=True)
class FileChange:
    path: str
    added_lines: list[AddedLine] = field(default_factory=list)
    is_test: bool = False


@dataclass(frozen=True)
class ParsedDiff:
    files: list[FileChange] = field(default_factory=list)
    has_tests: bool = False


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    title_zh: str
    severity: str
    file_path: str
    line_number: int
    message: str
    message_zh: str
    recommendation: str
    recommendation_zh: str


@dataclass(frozen=True)
class ReviewSummary:
    changed_files: list[str]
    total_added_lines: int
    finding_count: int
    test_files_changed: bool
    added_lines_by_file: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class FileContextStrategy:
    file_path: str
    added_lines: int
    risk_score: int
    strategy: str
    reason: str


@dataclass(frozen=True)
class ContextPlan:
    total_files: int
    total_added_lines: int
    modules: list[str]
    file_strategies: list[FileContextStrategy]


@dataclass(frozen=True)
class ImpactCall:
    symbol: str
    file_path: str
    line_number: int
    call_style: str


@dataclass(frozen=True)
class ImpactAnalysis:
    changed_symbols: list[str]
    direct_callers: list[ImpactCall]
    impact_level: str
    attention_files: list[str]


@dataclass(frozen=True)
class ReviewComment:
    file: str
    line: int
    severity: str
    rule_id: str
    message: str
    message_en: str
    suggested_fix: str


@dataclass(frozen=True)
class StructuredReviewOutput:
    risk_level: str
    risk_score: int
    risk_reasons: list[str]
    affected_files: list[str]
    review_comments: list[ReviewComment]
    test_coverage_gaps: list[str]
    impact_analysis: ImpactAnalysis
    auto_approve_eligible: bool


@dataclass(frozen=True)
class HarnessAgent:
    name: str
    responsibility: str
    input_source: str
    output: str


@dataclass(frozen=True)
class MemoryLayer:
    name: str
    purpose: str
    retention: str


@dataclass(frozen=True)
class SandboxPolicy:
    mode: str
    allowed_operations: list[str]
    blocked_operations: list[str]


@dataclass(frozen=True)
class ResiliencePolicy:
    primary_path: str
    fallbacks: list[str]
    retryable_errors: list[str]


@dataclass(frozen=True)
class ObservabilityProfile:
    trace_id: str
    events: list[str]
    metrics: dict[str, int]


@dataclass(frozen=True)
class AgentHarnessProfile:
    agents: list[HarnessAgent]
    memory_layers: list[MemoryLayer]
    sandbox: SandboxPolicy
    resilience: ResiliencePolicy
    observability: ObservabilityProfile


@dataclass(frozen=True)
class ReviewReport:
    risk_level: str
    summary: ReviewSummary
    findings: list[Finding]
    test_plan: list[str]
    test_plan_zh: list[str]
    context_plan: ContextPlan
    impact_analysis: ImpactAnalysis
    structured_output: StructuredReviewOutput
    agent_harness: AgentHarnessProfile
    ai_review: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
