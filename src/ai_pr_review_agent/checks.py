from __future__ import annotations

import ast
import re

from .models import AddedLine, Finding, ParsedDiff


SECRET_PATTERN = re.compile(
    r"\b(api[_-]?key|apiKey|secret|token|authToken|password|passwd)\b\s*[:=]\s*['\"][^'\"]{6,}['\"]|sk-[A-Za-z0-9_-]{8,}",
    re.IGNORECASE,
)
SQL_INTERPOLATION_PATTERN = re.compile(
    r"\bexecute\s*\(\s*f['\"]|\.format\s*\(|%\s*\(",
    re.IGNORECASE,
)
SQL_KEYWORD_PATTERN = re.compile(r"\b(select|insert|update|delete)\b", re.IGNORECASE)
ASSIGNMENT_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)")
EXECUTE_VARIABLE_PATTERN = re.compile(r"\bexecute\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\b")
INTERPOLATED_STRING_PATTERN = re.compile(r"f['\"]|\.format\s*\(|%\s*[A-Za-z_(]", re.IGNORECASE)
JS_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.+)"
)
JS_EXECUTE_VARIABLE_PATTERN = re.compile(
    r"\b(?:query|execute)\s*\(\s*([A-Za-z_$][A-Za-z0-9_$]*)\b"
)
JS_TEMPLATE_INTERPOLATION_PATTERN = re.compile(r"`[^`]*\$\{[^`]+`", re.IGNORECASE)
JS_STRING_CONCAT_PATTERN = re.compile(
    r"['\"][^'\"]*\b(select|insert|update|delete)\b[^'\"]*['\"]\s*\+|\+\s*['\"][^'\"]*\b(select|insert|update|delete)\b",
    re.IGNORECASE,
)
UNSAFE_EVAL_PATTERN = re.compile(r"\b(eval|exec)\s*\(")
SHELL_TRUE_PATTERN = re.compile(r"\bshell\s*=\s*True\b|os\.system\s*\(")
JS_SHELL_EXECUTION_PATTERN = re.compile(r"\b(?:child_process\.)?(?:exec|execSync)\s*\(")
BROAD_EXCEPTION_PATTERN = re.compile(r"\bexcept\s+(Exception|BaseException)\s*:")


def run_static_checks(parsed: ParsedDiff) -> list[Finding]:
    findings: list[Finding] = []
    for file_change in parsed.files:
        interpolated_sql_variables: dict[str, AddedLine] = {}
        for line in file_change.added_lines:
            findings.extend(check_line(line))
            assigned_variable = find_interpolated_sql_assignment(line)
            if assigned_variable:
                interpolated_sql_variables[assigned_variable] = line
            executed_variable = find_executed_variable(line)
            if executed_variable in interpolated_sql_variables:
                findings.append(make_sql_interpolation_finding(line))

    if should_flag_missing_tests(parsed):
        first_application_file = next(file for file in parsed.files if not file.is_test)
        findings.append(
            Finding(
                rule_id="missing_tests",
                title="Application change has no test update",
                title_zh="应用代码变更缺少测试更新",
                severity="medium",
                file_path=first_application_file.path,
                line_number=0,
                message="Production code changed without a matching test file in the diff.",
                message_zh="本次 diff 修改了生产代码，但没有看到对应的测试文件变更。",
                recommendation="Add or update focused tests for the changed behavior before merging.",
                recommendation_zh="合并前为变更行为补充聚焦测试，或更新已有测试覆盖该场景。",
            )
        )

    return findings


def check_line(line: AddedLine) -> list[Finding]:
    content = line.content.strip()
    findings: list[Finding] = []

    if SECRET_PATTERN.search(content):
        findings.append(
            Finding(
                rule_id="secret_literal",
                title="Possible secret committed in code",
                title_zh="疑似密钥被提交到代码中",
                severity="high",
                file_path=line.file_path,
                line_number=line.new_line_number,
                message="The added line looks like a hard-coded key, token, password, or secret.",
                message_zh="新增代码看起来包含硬编码的 key、token、password 或 secret。",
                recommendation="Move the value to an environment variable or secret manager and rotate it if it is real.",
                recommendation_zh="将敏感值迁移到环境变量或密钥管理服务；如果是真实密钥，需要立即轮换。",
            )
        )

    if has_sql_interpolation_execute(line):
        findings.append(make_sql_interpolation_finding(line))

    if has_unsafe_dynamic_execution(line):
        findings.append(
            Finding(
                rule_id="unsafe_eval",
                title="Unsafe dynamic code execution",
                title_zh="不安全的动态代码执行",
                severity="critical",
                file_path=line.file_path,
                line_number=line.new_line_number,
                message="The added line executes dynamic code with eval or exec.",
                message_zh="新增代码使用 eval 或 exec 执行动态代码，风险极高。",
                recommendation="Replace dynamic execution with an explicit parser, allowlist, or command dispatch table.",
                recommendation_zh="用显式解析器、白名单或命令分发表替代动态执行。",
            )
        )

    if SHELL_TRUE_PATTERN.search(content) or (
        is_javascript_like_path(line.file_path) and JS_SHELL_EXECUTION_PATTERN.search(content)
    ):
        findings.append(
            Finding(
                rule_id="shell_execution",
                title="Shell execution risk",
                title_zh="Shell 命令执行风险",
                severity="high",
                file_path=line.file_path,
                line_number=line.new_line_number,
                message="The added line invokes a shell command or enables shell=True.",
                message_zh="新增代码调用 Shell 命令或启用了 shell=True，可能放大命令注入风险。",
                recommendation="Use argument lists with subprocess and validate all user-controlled inputs.",
                recommendation_zh="使用 subprocess 参数列表形式，并校验所有用户可控输入。",
            )
        )

    if BROAD_EXCEPTION_PATTERN.search(content):
        findings.append(
            Finding(
                rule_id="broad_exception",
                title="Broad exception handler",
                title_zh="异常捕获范围过宽",
                severity="low",
                file_path=line.file_path,
                line_number=line.new_line_number,
                message="The code catches a broad exception type.",
                message_zh="代码捕获了过宽的异常类型，可能掩盖真实错误。",
                recommendation="Catch the narrow exception type and preserve the original error context.",
                recommendation_zh="改为捕获更具体的异常类型，并保留原始错误上下文。",
            )
        )

    return findings


