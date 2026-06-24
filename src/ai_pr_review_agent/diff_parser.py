from __future__ import annotations

import re

from .models import AddedLine, FileChange, ParsedDiff


HUNK_HEADER = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_unified_diff(diff_text: str) -> ParsedDiff:
    files: list[FileChange] = []
    current_path: str | None = None
    current_added: list[AddedLine] = []
    current_new_line: int | None = None

    def finish_current_file() -> None:
        nonlocal current_path, current_added
        if current_path is None:
            return
        files.append(
            FileChange(
                path=current_path,
                added_lines=list(current_added),
                is_test=is_test_path(current_path),
            )
        )
        current_path = None
        current_added = []

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            finish_current_file()
            current_new_line = None
            continue

        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path == "/dev/null":
                continue
            current_path = normalize_diff_path(path)
            current_added = []
            current_new_line = None
            continue

        hunk_match = HUNK_HEADER.match(raw_line)
        if hunk_match:
            current_new_line = int(hunk_match.group(1))
            continue

        if current_path is None or current_new_line is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            content = raw_line[1:]
            current_added.append(AddedLine(current_path, current_new_line, content))
            current_new_line += 1
        elif raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        else:
            current_new_line += 1

    finish_current_file()
    return ParsedDiff(files=files, has_tests=any(file.is_test for file in files))


def normalize_diff_path(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    return (
        normalized.startswith("tests/")
        or "/tests/" in normalized
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.js")
        or name.endswith(".spec.js")
        or name.endswith(".test.ts")
        or name.endswith(".spec.ts")
    )
