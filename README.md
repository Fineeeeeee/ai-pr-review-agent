# AI PR Review Agent

[English README](README.en.md)

AI PR Review Agent 是一个面向企业团队的本地优先 PR 风险门禁工具。它接收 `git diff` 或 patch 文件，只审查本次变更中的新增代码行，识别密钥泄露、SQL 拼接、动态执行、Shell 执行、缺少测试等风险，并输出 Markdown、JSON、SARIF 和 PR 评论所需的结构化结果。

项目默认路径只依赖 Python 标准库，不需要 API Key，不会把代码发送到外部模型。DeepSeek 只作为可选增强层，必须显式传入 `--deepseek` 并配置 `DEEPSEEK_API_KEY` 才会调用。

## 核心能力

- 本地优先审查：默认离线运行，适合本地预检、CI 和企业内网环境。
- 增量风险检测：只分析 PR diff 中的新增行，减少对旧代码的重复噪声。
- 多语言规则：支持 Python、JavaScript、TypeScript 的常见安全风险检测。
- 团队规则库：通过 `.ai-pr-review.yml` 配置 `custom_rules`，支持 `literal` 和 `forbidden_call` 两类规则。
- GitHub Actions 集成：生成 Markdown、JSON、SARIF，更新 PR 评论，并按风险阈值执行门禁。
- Review Memory：将审查发现保存为 JSONL，支持标注 `accepted`、`false_positive`、`false_negative` 并生成规则健康度统计。
- Docker 私有化运行：提供非 root CLI 镜像，适配自托管 Runner 和离线审查场景。
- 可量化评估：内置 25 个模拟 PR diff 样本，用于统计召回率、精确率、误报数和耗时。

## 技术栈

- Python 3.10+
- Python Standard Library
- Git unified diff parsing
- AST-based Python checks
- Lightweight JavaScript / TypeScript rules
- JSON / SARIF / JSONL
- GitHub Actions
- Docker
- unittest

## 快速开始

```powershell
cd ai-pr-review-agent
$env:PYTHONPATH='src'
$env:PYTHONIOENCODING='utf-8'
```

运行示例审查：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff
```

输出 JSON：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format json
```

输出 SARIF：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --format sarif
```

审查当前仓库 diff：

```powershell
python -m ai_pr_review_agent.cli --repo .
```

审查 staged diff：

```powershell
python -m ai_pr_review_agent.cli --repo . --staged
```

## 策略配置

默认配置文件：

```text
.ai-pr-review.yml
```

示例：

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

字段说明：

- `fail_on`：启用策略门禁时触发失败的最低风险等级，可选 `low`、`medium`、`high`、`critical`。
- `ignore_rules`：从最终报告和风险评分中移除的规则 ID。
- `ignore_paths`：从最终报告和风险评分中移除的路径 glob。
- `custom_rules`：团队自定义规则列表，在内置规则之前执行。

`custom_rules` 当前支持两类：

| 类型 | 用途 |
| --- | --- |
| `literal` | 对新增行做字面匹配，适合内部 SDK 名称、固定危险片段 |
| `forbidden_call` | 识别真实函数调用，适合团队禁用 API；Python 使用 AST，JS/TS 使用调用形态匹配 |

普通报告命令会应用 `ignore_rules` 和 `ignore_paths`，但不会因为 `fail_on` 自动失败。只有显式传入 `--enforce-policy` 或 `--fail-on-risk` 时，CLI 才会返回非零退出码。

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --config .ai-pr-review.yml --enforce-policy
```

## GitHub Actions

工作流文件：

```text
.github/workflows/ai-pr-review.yml
```

Pull Request 触发后会执行：

1. 运行单元测试。
2. 生成 PR diff。
3. 生成 Markdown、JSON、SARIF 审查结果。
4. 写入 GitHub Step Summary。
5. 创建或更新固定 PR 评论。
6. 上传审查 artifact。
7. 上传 SARIF 到 GitHub Code Scanning。
8. 根据 `.ai-pr-review.yml` 的 `fail_on` 阈值执行风险门禁。

工作流默认不调用 DeepSeek，也不需要 API Key。

## Docker 私有化运行

构建镜像：

```powershell
docker build -t ai-pr-review-agent:local .
```

运行示例审查：

```powershell
docker run --rm ai-pr-review-agent:local --diff-file examples/risky.diff --format json
```

挂载私有 diff 和策略配置：

```powershell
docker run --rm -v ${PWD}:/workspace ai-pr-review-agent:local --diff-file /workspace/pr.diff --config /workspace/.ai-pr-review.yml --enforce-policy
```

镜像使用非 root 用户运行，`.dockerignore` 会排除 `.env`、本地记忆数据、学习资料、简历资料和生成产物。详细说明见 [docs/private-deployment.md](docs/private-deployment.md)。

## Review Memory

保存审查发现：

```powershell
python -m ai_pr_review_agent.cli --diff-file examples/risky.diff --save-memory data/review-memory.jsonl
```

标注一条发现：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --file app.py --line 4 --status false_positive
```

输出反馈统计：

```powershell
python -m ai_pr_review_agent.memory_cli --memory-file data/review-memory.jsonl --summary --format json
```

支持状态：

- `pending`
- `accepted`
- `false_positive`
- `false_negative`
- `ignored`

摘要中的 `rule_health` 会按规则统计已复核数量、误报率、漏报数量和建议动作。当前版本只做提示，不自动关闭或降权规则，避免少量反馈导致门禁策略漂移。

## Web UI

启动本地服务：

```powershell
python -m ai_pr_review_agent.server
```

打开：

```text
http://127.0.0.1:8765
```

Web UI 支持粘贴 diff、加载示例、查看风险等级、Markdown 报告和结构化 JSON。

## 验证

单元测试：

```powershell
python -m unittest discover -s tests
```

评估集：

```powershell
python -m ai_pr_review_agent.evaluation --dataset examples/evaluation-set --format json
```

当前可复现指标：

- 样本数：25
- 召回率：100.0%
- 精确率：100.0%
- 误报数：0
- 平均分析耗时：低于 1 ms

完整验证命令见 [docs/verification.md](docs/verification.md)。

## 架构概览

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

## 文档

- [docs/private-deployment.md](docs/private-deployment.md)：企业私有化部署说明
- [docs/verification.md](docs/verification.md)：验证命令清单
- [docs/evaluation-report.md](docs/evaluation-report.md)：评估结果
- [repo-docs/README.md](repo-docs/README.md)：中文项目理解 guide

## 适用边界

本项目适合做企业团队的 PR 风险预检和 CI 门禁，不是完整 SAST 平台，也不包含数据库、后台管理系统或多租户权限模型。复杂语义规则应沉淀到内置规则和评估集，不建议把 `.ai-pr-review.yml` 扩展成大型规则语言。