def find_interpolated_sql_assignment(line: AddedLine) -> str | None:
    if is_javascript_like_path(line.file_path):
        return find_js_interpolated_sql_assignment(line.content)

    ast_variable = find_interpolated_sql_assignment_ast(line.content)
    if ast_variable:
        return ast_variable

    match = ASSIGNMENT_PATTERN.search(line.content.strip())
    if not match:
        return None
    value = match.group(2)
    if SQL_KEYWORD_PATTERN.search(value) and INTERPOLATED_STRING_PATTERN.search(value):
        return match.group(1)
    return None


def find_executed_variable(line: AddedLine) -> str | None:
    if is_javascript_like_path(line.file_path):
        return find_js_executed_variable(line.content)

    ast_variable = find_executed_variable_ast(line.content)
    if ast_variable:
        return ast_variable

    match = EXECUTE_VARIABLE_PATTERN.search(line.content.strip())
    return match.group(1) if match else None


def has_sql_interpolation_execute(line: AddedLine) -> bool:
    if is_javascript_like_path(line.file_path):
        return has_js_sql_interpolation_execute(line.content)

    if has_sql_interpolation_execute_ast(line.content):
        return True
    content = line.content.strip()
    return bool(SQL_INTERPOLATION_PATTERN.search(content) and "execute" in content)


def is_javascript_like_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return normalized.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"))


def has_unsafe_dynamic_execution(line: AddedLine) -> bool:
    content = line.content.strip()
    if is_javascript_like_path(line.file_path):
        return bool(re.search(r"\beval\s*\(", content))
    return bool(UNSAFE_EVAL_PATTERN.search(content))


def find_js_interpolated_sql_assignment(content: str) -> str | None:
    match = JS_ASSIGNMENT_PATTERN.search(content.strip())
    if not match:
        return None
    value = match.group(2)
    if js_expression_is_interpolated_sql(value):
        return match.group(1)
    return None


def find_js_executed_variable(content: str) -> str | None:
    match = JS_EXECUTE_VARIABLE_PATTERN.search(content.strip())
    return match.group(1) if match else None


def has_js_sql_interpolation_execute(content: str) -> bool:
    stripped = content.strip()
    if not re.search(r"\b(query|execute)\s*\(", stripped):
        return False
    return js_expression_is_interpolated_sql(stripped)


def js_expression_is_interpolated_sql(content: str) -> bool:
    if not SQL_KEYWORD_PATTERN.search(content):
        return False
    return bool(JS_TEMPLATE_INTERPOLATION_PATTERN.search(content) or JS_STRING_CONCAT_PATTERN.search(content))


def find_interpolated_sql_assignment_ast(content: str) -> str | None:
    tree = parse_python_line(content)
    if tree is None:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and expression_is_interpolated_sql(node.value):
            return target.id
    return None


def find_executed_variable_ast(content: str) -> str | None:
    tree = parse_python_line(content)
    if tree is None:
        return None
    for node in ast.walk(tree):
        if is_execute_call(node) and node.args and isinstance(node.args[0], ast.Name):
            return node.args[0].id
    return None


def has_sql_interpolation_execute_ast(content: str) -> bool:
    tree = parse_python_line(content)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if is_execute_call(node) and node.args and expression_is_interpolated_sql(node.args[0]):
            return True
    return False


def parse_python_line(content: str) -> ast.AST | None:
    try:
        return ast.parse(content.strip())
    except SyntaxError:
        return None


def is_execute_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return isinstance(node.func, ast.Attribute) and node.func.attr == "execute"


def expression_is_interpolated_sql(node: ast.AST) -> bool:
    return expression_contains_sql_keyword(node) and expression_uses_interpolation(node)


def expression_contains_sql_keyword(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if SQL_KEYWORD_PATTERN.search(child.value):
                return True
    return False


def expression_uses_interpolation(node: ast.AST) -> bool:
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "format"
    return False


def make_sql_interpolation_finding(line: AddedLine) -> Finding:
    return Finding(
        rule_id="sql_interpolation",
        title="SQL query uses string interpolation",
        title_zh="SQL 查询使用字符串插值",
        severity="high",
        file_path=line.file_path,
        line_number=line.new_line_number,
        message="The query appears to interpolate user-controlled values into SQL.",
        message_zh="查询语句疑似把用户可控值直接拼进 SQL，存在注入风险。",
        recommendation="Use parameterized queries and pass values separately from the SQL string.",
        recommendation_zh="改用参数化查询，将 SQL 模板和值分开传递。",
    )


def should_flag_missing_tests(parsed: ParsedDiff) -> bool:
    has_application_changes = any(
        file.added_lines and not file.is_test and not is_docs_or_config(file.path)
        for file in parsed.files
    )
    return has_application_changes and not parsed.has_tests


def is_docs_or_config(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return normalized.startswith("docs/") or normalized.endswith(
        (".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".css", ".scss")
    )
