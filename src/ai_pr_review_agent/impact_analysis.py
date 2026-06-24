from __future__ import annotations

import ast
import re
from pathlib import Path

from .models import ImpactAnalysis, ImpactCall


FUNCTION_DEF_PATTERN = re.compile(r"^\+\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
HUNK_CONTEXT_FUNCTION_PATTERN = re.compile(
    r"^@@ .* @@\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)


def analyze_impact(diff_text: str, repo_path: Path | None = None) -> ImpactAnalysis:
    changed_symbols = extract_changed_functions(diff_text)
    if not changed_symbols or repo_path is None:
        return ImpactAnalysis(
            changed_symbols=changed_symbols,
            direct_callers=[],
            impact_level="none" if not changed_symbols else "unknown",
            attention_files=[],
        )

    callers = find_direct_callers(repo_path, changed_symbols)
    attention_files = sorted({caller.file_path for caller in callers})
    return ImpactAnalysis(
        changed_symbols=changed_symbols,
        direct_callers=callers,
        impact_level=calculate_impact_level(len(callers)),
        attention_files=attention_files,
    )


def extract_changed_functions(diff_text: str) -> list[str]:
    symbols: list[str] = []
    for line in diff_text.splitlines():
        for pattern in (FUNCTION_DEF_PATTERN, HUNK_CONTEXT_FUNCTION_PATTERN):
            match = pattern.match(line)
            if match and match.group(1) not in symbols:
                symbols.append(match.group(1))
    return symbols


def find_direct_callers(repo_path: Path, symbols: list[str]) -> list[ImpactCall]:
    callers: list[ImpactCall] = []
    for file_path in repo_path.rglob("*.py"):
        if any(part.startswith(".") for part in file_path.relative_to(repo_path).parts):
            continue
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        visitor = CallVisitor(symbols, file_path.relative_to(repo_path).as_posix())
        visitor.visit(tree)
        callers.extend(visitor.calls)
    return callers


class CallVisitor(ast.NodeVisitor):
    def __init__(self, symbols: list[str], file_path: str) -> None:
        self.symbols = set(symbols)
        self.file_path = file_path
        self.calls: list[ImpactCall] = []

    def visit_Call(self, node: ast.Call) -> None:
        call_name, call_style = call_identity(node.func)
        if call_name in self.symbols:
            self.calls.append(
                ImpactCall(
                    symbol=call_name,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    call_style=call_style,
                )
            )
        self.generic_visit(node)


def call_identity(node: ast.AST) -> tuple[str | None, str]:
    if isinstance(node, ast.Name):
        return node.id, "direct"
    if isinstance(node, ast.Attribute):
        return node.attr, "attribute"
    return None, "unknown"


def calculate_impact_level(caller_count: int) -> str:
    if caller_count == 0:
        return "none"
    if caller_count <= 2:
        return "medium"
    return "high"
