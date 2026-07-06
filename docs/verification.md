# Verification Guide

This document lists the checks used to verify the project before publishing or committing changes.

## Environment

PowerShell:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
```

The default review path uses only the Python standard library. `DEEPSEEK_API_KEY` is required only when `--deepseek` is explicitly enabled.

## Unit Tests

```powershell
python -m unittest discover -s tests
```

Expected result:

```text
OK
```

## Evaluation Set

```powershell
python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json
```

Expected headline metrics:

```text
sample_count = 25
recall_percent = 100.0
precision_percent = 100.0
false_positive_count = 0
```

## CLI Smoke Tests

Markdown output:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff
```

JSON output:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format json
```

SARIF output:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format sarif
```

Policy gate:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy
```

Expected exit code for the policy gate is `3` when the configured threshold is met.

## Web Server Smoke Test

Start the local server:

```powershell
python -m ai_pr_review_agent.server
```

Open:

```text
http://127.0.0.1:8765
```

Expected behavior:

- The home page loads.
- Pasting a unified diff and clicking review returns a risk summary.
- Enabling DeepSeek without `DEEPSEEK_API_KEY` returns a controlled error.

## Docker Verification

Build the image:

```powershell
docker build -t ai-pr-review-agent:local .
```

Run the sample review:

```powershell
docker run --rm ai-pr-review-agent:local --diff-file examples/risky.diff --format json
```

Verify non-root execution:

```powershell
docker run --rm --entrypoint python ai-pr-review-agent:local -c "import os; print(os.getuid())"
```

Expected UID:

```text
1000
```

## Repo Docs

```powershell
python C:\Users\Administrator\.codex\skills\repo-docs-skills\scripts\validate_repo_docs.py repo-docs --repo-root .
```

Expected result:

```text
OK: 0 errors, 0 warning(s)
```

## Publish Dry Run

Before uploading to GitHub, inspect what would be staged:

```powershell
git add -n .
```

Private or local-only files should not appear, including:

- `.env`
- `AGENTS.md`
- `.vscode/`
- `data/`
- `study/`
- `docs/resume-copy.md`
- `docs/project-learning-guide.md`
- `docs/interview-cheatsheet.md`
