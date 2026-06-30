from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .deepseek_client import DEFAULT_DEEPSEEK_MODEL, attach_ai_review, request_deepseek_review
from .renderers import render_json, render_markdown
from .review_memory import append_review_events
from .review_policy import (
    PolicyConfigError,
    apply_policy,
    configured_fail_threshold,
    discover_config_path,
    load_policy_config,
    risk_meets_threshold,
)
from .reviewer import review_diff
from .sarif_renderer import render_sarif
from .harness_renderer import render_harness_manifest


class CliArgumentError(ValueError):
    pass


class ReviewArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def run_cli(argv: list[str] | None = None) -> tuple[int, str]:
    parser = ReviewArgumentParser(
        prog="ai-pr-review",
        description="Review a git diff and generate a PR risk report.",
    )
    parser.add_argument("--diff-file", help="Path to a unified diff file.")
    parser.add_argument("--diff-text", help="Unified diff text.")
    parser.add_argument("--repo", help="Repository path. Runs `git diff` inside it.")
    parser.add_argument("--format", choices=["markdown", "json", "sarif", "harness"], default="markdown")
    parser.add_argument("--staged", action="store_true", help="Use `git diff --staged` with --repo.")
    parser.add_argument("--deepseek", action="store_true", help="Call DeepSeek API for an enhanced bilingual review.")
    parser.add_argument("--model", default=DEFAULT_DEEPSEEK_MODEL, help="DeepSeek model name.")
    parser.add_argument("--save-memory", help="Append review findings to a JSONL memory file.")
    parser.add_argument("--config", help="Path to .ai-pr-review.yml policy config.")
    parser.add_argument(
        "--fail-on-risk",
        choices=["low", "medium", "high", "critical"],
        help="Return a non-zero exit code when the final risk level meets this threshold.",
    )
    parser.add_argument(
        "--enforce-policy",
        action="store_true",
        help="Use fail_on from policy config as a CI risk gate.",
    )
    try:
        args = parser.parse_args(argv)
    except CliArgumentError as error:
        return 2, str(error)

    try:
        diff_text = load_diff_text(args)
    except ValueError as error:
        return 2, str(error)
    except OSError as error:
        return 1, f"Unable to read diff input: {error}"
    except subprocess.CalledProcessError as error:
        return 1, f"Unable to read git diff: {error.stderr.strip() or error}"

    repo_path = Path(args.repo) if args.repo else None
    try:
        config_path = Path(args.config) if args.config else discover_config_path(repo_path)
        policy_config = load_policy_config(config_path)
    except PolicyConfigError as error:
        return 2, str(error)

    report = apply_policy(review_diff(diff_text, repo_path=repo_path, policy_config=policy_config), policy_config)
    if args.deepseek:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            return 2, "DEEPSEEK_API_KEY is required when --deepseek is enabled."
        try:
            ai_review = request_deepseek_review(report, diff_text, api_key=api_key, model=args.model)
        except RuntimeError as error:
            return 1, str(error)
        report = attach_ai_review(report, ai_review)

    if args.save_memory:
        append_review_events(report, Path(args.save_memory))

    if args.format == "json":
        output = render_json(report)
    elif args.format == "sarif":
        output = render_sarif(report)
    elif args.format == "harness":
        output = render_harness_manifest(report)
    else:
        output = render_markdown(report)

    try:
        threshold = configured_fail_threshold(policy_config, args.fail_on_risk, args.enforce_policy)
        if risk_meets_threshold(report.risk_level, threshold):
            return 3, output
    except PolicyConfigError as error:
        return 2, str(error)
    return 0, output


def load_diff_text(args: argparse.Namespace) -> str:
    provided = [bool(args.diff_file), bool(args.diff_text), bool(args.repo)]
    if sum(provided) != 1:
        raise ValueError("Provide --diff-file, --diff-text, or --repo.")

    if args.diff_file:
        return Path(args.diff_file).read_text(encoding="utf-8")
    if args.diff_text:
        return args.diff_text
    return read_git_diff(Path(args.repo), staged=args.staged)


def read_git_diff(repo_path: Path, staged: bool = False) -> str:
    command = ["git", "diff", "--staged" if staged else "--"]
    completed = subprocess.run(
        command,
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def main() -> None:
    exit_code, output = run_cli()
    stream = sys.stderr if exit_code else sys.stdout
    stream.write(output)
    if output and not output.endswith("\n"):
        stream.write("\n")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
