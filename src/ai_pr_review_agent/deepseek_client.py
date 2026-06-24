from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import replace

from .models import ReviewReport
from .renderers import render_json


DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"


def build_deepseek_payload(
    report: ReviewReport,
    diff_text: str,
    model: str = DEFAULT_DEEPSEEK_MODEL,
) -> dict[str, object]:
    return {
        "model": model,
        "stream": False,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是资深代码审查工程师。请基于规则引擎结果、上下文压缩计划和精选 diff "
                    "输出中英文代码审查补充意见。不要编造 diff 中不存在的文件、函数或业务背景。"
                    "先中文后英文，保持简洁，重点关注风险、修复建议、影响范围和测试建议。"
                ),
            },
            {
                "role": "user",
                "content": build_deepseek_review_context(report, diff_text),
            },
        ],
    }


def build_deepseek_review_context(report: ReviewReport, diff_text: str) -> str:
    selected_diff = select_diff_for_deepseek(report, diff_text)
    plan_lines = [
        f"- {item.file_path} -> {item.strategy} ({item.reason}, score={item.risk_score})"
        for item in report.context_plan.file_strategies
    ]
    return (
        "Rule engine report JSON:\n"
        f"{render_json(report)}\n\n"
        "Context compression plan:\n"
        f"{chr(10).join(plan_lines)}\n\n"
        "Selected git diff for LLM review:\n"
        f"{selected_diff}"
    )


def select_diff_for_deepseek(report: ReviewReport, diff_text: str) -> str:
    selected_files = {
        item.file_path
        for item in report.context_plan.file_strategies
        if item.strategy in {"full", "focused"}
    }
    if not selected_files:
        return diff_text[:12000]
    blocks = split_diff_by_file(diff_text)
    selected = [block for path, block in blocks if path in selected_files]
    return "\n".join(selected)[:12000]


def split_diff_by_file(diff_text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    current_path: str | None = None
    current_lines: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current_path is not None:
                blocks.append((current_path, "\n".join(current_lines)))
            current_path = None
            current_lines = [line]
            continue
        current_lines.append(line)
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_path = path
    if current_path is not None:
        blocks.append((current_path, "\n".join(current_lines)))
    return blocks


def extract_deepseek_content(raw_body: bytes) -> str:
    payload = json.loads(raw_body.decode("utf-8"))
    return payload["choices"][0]["message"]["content"].strip()


def request_deepseek_review(
    report: ReviewReport,
    diff_text: str,
    api_key: str,
    model: str = DEFAULT_DEEPSEEK_MODEL,
    timeout_seconds: int = 30,
) -> str:
    body = json.dumps(
        build_deepseek_payload(report, diff_text, model=model),
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return extract_deepseek_content(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Unable to reach DeepSeek API: {error.reason}") from error


def attach_ai_review(report: ReviewReport, ai_review: str) -> ReviewReport:
    return replace(report, ai_review=ai_review)
