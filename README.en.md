# AI PR Review Agent

[中文 README](README.md)

AI PR Review Agent is a local-first PR risk gate for engineering teams. It accepts a `git diff` or patch file, analyzes only newly added lines, detects common security and review risks, and emits Markdown, JSON, SARIF, and PR-comment-ready structured output.

The default path uses only the Python standard library. It does not require an API key and does not send source code to an external model. DeepSeek is an optional enhancement layer and is used only when `--deepseek` is explicitly enabled with `DEEPSEEK_API_KEY`.

## Core Capabilities

- Local-first review: runs offline by default for local checks, CI, and private environments.
- Incremental risk detection: analyzes added lines in a PR diff instead of rescanning the whole repository.
- Multi-language rules: covers Python, JavaScript, and TypeScript risk patterns.
- Team rule library: supports `custom_rules` in `.ai-pr-review.yml` with `literal` and `forbidden_call` rule types.
- GitHub Actions integration: generates Markdown, JSON, SARIF, updates PR comments, and enforces risk gates.
- Review Memory: stores findings as JSONL events and supports `accepted`, `false_positive`, and `false_negative` feedback.
- Private Docker runtime: provides a non-root CLI image for self-hosted runners and offline review.
- Measurable evaluation: includes 25 simulated PR diff samples for recall, precision, false positive count, and latency checks.

## Tech Stack

- Python 3.10+
- Python Standard Library
- Git unified diff parsing
- AST-based Python checks
- Lightweight JavaScript / TypeScript rules
- JSON / SARIF / JSONL
- GitHub Actions
- Docker
- unittest

## Quick Start

PowerShell:

```powershell
cd ai-pr-review-agent
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
```

Run the sample review:

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

Review the current repository diff:

```powershell
python -m ai_pr_review_agent.cli --repo .
```

Review staged changes:

```powershell
python -m ai_pr_review_agent.cli --repo . --staged
```

## Policy Configuration

Default policy file:

```text
.ai-pr-review.yml
```

Example:

```yaml
fail_on: high

ignore_rules: []

ignore_paths:
  - "docs/**"
  - "*.md"

custom_rules:
  - id: team_no_pickle_loads
    type: forbidden_call
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization in PR changes."
```

Configuration fields:

- `fail_on`: minimum risk level that fails the policy gate when enforcement is enabled.
- `ignore_rules`: rule IDs removed from final reports and risk scoring.
- `ignore_paths`: path globs removed from final reports and risk scoring.
- `custom_rules`: team-owned rules executed before built-in checks.

Supported custom rule types:

| Type | Purpose |
| --- | --- |
| `literal` | Literal match against added lines. Useful for internal SDK names or fixed banned snippets. |
| `forbidden_call` | Detects real function calls. Python uses AST; JS/TS uses call-shape matching. |

Normal report generation applies `ignore_rules` and `ignore_paths`, but does not fail on `fail_on` automatically. A non-zero exit code is returned only when `--enforce-policy` or `--fail-on-risk` is explicitly provided.

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy
```

## GitHub Actions

Workflow file:

```text
.github/workflows/ai-pr-review.yml
```

On pull requests, the workflow:

1. Runs unit tests.
2. Generates the PR diff.
3. Generates Markdown, JSON, and SARIF review outputs.
4. Writes the review to GitHub Step Summary.
5. Creates or updates a stable PR comment.
6. Uploads review artifacts.
7. Uploads SARIF to GitHub Code Scanning.
8. Enforces the configured `fail_on` risk gate.

The workflow does not call DeepSeek by default and does not require an API key.

## Docker Private Runtime

Build the image:

```powershell
docker build -t ai-pr-review-agent:local .
```

Run the sample review:

```powershell
docker run --rm ai-pr-review-agent:local --diff-file examples/risky.diff --format json
```

Mount a private diff and policy file:

```powershell
docker run --rm -v ${PWD}:/workspace ai-pr-review-agent:local --diff-file /workspace/pr.diff --config /workspace/.ai-pr-review.yml --enforce-policy
```

The image runs as a non-root user. `.dockerignore` excludes `.env`, local review memory, study notes, resume drafts, and generated artifacts. See [docs/private-deployment.md](docs/private-deployment.md) for details.

## Review Memory

Save findings:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --save-memory data/review-memory.jsonl
```

Mark a finding:

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --file app.py --line 4 --status false_positive
```

Print feedback summary:

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --summary --format json
```

Supported statuses:

- `pending`
- `accepted`
- `false_positive`
- `false_negative`
- `ignored`

The `rule_health` section summarizes reviewed count, false positive rate, false negative count, and recommended action by rule. It is advisory only; it does not automatically disable or downgrade rules.

## Web UI

Start the local server:

```powershell
python -m ai_pr_review_agent.server
```

Open:

```text
http://127.0.0.1:8765
```

The Web UI supports pasted diffs, sample loading, risk summary, Markdown report view, and structured JSON view.

## Verification

Unit tests:

```powershell
python -m unittest discover -s tests
```

Evaluation set:

```powershell
python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json
```

Current reproducible metrics:

- Samples: 25
- Recall: 100.0%
- Precision: 100.0%
- False positives: 0
- Average latency: under 1 ms

Full verification commands are in [docs/verification.md](docs/verification.md).

## Architecture

```text
git diff / patch
        |
        v
diff_parser.py        -> parse changed files and added lines
        |
        v
checks.py             -> deterministic built-in and team rules
        |
        v
reviewer.py           -> risk level, test plan, review report
        |
        +--> context_compressor.py -> context routing
        +--> impact_analysis.py    -> changed symbols and callers
        +--> structured_output.py  -> CI-ready JSON schema
        +--> review_memory.py      -> JSONL feedback events
        +--> agent_harness.py      -> agent workflow profile
        |
        v
renderers.py          -> Markdown / JSON
sarif_renderer.py     -> SARIF
harness_renderer.py   -> Agent Harness Manifest
```

## Documentation

- [docs/private-deployment.md](docs/private-deployment.md): private deployment notes
- [docs/verification.md](docs/verification.md): verification checklist
- [docs/evaluation-report.md](docs/evaluation-report.md): evaluation report
- [repo-docs/README.md](repo-docs/README.md): Chinese repository guide

## Scope

This project is designed for PR risk pre-checks and CI risk gates. It is not a full SAST platform and does not include a database, admin console, or multi-tenant permission system. Complex semantic rules should be implemented in the built-in rule engine and covered by the evaluation set instead of turning `.ai-pr-review.yml` into a large rule language.
