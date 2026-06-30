from __future__ import annotations

import fnmatch
from dataclasses import replace
from pathlib import Path

from .agent_harness import build_agent_harness
from .context_compressor import build_context_plan
from .models import Finding, ReviewReport
from .reviewer import RISK_ORDER, calculate_risk_level, build_test_plan, build_test_plan_zh
from .structured_output import build_structured_output


DEFAULT_CONFIG_NAMES = (".ai-pr-review.yml", ".ai-pr-review.yaml")


class PolicyConfigError(ValueError):
    pass


def discover_config_path(start: Path | None = None) -> Path | None:
    root = start or Path.cwd()
    for name in DEFAULT_CONFIG_NAMES:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def load_policy_config(path: Path | None) -> dict[str, object]:
    if path is None:
        return {}
    try:
        return parse_simple_yaml(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise PolicyConfigError(f"Unable to read policy config: {error}") from error


def parse_simple_yaml(text: str) -> dict[str, object]:
    config: dict[str, object] = {}
    current_list_key: str | None = None
    current_list_item: dict[str, object] | None = None
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("    ") and current_list_item is not None:
            if ":" not in line:
                raise PolicyConfigError(f"Invalid config line: {raw_line}")
            key, raw_value = line.split(":", 1)
            current_list_item[key.strip()] = normalize_scalar(raw_value.strip())
            continue
        if line.startswith("  - ") and current_list_key:
            config.setdefault(current_list_key, [])
            value = parse_list_item(line[4:].strip())
            if isinstance(config[current_list_key], list):
                config[current_list_key].append(value)
            current_list_item = value if isinstance(value, dict) else None
            continue
        if ":" not in line:
            raise PolicyConfigError(f"Invalid config line: {raw_line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise PolicyConfigError(f"Invalid config key: {raw_line}")
        if value == "":
            config[key] = []
            current_list_key = key
            current_list_item = None
        else:
            config[key] = normalize_scalar(value)
            current_list_key = None
            current_list_item = None
    return config


def parse_list_item(value: str) -> object:
    if ":" not in value:
        return normalize_scalar(value)
    key, raw_value = value.split(":", 1)
    return {key.strip(): normalize_scalar(raw_value.strip())}


def normalize_scalar(value: str) -> object:
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [normalize_scalar(item.strip()) for item in inner.split(",")]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value.strip("\"'")


def apply_policy(report: ReviewReport, config: dict[str, object]) -> ReviewReport:
    ignored_rules = set(as_string_list(config.get("ignore_rules")))
    ignored_paths = as_string_list(config.get("ignore_paths"))
    if not ignored_rules and not ignored_paths:
        return report

    findings = [
        finding
        for finding in report.findings
        if not should_ignore_finding(finding, ignored_rules, ignored_paths)
    ]
    risk_level = calculate_risk_level([finding.severity for finding in findings])
    summary = replace(report.summary, finding_count=len(findings))
    test_plan = build_test_plan(summary, risk_level)
    test_plan_zh = build_test_plan_zh(summary, risk_level)
    context_plan = build_context_plan(summary, findings)
    structured_output = build_structured_output(
        risk_level=risk_level,
        summary=summary,
        findings=findings,
        test_plan_zh=test_plan_zh,
        impact_analysis=report.impact_analysis,
    )
    updated = replace(
        report,
        risk_level=risk_level,
        summary=summary,
        findings=findings,
        test_plan=test_plan,
        test_plan_zh=test_plan_zh,
        context_plan=context_plan,
        structured_output=structured_output,
    )
    return replace(updated, agent_harness=build_agent_harness(updated))


def should_ignore_finding(finding: Finding, ignored_rules: set[str], ignored_paths: list[str]) -> bool:
    if finding.rule_id in ignored_rules:
        return True
    normalized_path = finding.file_path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized_path, pattern) for pattern in ignored_paths)


def as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise PolicyConfigError("Expected a string or list of strings in policy config.")


def risk_meets_threshold(risk_level: str, threshold: str | None) -> bool:
    if not threshold:
        return False
    if threshold not in RISK_ORDER:
        raise PolicyConfigError(f"Invalid risk threshold: {threshold}")
    return RISK_ORDER[risk_level] >= RISK_ORDER[threshold]


def configured_fail_threshold(
    config: dict[str, object],
    cli_threshold: str | None,
    enforce_policy: bool = False,
) -> str | None:
    if cli_threshold:
        return cli_threshold
    if not enforce_policy:
        return None
    value = config.get("fail_on")
    return str(value) if value else None
