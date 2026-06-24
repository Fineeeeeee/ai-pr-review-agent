# Harness Integration Notes

## Two Meanings Of Harness

This project uses the word Harness in two related but different ways:

1. **Agent Harness**: the engineering layer around a model or agent workflow. In this project it means multi-agent routing, memory layers, sandbox policy, resilience policy, and observability metadata.
2. **Harness CI/CD platform**: the software delivery platform from Harness.io. This project does not create CI/CD configuration by default, but it can be called from CI as a CLI tool.

## Implemented Agent Harness

Run:

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format harness
```

The manifest includes:

- `agents`: diff parser, rule reviewer, impact analyzer, context router, optional LLM reviewer.
- `memory_layers`: working memory, review memory, future pattern memory.
- `sandbox`: read-only default operations and blocked actions.
- `resilience`: local rule engine fallback and DeepSeek failure behavior.
- `observability`: trace id, lifecycle events, and basic metrics.

## Harness CI/CD Platform Integration Sketch

This repository intentionally does not create `.github/workflows`, Harness pipeline YAML, or other CI/CD config without explicit approval.

A typical Harness CI step could call:

```bash
python -m ai_pr_review_agent.cli --diff-file pr.diff --format sarif > ai-pr-review.sarif
python -m ai_pr_review_agent.cli --diff-file pr.diff --format json > ai-pr-review.json
```

Recommended secret handling:

- Store `DEEPSEEK_API_KEY` in the CI secret manager.
- Do not print the key in logs.
- Keep DeepSeek optional; local rules should still produce reports when the key is missing.

## Why This Matters In Interviews

The project is not only an LLM call. It shows the harness around AI:

- Tool routing: deterministic rules first, optional LLM second.
- Memory: review feedback is persisted as JSONL events.
- Sandbox: default behavior is read-only and blocks CI/CD mutation.
- Resilience: local reports still work without DeepSeek.
- Observability: each review has trace-like metadata and metrics.

## References

- Harness describes itself as an AI software delivery platform across CI/CD, testing, security, and cost workflows: https://www.harness.io/
- Martin Fowler's article frames coding-agent harness engineering as the system around the model: https://martinfowler.com/articles/harness-engineering.html
