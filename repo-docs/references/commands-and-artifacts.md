# 命令和产物速查

这是查表材料。如果你还不了解审查路径，先读[一次真实审查怎么跑完](../walkthroughs/one-real-run.md)。

## CLI 入口

| 目标 | 命令 |
| --- | --- |
| 审查示例 diff | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff` |
| 输出 JSON | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format json` |
| 输出 SARIF | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format sarif` |
| 输出 Agent Harness Manifest | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format harness` |
| 审查当前仓库 diff | `python -m ai_pr_review_agent.cli --repo .` |
| 审查 staged diff | `python -m ai_pr_review_agent.cli --repo . --staged` |
| 使用策略配置 | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml` |
| 启用配置门禁 | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy` |

## 本地复现命令

| 检查 | 命令 | 期望 |
| --- | --- | --- |
| 单元测试 | `$env:PYTHONPATH='src'; python -m unittest discover -s tests` | 测试全部通过 |
| 评测 JSON | `$env:PYTHONPATH='src'; python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json` | `missed_positive_count=0` 且 `false_positive_count=0` |
| 高风险门禁 | `$env:PYTHONPATH='src'; python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy` | 返回码 `3` |

## GitHub Actions 产物

| 产物 | 来源 | 用途 |
| --- | --- | --- |
| `pr.diff` | `.github/workflows/ai-pr-review.yml` | 本次 PR 的统一 diff |
| `ai-pr-review.md` | CLI Markdown 输出 | Step Summary 和 PR 评论 |
| `ai-pr-review.json` | CLI JSON 输出 | 结构化集成和调试 |
| `ai-pr-review.sarif` | CLI SARIF 输出 | GitHub Code Scanning |
| `ai-pr-review-results` artifact | `actions/upload-artifact` | 下载完整审查产物 |

## 评测和记忆命令

| 目标 | 命令 |
| --- | --- |
| 跑评测集 | `python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set` |
| 保存审查记忆 | `python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --save-memory data/review-memory.jsonl` |
| 标注一条记忆 | `python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --file app.py --line 4 --status false_positive` |
| 输出记忆统计 | `python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --summary --format json` |

## 私有化运行命令

| 目标 | 命令 |
| --- | --- |
| 构建 Docker 镜像 | `docker build -t ai-pr-review-agent .` |
| 容器内审查示例 diff | `docker run --rm ai-pr-review-agent --diff-file examples/risky.diff --format json` |
| 容器内审查挂载 diff | `docker run --rm -v ${PWD}:/workspace ai-pr-review-agent --diff-file /workspace/pr.diff --config /workspace/.ai-pr-review.yml --enforce-policy` |
