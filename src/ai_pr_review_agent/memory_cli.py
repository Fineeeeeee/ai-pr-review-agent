from __future__ import annotations

import argparse
import json
from pathlib import Path

from .review_memory import load_review_events


VALID_STATUSES = {"accepted", "false_positive", "false_negative", "ignored", "pending"}


def run_memory_cli(argv: list[str] | None = None) -> tuple[int, str]:
    parser = argparse.ArgumentParser(
        prog="ai-pr-review-memory",
        description="Mark review memory feedback events.",
    )
    parser.add_argument("--memory-file", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--line", type=int, required=True)
    parser.add_argument("--status", choices=sorted(VALID_STATUSES), required=True)
    args = parser.parse_args(argv)

    memory_path = Path(args.memory_file)
    events = load_review_events(memory_path)
    updated = 0
    for event in events:
        if event.get("file") == args.file and int(event.get("line", -1)) == args.line:
            event["feedback_status"] = args.status
            event["developer_action"] = "reviewed"
            updated += 1

    if updated:
        write_review_events(memory_path, events)
    return 0, f"updated={updated}"


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
