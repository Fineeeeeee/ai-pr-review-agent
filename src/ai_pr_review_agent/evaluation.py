from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .reviewer import review_diff


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    expected_rules: list[str]
    detected_rules: list[str]
    missed_rules: list[str]
    unexpected_rules: list[str]
    latency_ms: float
    context_full_count: int
    context_skip_count: int
    risk_level: str


@dataclass(frozen=True)
class EvaluationResult:
    sample_count: int
    expected_positive_count: int
    detected_positive_count: int
    missed_positive_count: int
    false_positive_count: int
    recall_percent: float
    precision_percent: float
    average_latency_ms: float
    high_risk_full_analysis_percent: float
    low_risk_skip_percent: float
    cases: list[CaseResult]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_dataset(dataset_dir: Path) -> EvaluationResult:
    manifest_path = dataset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_results: list[CaseResult] = []

    for case in manifest:
        diff_text = (dataset_dir / case["file"]).read_text(encoding="utf-8")
        started = time.perf_counter()
        report = review_diff(diff_text)
        latency_ms = (time.perf_counter() - started) * 1000
        expected = sorted(case.get("expected_rules", []))
        detected = sorted({finding.rule_id for finding in report.findings})
        missed = [rule for rule in expected if rule not in detected]
        unexpected = [rule for rule in detected if rule not in expected]
        case_results.append(
            CaseResult(
                case_id=case["id"],
                expected_rules=expected,
                detected_rules=detected,
                missed_rules=missed,
                unexpected_rules=unexpected,
                latency_ms=latency_ms,
                context_full_count=count_strategy(report, "full"),
                context_skip_count=count_strategy(report, "skip"),
                risk_level=report.risk_level,
            )
        )

    expected_positive_count = sum(len(case.expected_rules) for case in case_results)
    detected_positive_count = sum(
        len([rule for rule in case.detected_rules if rule in case.expected_rules])
        for case in case_results
    )
    missed_positive_count = sum(len(case.missed_rules) for case in case_results)
    false_positive_count = sum(len(case.unexpected_rules) for case in case_results)
    detected_total = detected_positive_count + false_positive_count
    average_latency_ms = (
        sum(case.latency_ms for case in case_results) / len(case_results)
        if case_results
        else 0.0
    )
    total_files = sum(case.context_full_count + case.context_skip_count for case in case_results)
    full_count = sum(case.context_full_count for case in case_results)
    skip_count = sum(case.context_skip_count for case in case_results)

    return EvaluationResult(
        sample_count=len(case_results),
        expected_positive_count=expected_positive_count,
        detected_positive_count=detected_positive_count,
        missed_positive_count=missed_positive_count,
        false_positive_count=false_positive_count,
        recall_percent=percentage(detected_positive_count, expected_positive_count),
        precision_percent=percentage(detected_positive_count, detected_total),
        average_latency_ms=round(average_latency_ms, 2),
        high_risk_full_analysis_percent=percentage(full_count, total_files),
        low_risk_skip_percent=percentage(skip_count, total_files),
        cases=case_results,
    )


def count_strategy(report, strategy: str) -> int:
    return sum(1 for item in report.context_plan.file_strategies if item.strategy == strategy)


def percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 100.0
    return round((numerator / denominator) * 100, 2)


def render_evaluation_markdown(result: EvaluationResult) -> str:
    lines = [
        "# AI PR Review Agent Evaluation",
        "",
        f"- Sample Count / 样本数: {result.sample_count}",
        f"- Expected Positive Rules / 预期风险规则数: {result.expected_positive_count}",
        f"- Detected Positive Rules / 命中风险规则数: {result.detected_positive_count}",
        f"- Missed Positive Rules / 漏检规则数: {result.missed_positive_count}",
        f"- False Positives / 误报规则数: {result.false_positive_count}",
        f"- Recall / 召回率: {result.recall_percent}%",
        f"- Precision / 精确率: {result.precision_percent}%",
        f"- Average Latency / 平均分析耗时: {result.average_latency_ms} ms",
        f"- Full Analysis Share / 全量分析占比: {result.high_risk_full_analysis_percent}%",
        f"- Skip Share / 跳过占比: {result.low_risk_skip_percent}%",
        "",
        "## Case Details / 样本明细",
        "",
    ]
    for case in result.cases:
        lines.extend(
            [
                f"### {case.case_id}",
                f"- Risk Level: {case.risk_level}",
                f"- Expected: {', '.join(case.expected_rules) or 'none'}",
                f"- Detected: {', '.join(case.detected_rules) or 'none'}",
                f"- Missed: {', '.join(case.missed_rules) or 'none'}",
                f"- Unexpected: {', '.join(case.unexpected_rules) or 'none'}",
                f"- Latency: {round(case.latency_ms, 2)} ms",
                "",
            ]
        )
    return "\n".join(lines)


def run_evaluation_cli(argv: list[str] | None = None) -> tuple[int, str]:
    parser = argparse.ArgumentParser(prog="ai-pr-review-eval")
    parser.add_argument("--dataset", default="examples/evaluation-set")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)

    result = evaluate_dataset(Path(args.dataset))
    if args.format == "json":
        return 0, json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    return 0, render_evaluation_markdown(result)


def main() -> None:
    exit_code, output = run_evaluation_cli()
    print(output)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
