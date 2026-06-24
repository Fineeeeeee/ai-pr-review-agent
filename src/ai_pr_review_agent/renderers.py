from __future__ import annotations

import json

from .models import ReviewReport


def render_json(report: ReviewReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def render_markdown(report: ReviewReport) -> str:
    lines = [
        "# AI Code Review Report / 智能代码审查报告",
        "",
        f"- Risk Level / 风险等级: **{report.risk_level}**",
        f"- Changed Files / 变更文件数: {len(report.summary.changed_files)}",
        f"- Added Lines / 新增代码行: {report.summary.total_added_lines}",
        f"- Findings / 风险项: {report.summary.finding_count}",
        f"- Test Files Changed / 是否包含测试变更: {'yes / 是' if report.summary.test_files_changed else 'no / 否'}",
        "",
        "## Changed Files / 变更文件",
        "",
    ]
    if report.summary.changed_files:
        lines.extend(f"- `{path}`" for path in report.summary.changed_files)
    else:
        lines.append("- No files detected. / 未检测到文件。")

    lines.extend(["", "## Findings / 风险发现", ""])
    if report.findings:
        for index, finding in enumerate(report.findings, start=1):
            location = f"{finding.file_path}:{finding.line_number}" if finding.line_number else finding.file_path
            lines.extend(
                [
                    f"### {index}. {finding.title} / {finding.title_zh}",
                    "",
                    f"- Severity / 严重级别: **{finding.severity}**",
                    f"- Rule / 规则: `{finding.rule_id}`",
                    f"- Location / 位置: `{location}`",
                    f"- Why it matters / 为什么重要: {finding.message}",
                    f"- 中文说明: {finding.message_zh}",
                    f"- Recommendation / 建议: {finding.recommendation}",
                    f"- 中文建议: {finding.recommendation_zh}",
                    "",
                ]
            )
    else:
        lines.append("No issues found by the local rule engine. / 本地规则引擎未发现风险。")

    lines.extend(["", "## Context Compression Plan / 上下文压缩计划", ""])
    lines.append(f"- Total Files / 文件总数: {report.context_plan.total_files}")
    lines.append(f"- Modules / 涉及模块: {', '.join(report.context_plan.modules) or 'none'}")
    for item in report.context_plan.file_strategies:
        lines.append(f"- `{item.file_path}`: {item.strategy} ({item.reason}, score={item.risk_score})")

    lines.extend(["", "## Impact Analysis / 跨文件影响分析", ""])
    lines.append(f"- Changed Symbols / 变更符号: {', '.join(report.impact_analysis.changed_symbols) or 'none'}")
    lines.append(f"- Impact Level / 影响等级: {report.impact_analysis.impact_level}")
    if report.impact_analysis.direct_callers:
        for caller in report.impact_analysis.direct_callers:
            lines.append(f"- `{caller.file_path}:{caller.line_number}` calls `{caller.symbol}` ({caller.call_style})")
    else:
        lines.append("- No direct callers found in the provided repository context. / 当前上下文未发现直接调用方。")

    lines.extend(["", "## Structured Output / 结构化输出摘要", ""])
    lines.append(f"- Risk Score / 风险分: {report.structured_output.risk_score}")
    lines.append(f"- Auto Approve Eligible / 是否可自动通过: {report.structured_output.auto_approve_eligible}")

    lines.extend(["", "## Agent Harness / Agent 运行框架", ""])
    lines.append("### Multi-Agent Collaboration / 多 Agent 协同")
    for agent in report.agent_harness.agents:
        lines.append(f"- `{agent.name}`: {agent.responsibility}")
    lines.append("")
    lines.append("### Layered Memory / 分层记忆")
    for layer in report.agent_harness.memory_layers:
        lines.append(f"- `{layer.name}`: {layer.purpose} ({layer.retention})")
    lines.append("")
    lines.append("### Sandbox / 沙盒策略")
    lines.append(f"- Mode / 模式: `{report.agent_harness.sandbox.mode}`")
    lines.append(f"- Allowed / 允许: {', '.join(report.agent_harness.sandbox.allowed_operations)}")
    lines.append(f"- Blocked / 阻断: {', '.join(report.agent_harness.sandbox.blocked_operations)}")
    lines.append("")
    lines.append("### Resilience / 容错机制")
    lines.append(f"- Primary / 主路径: {report.agent_harness.resilience.primary_path}")
    lines.append(f"- Fallbacks / 降级: {', '.join(report.agent_harness.resilience.fallbacks)}")
    lines.append("")
    lines.append("### Observability / 可观测性")
    lines.append(f"- Trace ID: `{report.agent_harness.observability.trace_id}`")
    lines.append(f"- Events: {', '.join(report.agent_harness.observability.events)}")

    lines.extend(["", "## Recommended Test Plan / 推荐测试计划", ""])
    for english, chinese in zip(report.test_plan, report.test_plan_zh):
        lines.append(f"- {english}")
        lines.append(f"  中文: {chinese}")
    if report.ai_review:
        lines.extend(["", "## DeepSeek Enhanced Review / DeepSeek 增强审查", "", report.ai_review])
    lines.append("")
    return "\n".join(lines)
