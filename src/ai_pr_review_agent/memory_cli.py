from __future__ import annotations

import argparse
import json
from pathlib import Path

from .review_memory import load_review_events, summarize_review_events


VALID_STATUSES = {"accepted", "false_positive", "false_negative", "ignored", "pending"}


def run_memory_cli(argv: list[str] | None = None) -> tuple[int, str]:
    parser = argparse.ArgumentParser(
        prog="ai-pr-review-memory",
        description="Mark review memory feedback events.",
    )
    parser.add_argument("--memory-file", required=True)
    parser.add_argument("--file")
    parser.add_argument("--line", type=int)
    parser.add_argument("--status", choices=sorted(VALID_STATUSES))
    parser.add_argument("--summary", action="store_true", help="Print aggregated memory statistics.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    memory_path = Path(args.memory_file)
    events = load_review_events(memory_path)
    if args.summary:
        summary = summarize_review_events(events)
        if args.format == "json":
            return 0, json.dumps(summary, ensure_ascii=False, indent=2)
        return 0, render_summary_text(summary)

    if args.file is None or args.line is None or args.status is None:
        return 2, "--file, --line, and --status are required unless --summary is used."

    updated = 0
    for event in events:
        if event.get("file") == args.file and int(event.get("line", -1)) == args.line:
            event["feedback_status"] = args.status
            event["developer_action"] = "reviewed"
            updated += 1

    if updated:
        write_review_events(memory_path, events)
    return 0, f"updated={updated}"


def render_summary_text(summary: dict[str, object]) -> str:
    lines = [f"total_events={summary['total_events']}"]
    for section in ("by_status", "by_rule", "accepted_by_rule", "false_positive_by_rule", "false_negative_by_rule"):
        values = summary.get(section, {})
        if isinstance(values, dict):
            for key, value in values.items():
                lines.append(f"{section}.{key}={value}")
    return "\n".join(lines)


def write_review_events(memory_path: Path, events: list[dict[str, object]]) -> None:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    with memory_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> None:
    exit_code, output = run_memory_cli()
    print(output)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
